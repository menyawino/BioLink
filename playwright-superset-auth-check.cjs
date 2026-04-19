const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Logging in...');
  await page.goto('http://localhost:3000/login');
  
  const emailInput = await page.locator('input[placeholder*="username"]').first();
  const passwordInput = await page.locator('input[placeholder*="password"]').first();
  const loginButton = await page.locator('button:has-text("Sign in"), button:has-text("Login"), button[type="submit"]').first();
  
  if (await emailInput.count() > 0) {
      await emailInput.fill('admin');
      await passwordInput.fill('admin');
      await loginButton.click();
      console.log('Clicked login button');
  } else {
      console.log('No login inputs found with current selector.');
  }

  await page.waitForTimeout(2000); 

  console.log('Opening Chart Builder...');
  await page.goto('http://localhost:3000/chart-builder');
  
  try {
    const iframeElement = await page.waitForSelector('iframe', { timeout: 15000 });
    const src = await iframeElement.getAttribute('src');
    console.log('iframe src:', src);

    const screenshotPath = path.join(process.cwd(), 'superset-auth-check.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('screenshot path:', screenshotPath);

    await page.waitForTimeout(5000);

    const frame = page.frames().find(f => f.url() && f.url().includes('superset'));
    if (frame) {
        try {
            const bodyText = await frame.innerText('body');
            console.log('iframe body text (first 1200 chars):', bodyText.substring(0, 1200));
        } catch (e) {
            console.log('Could not access iframe body (likely cross-origin):', e.message);
        }
    } else {
        console.log('Superset iframe not found in frames list');
    }

  } catch (error) {
    console.error('Error finding iframe:', error.message);
    const screenshotPath = path.join(process.cwd(), 'superset-auth-error.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('Error screenshot saved to:', screenshotPath);
  }

  await browser.close();
})();
