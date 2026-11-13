"""polymarket-nvidia-ceo-forecast-01 entry: quantile forecasts of each market's Yes price for the next 240 minutes.

Reads every /input/<id>.in (makefun/polymarket-case/v1) and writes /output/<id>.out with, for each market, one row per
minute after the checkpoint holding five non-decreasing quantiles (5%, 25%, 50%, 75%, 95%) of that minute's price.
Standard library only, no network, deterministic.

Model, per market, from its price x at the checkpoint:
  - centre: x, nudged by (a) sum-reversion: the event's Yes prices should add up to about 1, so each price is pulled
    toward x / S (S the sum over the markets) with a strength that grows with the horizon; and (b) give-back: part of
    the market's move over the last few minutes is expected to reverse.
  - spread: a robust per-market volatility (mean absolute 1-minute move over recent windows, blended), growing like
    h ** alpha, with separate multipliers for the inner (25/75%) and outer (5/95%) quantiles.

Locally: MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import json
import math
import os

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]

# Parameters, set by backtesting on the kit's practice history.
P = {
    "w_short": 60,  # minutes for the short volatility window
    "w_long": 2880,  # minutes for the long volatility window
    "mix": 0.75,  # weight of the short window in the blended volatility
    "alpha": 0.15,  # spread grows like h ** alpha
    "inner": 0.5,  # multiplier for the 25/75% half-width (times vol * h**alpha)
    "outer": 2.2,  # multiplier for the 5/95% half-width
    "floor": 0.001,  # smallest half-width at the outer quantiles, in price units
    "sum_k": 0.0,  # strength of sum-reversion at long horizons (0 = off)
    "sum_t": 120.0,  # minutes for sum-reversion to build up
    "gb_n": 120,  # minutes of recent move considered for give-back
    "gb_f": 0.4,  # fraction of a recent rise expected to reverse (0 = off)
    "gb_fd": 0.0,  # fraction of a recent fall expected to reverse (0 = off)
    "gb_t": 30.0,  # minutes for give-back to build up
    "skew": 0.0,  # extra outer width on the side toward 0.5 for low prices (0 = off)
    "lo_i": 1.75,  # multiplier on the 25% half-width (the lower side)
    "lo_o": 0.35,  # multiplier on the 5% half-width (the lower side)
    "emp": 0.25,  # weight of the pooled empirical quantiles (0 = parametric only, 1 = empirical only)
    "emp_l": 1440,  # minutes of each market's history pooled for the empirical quantiles
    "emp_s": 1.2,  # multiplier on the empirical offsets
    "lr_k": 0.0,  # strength of reversion toward the market's long-run median (0 = off)
    "lr_w": 1440,  # minutes of history for that median
    "lr_t": 240.0,  # minutes for the reversion to build up
    "own_w": 0.0,  # weight of the market's own mean absolute h-minute move in its spread (0 = off)
    "own_l": 1440,  # minutes of history for the market's own h-minute moves
    "oq_w": 0.0,  # weight of the market's own empirical h-minute move quantiles in the offsets (0 = off)
    "oq_l": 1440,  # minutes of history for those quantiles
}

ANCHORS = [1, 3, 10, 30, 60, 120, 240]


def pooled_z(case_prices, vols, p):
    """For each anchor horizon, five empirical quantiles of moves/(vol*h**alpha), pooled over every market."""
    table = {}
    for h in ANCHORS:
        zs = []
        for pr, v in zip(case_prices, vols):
            if v <= 0:
                continue
            seg = pr[-(p["emp_l"] + 1):]
            d = v * h ** p["alpha"]
            zs.extend((seg[i + h] - seg[i]) / d for i in range(0, len(seg) - h))
        zs.sort()
        table[h] = [zs[min(len(zs) - 1, int(t * len(zs)))] for t in QUANTILES] if zs else None
    return table


def interp_z(table, h):
    lo = max(a for a in ANCHORS if a <= h)
    hi = min((a for a in ANCHORS if a >= h), default=ANCHORS[-1])
    if table[lo] is None or table[hi] is None:
        return None
    if lo == hi:
        return table[lo]
    w = (math.log(h) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return [a * (1 - w) + b * w for a, b in zip(table[lo], table[hi])]


def clamp6(x):
    return round(min(1.0, max(0.0, x)), 6) + 0.0


def mean_abs_move(prices, w):
    seg = prices[-(w + 1):]
    if len(seg) < 2:
        return 0.0
    return sum(abs(b - a) for a, b in zip(seg, seg[1:])) / (len(seg) - 1)


def market_vol(prices, p):
    return p["mix"] * mean_abs_move(prices, p["w_short"]) + (1 - p["mix"]) * mean_abs_move(prices, p["w_long"])


def own_scales(prices, p):
    """The market's mean absolute h-minute move at each anchor horizon, divided by h ** alpha (vol units)."""
    seg = prices[-(p["own_l"] + 1):]
    out = {}
    for h in ANCHORS:
        n = len(seg) - h
        out[h] = (sum(abs(seg[i + h] - seg[i]) for i in range(n)) / n) / h ** p["alpha"] if n > 0 else None
    return out


