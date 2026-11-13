# pm-entry

Quantile forecaster for make.fun's "Forecast Polymarket's next NVIDIA CEO prices minute by minute, 4 hours ahead" bounty.

For each market it centres on the last price (with part of a recent rise expected to give back),
and sets its five quantiles from a robust per-market volatility blended with empirical move quantiles pooled across
every market. Standard library only, no network, deterministic.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```
