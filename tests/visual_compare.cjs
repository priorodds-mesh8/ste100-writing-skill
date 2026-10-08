// Development test only. The installed renderer has no JavaScript dependency.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { pathToFileURL } = require('url');
const { spawnSync } = require('child_process');

async function main() {
  const root = path.resolve(__dirname, '..');
  const assets = path.join(root, 'skills/diagram-first/assets');
  const out = path.resolve(process.argv[2] || path.join(root, 'validation-output'));
  fs.mkdirSync(out, { recursive: true });
  const python = process.env.STE100_TEST_PYTHON || 'python3';
  const run = (args) => {
    const result = spawnSync(python, args, { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(result.stderr || result.stdout || 'Python test failed.');
    return result.stdout;
  };
  const renderScript = path.join(root, 'skills/diagram-first/scripts/render_diagram.py');
  for (const name of ['reference', 'workflow']) {
    run([renderScript, path.join(root, `examples/diagram-${name}.json`), '--output', path.join(out, `${name}.html`)]);
  }
  const fonts = fs.readFileSync(path.join(assets, 'fonts.css'), 'utf8').replace(/url\((fonts\/[^)]+)\)/g, (_, file) =>
    'url(data:font/ttf;base64,' + fs.readFileSync(path.join(assets, file)).toString('base64') + ')');
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const width of [1280, 390, 899, 901]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 1000 }, colorScheme: theme, deviceScaleFactor: 1 });
        await context.route('https://fonts.googleapis.com/**', route => route.fulfill({ contentType: 'text/css', body: fonts }));
        await context.route('https://fonts.gstatic.com/**', route => route.abort());
        const measurements = [];
        for (const [kind, file] of [
          ['reference', path.join(assets, 'ste100-wiring-sheet.reference.html')],
          ['rendered', path.join(out, 'reference.html')]
        ]) {
          const page = await context.newPage();
          await page.goto(pathToFileURL(file).href);
          await page.evaluate(async () => {
            for (const family of ['IBM Plex Sans', 'IBM Plex Mono']) {
              for (const weight of [400, 500, 600]) await document.fonts.load(`${weight} 14px "${family}"`);
            }
            await document.fonts.ready;
          });
          await page.screenshot({ path: path.join(out, `${width}-${theme}-${kind}.png`), fullPage: true });
          measurements.push(await page.evaluate(() => ({
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight,
            fontsLoaded: Array.from(document.fonts).filter(f => f.status === 'loaded').length,
            panels: Array.from(document.querySelectorAll('section')).map(e => {
              const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height };
            })
          })));
        }
        if (measurements.some(x => x.width !== width || x.fontsLoaded !== 6)) throw new Error('The reference has overflow or missing fonts.');
        if (JSON.stringify(measurements[0]) !== JSON.stringify(measurements[1])) throw new Error('Reference geometry differs.');
        await context.close();
        const offline = await browser.newContext({ viewport: { width, height: 1000 }, colorScheme: theme });
        let blockedRequests = 0;
        await offline.route('**/*', route => {
          if (route.request().url().startsWith('file:')) return route.continue();
          blockedRequests += 1; return route.abort();
        });
        const page = await offline.newPage();
        await page.goto(pathToFileURL(path.join(out, 'workflow.html')).href);
        await page.evaluate(() => document.fonts.ready);
        const workflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, loadedFonts: Array.from(document.fonts).filter(f => f.status === 'loaded').length }));
        if (workflow.width !== width || blockedRequests !== 0 || workflow.loadedFonts < 4) throw new Error('The new diagram has overflow or an offline failure.');
        await page.screenshot({ path: path.join(out, `${width}-${theme}-workflow.png`), fullPage: true });
        await offline.close();
        results.push({ width, theme, geometry: measurements[1], workflow, blockedRequests });
      }
    }
    fs.writeFileSync(path.join(out, 'geometry.json'), JSON.stringify({ browser: browser.version(), platform: os.platform(), results }, null, 2) + '\n');
  } finally { await browser.close(); }
  process.stdout.write(run([path.join(root, 'tests/compare_pixels.py'), out]));
}
main().catch(e => { console.error(e.message); process.exit(1); });