def own_quantiles(prices, p):
    """Five empirical quantiles of the market's own h-minute moves at each anchor horizon, in price units."""
    seg = prices[-(p["oq_l"] + 1):]
    out = {}
    for h in ANCHORS:
        moves = sorted(seg[i + h] - seg[i] for i in range(len(seg) - h))
        out[h] = [moves[min(len(moves) - 1, int(t * len(moves)))] for t in QUANTILES] if moves else None
    return out


def forecast_market(prices, horizon, total, p=P, ztab=None):
    """Rows of five quantiles for minutes 1..horizon after the last price; total is the sum of all markets' prices."""
    x = prices[-1]
    vol = market_vol(prices, p)
    own = own_scales(prices, p) if p["own_w"] else None
    oq = own_quantiles(prices, p) if p["oq_w"] else None
    if p["lr_k"]:
        tail = sorted(prices[-p["lr_w"]:])
        lr_gap = tail[len(tail) // 2] - x
    else:
        lr_gap = 0.0
    target_sum = x / total if total > 0 else x
    n = min(p["gb_n"], len(prices) - 1)
    recent = x - prices[-1 - n] if n > 0 else 0.0
    rows = []
    for h in range(1, horizon + 1):
        c = x
        if p["sum_k"]:
            c += p["sum_k"] * (1 - math.exp(-h / p["sum_t"])) * (target_sum - x)
        if lr_gap:
            c += p["lr_k"] * (1 - math.exp(-h / p["lr_t"])) * lr_gap
        frac = p["gb_f"] if recent > 0 else p["gb_fd"]
        if frac:
            c -= frac * (1 - math.exp(-h / p["gb_t"])) * recent
        v = vol
        if own is not None:
            lo = max(a for a in ANCHORS if a <= h)
            hi = min((a for a in ANCHORS if a >= h), default=ANCHORS[-1])
            if own[lo] is not None and own[hi] is not None:
                w = 0.0 if lo == hi else (math.log(h) - math.log(lo)) / (math.log(hi) - math.log(lo))
                v = (1 - p["own_w"]) * vol + p["own_w"] * (own[lo] * (1 - w) + own[hi] * w)
        s = v * h ** p["alpha"]
        wi = p["inner"] * s
        wo = max(p["outer"] * s, p["floor"])
        up = wo * (1 + p["skew"]) if x < 0.5 else wo
        offs = [-max(wo * p["lo_o"], p["floor"]), -wi * p["lo_i"], 0.0, wi, up]
        if p["emp"] and ztab is not None:
            z = interp_z(ztab, h)
            if z is not None:
                offs = [(1 - p["emp"]) * o + p["emp"] * p["emp_s"] * zz * s for o, zz in zip(offs, z)]
                offs[0] = min(offs[0], -p["floor"])
                offs[4] = max(offs[4], p["floor"])
        if oq is not None:
            z = interp_z(oq, h)
            if z is not None:
                offs = [(1 - p["oq_w"]) * o + p["oq_w"] * zz for o, zz in zip(offs, z)]
                offs[0] = min(offs[0], -p["floor"])
                offs[4] = max(offs[4], p["floor"])
        row = [clamp6(c + o) for o in offs]
        for j in range(1, 5):
            row[j] = max(row[j], row[j - 1])
        rows.append(row)
    return rows


def forecast_case(case, p=P):
    horizon = case["horizon_minutes"]
    total = sum(m["prices"][-1] for m in case["markets"] if m["prices"])
    ztab = None
    if p["emp"]:
        prices = [m["prices"] for m in case["markets"]]
        ztab = pooled_z(prices, [market_vol(pr, p) for pr in prices], p)
    return {
        "forecasts": [
            {"id": m["id"], "q": forecast_market(m["prices"], horizon, total, p, ztab)} for m in case["markets"]
        ]
    }


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(f for f in os.listdir(in_dir) if f.endswith(".in")):
        with open(os.path.join(in_dir, name), encoding="utf-8") as fh:
            case = json.load(fh)
        if case["quantiles"] != QUANTILES:
            raise ValueError(f"{name} asks for quantiles {case['quantiles']}")
        out = forecast_case(case)
        with open(os.path.join(out_dir, name[:-3] + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
