const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 }
  });

  try {
    console.log('Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 10000 });
  } catch (error) {
    console.error('Navigation failed:', error.message);
    await browser.close();
    process.exit(1);
  }

  const url = page.url();
  const title = await page.title();
  const bodyText = await page.innerText('body');
  
  const buttons = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(t => t.length > 0);
  });

  const inputs = await page.evaluate(() => {
    const results = [];
    document.querySelectorAll('input').forEach(input => {
      let labelText = '';
      if (input.id) {
        const label = document.querySelector(\`label[for="\${input.id}"]\`);
        if (label) labelText = label.innerText.trim();
      }
      const placeholder = input.getAttribute('placeholder') || '';
      results.push({ labelText, placeholder });
    });
    return results;
  });

  console.log('Final URL:', url);
  console.log('Page Title:', title);
  console.log('Body Text (first 1200 chars):', bodyText.substring(0, 1200));
  console.log('Button Texts:', buttons);
  console.log('Inputs:', inputs);

  await page.screenshot({ path: 'test-results/visual-inspection/live-state.png' });
  console.log('Screenshot saved to test-results/visual-inspection/live-state.png');

  await browser.close();
})();
