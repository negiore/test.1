// Render promo.html frame-by-frame with Playwright (deterministic: window.seek(t)).
// usage:
//   node render.js <width> <height> <outDir> [fps=30] [duration=36] [workers=4]
//   node render.js <width> <height> <outDir> --times 1.0,5.5,9.2   (stills only, for review)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const [W, H, outDir] = [+args[0], +args[1], args[2]];
const timesIdx = args.indexOf('--times');
const stills = timesIdx >= 0 ? args[timesIdx + 1].split(',').map(Number) : null;
const fps = stills ? 30 : +(args[3] || 30);
const dur = stills ? 0 : +(args[4] || 36);
const workers = stills ? 1 : +(args[5] || 4);
const url = 'file://' + path.resolve(__dirname, 'promo.html');
fs.mkdirSync(outDir, { recursive: true });

async function openPage() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.goto(url);
  // Visit the whole timeline once so every lazily-loaded font subset is fetched.
  for (let t = 0; t < 36; t += 0.25) {
    await page.evaluate(t => { window.seek(t); return document.body.offsetHeight; }, t);
  }
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.waitForTimeout(300);
  await page.evaluate(async () => { await document.fonts.ready; });
  const bad = await page.evaluate(() => [...document.fonts].filter(f => f.status === 'error').length);
  if (bad) console.warn(`warning: ${bad} font faces failed to load`);
  return { browser, page };
}

(async () => {
  if (stills) {
    const { browser, page } = await openPage();
    for (const t of stills) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(outDir, `t${t.toFixed(2).padStart(6, '0')}.png`) });
    }
    await browser.close();
    return;
  }
  const total = Math.round(fps * dur);
  const t0 = Date.now();
  let done = 0;
  await Promise.all([...Array(workers).keys()].map(async k => {
    const { browser, page } = await openPage();
    for (let i = k; i < total; i += workers) {
      await page.evaluate(t => window.seek(t), i / fps);
      await page.screenshot({ path: path.join(outDir, `f${String(i).padStart(5, '0')}.png`) });
      if (++done % 120 === 0) console.log(`${done}/${total} frames (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    await browser.close();
  }));
  console.log(`rendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
})().catch(e => { console.error(e); process.exit(1); });
