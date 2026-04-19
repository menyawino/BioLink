const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const outputDir = 'test-results/visual-inspection/final-pass';
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const issues = [];
    const browser = await chromium.launch();

    try {
        const desktopContext = await browser.newContext({
            viewport: { width: 1440, height: 1100 }
        });
        const desktopPage = await desktopContext.newPage();
        
        console.log('Visiting Login Page...');
        await desktopPage.goto('http://localhost:3000/login');
        
        console.log('Logging in...');
        await desktopPage.waitForSelector('input', { timeout: 10000 });
        const inputs = await desktopPage.$$eval('input', els => els.map(el => ({type: el.type, name: el.name, placeholder: el.placeholder, id: el.id})));
        console.log('Inputs found:', JSON.stringify(inputs));
        
        // Try filling first visible text/email and password inputs
        await desktopPage.locator('input[type="text"], input[name*="user"], input[placeholder*="ser"]').first().fill('admin');
        await desktopPage.locator('input[type="password"]').first().fill('admin');
        
        const loginBtn = desktopPage.locator('button[type="submit"], button:has-text("Log in"), button:has-text("Login"), .login-button').first();
        await loginBtn.click();

        console.log('Waiting for navigation/sidebar...');
        await desktopPage.waitForSelector('.app-sidebar-shell, .main-content', { timeout: 30000 });

        console.log('Opening Chart Builder...');
        await desktopPage.locator('a:has-text("Chart Builder"), [href*="chart"]').first().click();
        
        let state = 'unknown';
        try {
            await Promise.race([
                desktopPage.waitForSelector('.superset-embedded-mount iframe', { timeout: 10000 }).then(() => { state = 'embedded'; }),
                desktopPage.waitForSelector(':has-text("failed"), :has-text("Error")', { timeout: 10000 }).then(() => { state = 'fallback'; })
            ]);
        } catch (e) {
            state = 'timeout/other';
        }
        console.log(`Chart Builder State: ${state}`);
        await desktopPage.screenshot({ path: path.join(outputDir, 'chart-builder-final.png') });

        console.log('Opening Patient Registry...');
        await desktopPage.locator('a:has-text("Patient Registry"), [href*="registry"]').first().click();
        await desktopPage.waitForTimeout(2000);
        await desktopPage.screenshot({ path: path.join(outputDir, 'registry-final.png') });

        await desktopContext.close();

        const mobileContext = await browser.newContext({ ...devices['iPhone 13'] });
        const mobilePage = await mobileContext.newPage();
        await mobilePage.goto('http://localhost:3000/login');
        await mobilePage.locator('input[type="text"], input[name*="user"]').first().fill('admin');
        await mobilePage.locator('input[type="password"]').first().fill('admin');
        await mobilePage.locator('button[type="submit"], button:has-text("Login")').first().click();
        await mobilePage.waitForTimeout(3000);
        await mobilePage.screenshot({ path: path.join(outputDir, 'mobile-home-final.png') });

        const menuButton = mobilePage.locator('.navbar-toggler, button[aria-label="Toggle navigation"], .mobile-menu-trigger, .header button').first();
        if (await menuButton.isVisible()) {
            await menuButton.click();
            await mobilePage.waitForTimeout(500);
            await mobilePage.screenshot({ path: path.join(outputDir, 'mobile-nav-final.png') });
        }
        await mobileContext.close();

    } catch (err) {
        console.error('Test script failed:', err);
        issues.push({ type: 'fatal', message: err.message });
    } finally {
        fs.writeFileSync(path.join(outputDir, 'runtime-issues.json'), JSON.stringify(issues, null, 2));
        await browser.close();
    }
})();
