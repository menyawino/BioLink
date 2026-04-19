const { chromium, devices } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const dir = 'test-results/visual-inspection';
  const issues = [];
  const files = [];

  const setupCapture = (page) => {
    page.on('console', msg => { if (msg.type() === 'error') issues.push({type: 'console-error', text: msg.text(), url: page.url()}); });
    page.on('pageerror', err => issues.push({type: 'page-error', text: err.message, url: page.url()}));
    page.on('requestfailed', req => issues.push({type: 'request-failed', url: req.url(), error: req.failure() ? req.failure().errorText : 'unknown'}));
  };

  try {
    const desktopCtx = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    const page = await desktopCtx.newPage();
    setupCapture(page);

    console.log('Visiting login page...');
    await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle' });
    await page.screenshot({ path: `${dir}/login-desktop.png` });
    files.push('login-desktop.png');

    console.log('Detecting login fields...');
    const userField = page.locator('input[type="text"], input[name*="user"], input[placeholder*="user"]').first();
    const passField = page.locator('input[type="password"]').first();
    const submitBtn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();

    if (await userField.count() > 0) {
      await userField.fill('admin');
      await passField.fill('admin');
      await submitBtn.click();
      console.log('Login submitted.');
      await page.waitForTimeout(5000);
      await page.screenshot({ path: `${dir}/welcome-desktop.png` });
      files.push('welcome-desktop.png');
    } else {
       console.log('Login fields not found. Page content:', await page.content());
    }

    const navItems = [
      { text: 'Patient Registry', file: 'registry-desktop.png' },
      { text: 'Registry Analytics', file: 'analytics-desktop.png' },
      { text: 'Chart Builder', file: 'charts-desktop.png' },
      { text: 'ETL Monitor', file: 'etl-desktop.png' },
      { text: 'Data Dictionary', file: 'dictionary-desktop.png' }
    ];

    for (const item of navItems) {
      console.log(`Navigating to ${item.text}...`);
      const link = page.getByText(item.text, { exact: false });
      if (await link.count() > 0) {
        await link.first().click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `${dir}/${item.file}` });
        files.push(item.file);
      }
    }

    const dnaLink = page.locator('a[href*="/registry/"]').first();
    if (await dnaLink.count() > 0) {
      await dnaLink.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${dir}/patient-desktop.png` });
      files.push('patient-desktop.png');
    }
  } catch (e) {
    console.error('Desktop flow failed:', e.message);
  }

  try {
    const mobileCtx = await browser.newContext({ ...devices['iPhone 13'] });
    const mobilePage = await mobileCtx.newPage();
    setupCapture(mobilePage);

    console.log('Mobile flow...');
    await mobilePage.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle' });
    await mobilePage.screenshot({ path: `${dir}/login-mobile.png` });
    files.push('login-mobile.png');

    const userField = mobilePage.locator('input').first();
    if (await userField.count() > 0) {
      await mobilePage.fill('input:nth-child(1)', 'admin');
      await mobilePage.fill('input[type="password"]', 'admin');
      await mobilePage.click('button[type="submit"]');
      await mobilePage.waitForTimeout(5000);
    }

    const menuBtn = mobilePage.locator('button[aria-label="menu"], button[aria-label="open drawer"]').first();
    if (await menuBtn.count() > 0) await menuBtn.click();
    
    await mobilePage.screenshot({ path: `${dir}/welcome-mobile.png` });
    files.push('welcome-mobile.png');
  } catch (e) {
    console.error('Mobile flow failed:', e.message);
  }

  fs.writeFileSync(`${dir}/runtime-issues.json`, JSON.stringify(issues, null, 2));
  console.log('\nSummary:');
  console.log('Files created:', files.join(', '));
  console.log('Issues found:', issues.length);
  
  await browser.close();
})();
