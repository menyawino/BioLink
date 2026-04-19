const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const outputDir = 'test-results/visual-inspection';
  const issues = [];
  const createdFiles = [];

  const captureIssue = (type, data) => {
    issues.push({ type, data, timestamp: new Date().toISOString() });
  };

  const runTest = async (viewport, prefix) => {
    const browser = await chromium.launch();
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') captureIssue('console-error', { text: msg.text(), location: msg.location() });
    });
    page.on('pageerror', err => captureIssue('page-error', { message: err.message, stack: err.stack }));
    page.on('requestfailed', req => captureIssue('request-failed', { url: req.url(), error: req.failure()?.errorText || 'Failed' }));

    try {
      // Login Page
      await page.goto('http://localhost:3000/login');
      await page.waitForLoadState('networkidle');
      const loginPath = path.join(outputDir, `login-${prefix}.png`);
      await page.screenshot({ path: loginPath });
      createdFiles.push(loginPath);

      // Login attempt
      try {
        await page.getByLabel('Username').fill('admin');
        await page.getByLabel('Password').fill('admin');
        await page.getByRole('button', { name: 'Sign In' }).click();
        await page.waitForURL('**/welcome', { timeout: 15000 });
        await page.waitForLoadState('networkidle');
      } catch (loginErr) {
        captureIssue('login-failure', { message: loginErr.message });
      }
      
      const welcomePath = path.join(outputDir, `welcome-${prefix}.png`);
      await page.screenshot({ path: welcomePath });
      createdFiles.push(welcomePath);

      if (prefix === 'mobile') {
        const menuBtn = page.getByRole('button', { name: /menu|toggle/i });
        if (await menuBtn.isVisible()) {
          await menuBtn.click();
          await page.waitForTimeout(1000);
          const navPath = path.join(outputDir, 'nav-mobile.png');
          await page.screenshot({ path: navPath });
          createdFiles.push(navPath);
        }
      } else {
        const navs = [
          { name: 'Patient Registry', url: '/registry' },
          { name: 'Registry Analytics', url: '/analytics' },
          { name: 'Chart Builder', url: '/chart-builder' },
          { name: 'ETL Monitor', url: '/etl-monitor' },
          { name: 'Data Dictionary', url: '/dictionary' }
        ];

        for (const nav of navs) {
          try {
            const btn = page.getByRole('button', { name: nav.name, exact: true }).first();
            await btn.click();
            await page.waitForURL(`**${nav.url}`, { timeout: 10000 });
            await page.waitForLoadState('networkidle');
            const p = path.join(outputDir, `${nav.name.toLowerCase().replace(/ /g, '-')}-desktop.png`);
            await page.screenshot({ path: p });
            createdFiles.push(p);
          } catch (navErr) {
            captureIssue('navigation-failure', { name: nav.name, message: navErr.message });
          }
        }
      }
    } catch (e) {
      captureIssue('test-failure', { message: e.message, prefix });
    }

    await browser.close();
  };

  await runTest({ width: 1440, height: 1100 }, 'desktop');
  await runTest({ width: 390, height: 844 }, 'mobile');

  fs.writeFileSync(path.join(outputDir, 'runtime-issues.json'), JSON.stringify(issues, null, 2));
  
  console.log('Inspection Complete');
  console.log('Created Files:', createdFiles.map(f => path.basename(f)).join(', '));
  console.log('Issues Found:', issues.length);
})();
