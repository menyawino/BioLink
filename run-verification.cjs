const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const resultsDir = 'test-results/visual-inspection/focused-fix';
    if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
    }

    const logs = [];
    const logIssue = (msg) => {
        console.log(msg);
        logs.push({ timestamp: new Date().toISOString(), message: msg });
    };

    const browser = await chromium.launch();
    
    // Desktop Verification
    const desktopContext = await browser.newContext({
        viewport: { width: 1440, height: 1100 }
    });
    const page = await desktopContext.newPage();
    
    page.on('console', msg => logIssue(`CONSOLE: ${msg.type()}: ${msg.text()}`));
    page.on('pageerror', err => logIssue(`PAGE ERROR: ${err.message}`));

    try {
        logIssue('Navigating to login page...');
        await page.goto('http://localhost:3000/login');
        await page.fill('input[name="username"], input[id="username"]', 'admin');
        await page.fill('input[name="password"], input[id="password"]', 'admin');
        
        logIssue('Submitting login form...');
        await page.click('button[type="submit"]');
        
        await page.waitForTimeout(5000); // Wait for potential redirects/navigation

        // Chart Builder
        logIssue('Checking Chart Builder...');
        const chartBuilderLink = page.locator('a[href*="/chart-builder"], button:has-text("Chart Builder")');
        if (await chartBuilderLink.count() > 0) {
            await chartBuilderLink.first().click();
        } else {
            logIssue('Sidebar link not found. Attempting direct navigation...');
            await page.goto('http://localhost:3000/chart-builder');
        }
        
        const state = await Promise.race([
            page.waitForSelector('iframe[title="Superset"]', { timeout: 15000 }).then(() => 'iframe'),
            page.waitForSelector('text=Superset URL not set', { timeout: 15000 }).then(() => 'not-set'),
            page.waitForSelector('text=Superset connection configured', { timeout: 15000 }).then(() => 'configured-ui')
        ]);
        
        logIssue(`Observed Chart Builder state: ${state}`);
        await page.screenshot({ path: path.join(resultsDir, 'chart-builder-after-fix.png'), fullPage: true });

        // Patient Registry
        logIssue('Checking Patient Registry...');
        await page.goto('http://localhost:3000/patients');

        // Wait for loading to disappear
        await page.waitForLoadState('networkidle');
        
        await Promise.race([
            page.waitForSelector('table tr, .patient-card', { timeout: 15000 }),
            page.waitForSelector(':text-is("No patients found")', { timeout: 15000 }),
            page.waitForTimeout(5000)
        ]);
        
        await page.screenshot({ path: path.join(resultsDir, 'registry-after-fix.png'), fullPage: true });

    } catch (err) {
        logIssue(`ERROR during desktop flow: ${err.message}`);
    }

    // Mobile Verification
    const mobileContext = await browser.newContext({
        ...devices['iPhone 13'],
        viewport: { width: 390, height: 844 }
    });
    const mobilePage = await mobileContext.newPage();
    
    try {
        logIssue('Checking mobile view login...');
        await mobilePage.goto('http://localhost:3000/login');
        await mobilePage.fill('input[name="username"], input[id="username"]', 'admin');
        await mobilePage.fill('input[name="password"], input[id="password"]', 'admin');
        
        await mobilePage.click('button[type="submit"]');
        await mobilePage.waitForTimeout(5000);
        
        await mobilePage.screenshot({ path: path.join(resultsDir, 'mobile-home-after-fix.png') });
    } catch (err) {
        logIssue(`ERROR during mobile flow: ${err.message}`);
    }

    fs.writeFileSync(path.join(resultsDir, 'runtime-issues.json'), JSON.stringify(logs, null, 2));
    await browser.close();
    logIssue('Verification script finished.');
})();
