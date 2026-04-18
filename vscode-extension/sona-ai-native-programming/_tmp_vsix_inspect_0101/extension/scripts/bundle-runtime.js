// Copy the repo's sona package (stdlib + __init__) into extension/runtime/sona
// Run as a prepublish step from extension folder
const fs = require('fs');
const path = require('path');

function copyDir(src, dest, filterFn) {
	if (!fs.existsSync(src)) return;
	if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
	for (const entry of fs.readdirSync(src)) {
		const s = path.join(src, entry);
		const d = path.join(dest, entry);
		const stat = fs.statSync(s);
		if (filterFn && !filterFn(s, stat)) continue;
		if (stat.isDirectory()) {
			copyDir(s, d, filterFn);
		} else {
			fs.mkdirSync(path.dirname(d), { recursive: true });
			fs.copyFileSync(s, d);
		}
	}
}

function main() {
		const repoRoot = path.resolve(__dirname, '..', '..', '..');
	const sourceSona = path.join(repoRoot, 'sona');
	const destRuntime = path.resolve(__dirname, '..', 'runtime');
	const destSona = path.join(destRuntime, 'sona');

	if (!fs.existsSync(sourceSona)) {
		console.error('ERROR: Could not find repo sona/ at', sourceSona);
		process.exit(1);
	}

	// Clean previous copy
	if (fs.existsSync(destSona)) {
		fs.rmSync(destSona, { recursive: true, force: true });
	}

	const filter = (p, stat) => {
		const rel = p.replace(sourceSona + path.sep, '');
		// Exclude pycache/tests and heavy folders not needed in runtime
		if (rel.includes('__pycache__')) return false;
		if (rel.startsWith('ai' + path.sep)) return false;
		if (rel.startsWith('native_') && rel.endsWith('.py')) return true; // keep native wrappers
		return true;
	};

	// Copy entire sona package (including stdlib and __init__.py)
	copyDir(sourceSona, destSona, filter);

	// Quick sanity: ensure MANIFEST.json exists
	const manifest = path.join(destSona, 'stdlib', 'MANIFEST.json');
	if (!fs.existsSync(manifest)) {
		console.error('ERROR: Missing stdlib MANIFEST.json at', manifest);
		process.exit(1);
	}
	console.log('Bundled Sona runtime to', destSona);
}

main();
