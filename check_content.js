const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.goto('https://biolink-preview-web.jollywave-3b662133.eastus.azurecontainerapps.io');
    const content = await page.content();
    console.log('Page Content Length:', content.length);
    console.log('Text Content:', await page.innerText('body'));
  } catch (e) {
    console.error('Error:', e.message);
  } finally {
    await browser.close();
  }
})();
