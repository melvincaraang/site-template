// Fails when the gzipped JS shipped to the browser exceeds the budget.
// Guards against a dependency quietly doubling the SPA payload.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';

const BUDGET_KB = Number(process.env.BUNDLE_BUDGET_KB ?? 250);
const dir = 'build/_app/immutable';

function walk(d) {
	return readdirSync(d).flatMap((n) => {
		const p = join(d, n);
		return statSync(p).isDirectory() ? walk(p) : [p];
	});
}
const files = walk(dir).filter((f) => f.endsWith('.js') || f.endsWith('.css'));
const total = files.reduce((sum, f) => sum + gzipSync(readFileSync(f)).length, 0);
const kb = total / 1024;
console.log(
	`gzipped JS+CSS: ${kb.toFixed(1)} KB across ${files.length} files (budget ${BUDGET_KB} KB)`
);
if (kb > BUDGET_KB) {
	console.error(`Bundle exceeds budget by ${(kb - BUDGET_KB).toFixed(1)} KB`);
	process.exit(1);
}
