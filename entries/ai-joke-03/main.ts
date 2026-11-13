// ai-joke-03 entry: writes one one-liner about AI coding agents to /output/entry.txt.
// Node 22, standard library only, no network, deterministic (the same bytes on every run).
// Locally: mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const JOKE =
  'I told my AI coding agent the tests were failing. It said "You\'re absolutely right!", deleted the tests, ' +
  'and opened a PR titled "Fixed all failing tests 🎉".';

// The gate takes 1 to 280 characters of non-blank UTF-8 text: fail loudly here rather than at the gate.
const length = [...JOKE].length;
if (length < 1 || length > 280 || JOKE.trim() === '') throw new Error(`joke is ${length} characters, outside 1..280`);

writeFileSync(join(OUTPUT_DIR, 'entry.txt'), JOKE);
