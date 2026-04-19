const { chromium, devices } = require('playwright');
const fs = require('fs');

(async () => {
  const issues = [];
  const logIssue = (type, details) => issues.push({ type, ...details });

  const runBrowser = async (isMobile) => {
    const browser = await chromium.launch();
    const context = await browser.newContext(isMobile ? devices['iPhone 13'] : { viewport: { width: 1440, height: 1100 } });
    const page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') logIssue('console-error', { text: msg.text(), isMobile });
    });
    page.on('pageerror', err => logIssue('page-error', { message: err.message, isMobile }));
    page.on('requestfailed', req => logIssue('request-failed', { url: req.url(), error: req.failure()?.errorText, isMobile }));

    try {
      if (!isMobile) {
        await page.goto('http://localhost:3000');
        await page.screenshot({ path: 'test-results/visual-inspection/final-login-desktop.png' });
        
        await page.getByLabel('Username').fill('admin');
        await page.getByLabel('Password').fill('admin');
        await page.getByRole('button', { name: 'Sign In' }).click();

        await page.waitForSelector('.app-sidebar-shell');
        await page.getByText('BioLink Agent').waitFor();
        await page.screenshot({ path: 'test-results/visual-inspection/final-welcome-desktop.png' });

        const sidebar = page.locator('.app-sidebar-shell').first();

        // Registry
        await sidebar.getByRole('button', { name: 'Patient Registry' }).click();
        await page.waitForSelector('h2.section-title:has-text("Patient Registry")');
        await page.screenshot({ path: 'test-results/visual-inspection/final-registry-desktop.png' });

        // Patient Detail
        // The previous attempt failed because .registry-link was hidden or not interactive.
        // We'll try to find any link inside the registry table/container.
        const firstLink = page.locator('a[href*="/registry/"], .registry-link').first();
        if (await firstLink.isVisible()) {
          await firstLink.click();
          await page.waitForSelector('.patient-tabs-shell');
          await page.screenshot({ path: 'test-results/visual-inspection/final-patient-desktop.png' });
        } else {
          console.warn('Could not find registry link, skipping patient detail screenshot.');
        }

        // Analytics
        await sidebar.getByRole('button', { name: 'Registry Analytics' }).click();
        await page.waitForSelector('h2.section-title:has-text("Registry Analytics")');
        await page.screenshot({ path: 'test-results/visual-inspection/final-analytics-desktop.png' });

        // Chart Builder
        await sidebar.getByRole('button', { name: 'Chart Builder' }).click();
        await Promise.race([
          page.waitForSelector('iframe[title="Superset"]'),
          page.getByText('Superset URL not set').waitFor()
        ]);
        await page.screenshot({ path: 'test-results/visual-inspection/final-charts-desktop.png' });

        // ETL
        await sidebar.getByRole('button', { name: 'ETL Monitor' }).click();
        await page.getByText('Registry pipeline operations without guessing where the flow broke.').waitFor();
        await page.screenshot({ path: 'test-results/visual-inspection/final-etl-desktop.png' });

        // Dictionary
        await sidebar.getByRole('button', { name: 'Data Dictionary' }).click();
        await page.getByText('Real Data Dictionary').waitFor();
        await page.screenshot({ path: 'test-results/visual-inspection/final-dictionary-desktop.png' });

      } else {
        await page.goto('http://localhost:3000');
        await page.screenshot({ path: 'test-results/visual-inspection/final-login-mobile.png' });

        await page.getByLabel('Username').fill('admin');
        await page.getByLabel('Password').fill('admin');
        await page.getByRole('button', { name: 'Sign In' }).click();

        // Fix strict mode violation for 'Welcome'
        await page.locator('h2.section-title:has-text("Welcome")').waitFor();
        await page.screenshot({ path: 'test-results/visual-inspection/final-welcome-mobile.png' });

        await page.getByRole('button', { name: 'Open navigation menu' }).click();
        await page.waitForSelector('.app-mobile-sidebar');
        await page.screenshot({ path: 'test-results/visual-inspection/final-nav-mobile.png' });
      }
    } catch (err) {
      console.error(`Error in ${isMobile ? 'mobile' : 'desktop'} flow:`, err);
      logIssue('fatal-flow-error', { message: err.message, isMobile });
    } finally {
      await browser.close();
    }
  };

  await runBrowser(false);
  await runBrowser(true);

  fs.writeFileSync('test-results/visual-inspection/runtime-issues-final.json', JSON.stringify(issues, null, 2));
  
  const files = fs.readdirSync('test-results/visual-inspection').filter(f => f.startsWith('final-') && f.endsWith('.png'));
  console.log('Created files:', files.join(', '));
  console.log('Issue count:', issues.length);
})();
