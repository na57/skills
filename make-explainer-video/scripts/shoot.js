const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const htmlPath = process.argv[2];
  const outDir = process.argv[3];
  const N = 33;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

  for (let i = 1; i <= N; i++) {
    const url = 'file://' + htmlPath + '?slide=' + i + '&autohide=1';
    await page.goto(url, { waitUntil: 'load', timeout: 60000 });
    try {
      await page.waitForFunction(() => window.MathJax && MathJax.startup && MathJax.startup.document && MathJax.startup.document.state() === 'ready', { timeout: 15000 });
    } catch (e) { /* MathJax 未就绪也继续（图片页无公式） */ }
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(outDir, `slide_${String(i).padStart(2, '0')}.png`) });
    console.log('shot', i);
  }
  console.log('CONSOLE_ERRORS:', errs.length ? errs.join(' | ').slice(0, 500) : 'none');
  await browser.close();
})();
