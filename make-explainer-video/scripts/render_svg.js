const { chromium } = require('playwright');
(async () => {
  const [,, svgPath, outPng] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1560, height: 940 }, deviceScaleFactor: 2 });
  await page.goto('file://' + svgPath);
  await page.waitForTimeout(500);
  await page.screenshot({ path: outPng, clip: { x: 0, y: 0, width: 1560, height: 940 } });
  await browser.close();
  console.log('saved', outPng);
})();
