const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const htmlPath = process.argv[2];
  const outDir = process.argv[3];
  const i = 3;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const url = 'file://' + htmlPath + '?slide=' + i + '&autohide=1';
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  // 图片页：等页面内 <img> 解码完成，避免截到未加载图
  try {
    await page.waitForFunction(() => {
      const im = document.querySelector('.figure img');
      return im && im.complete && im.naturalWidth > 0;
    }, { timeout: 15000 });
  } catch (e) { console.log('img-wait-timeout, continue'); }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(outDir, `slide_${String(i).padStart(2, '0')}.png`) });
  console.log('shot', i, 'done');
  await browser.close();
})();
