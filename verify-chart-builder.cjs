const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    try {
        console.log('Navigating to http://localhost:3000...');
        await page.goto('http://localhost:3000');
        await page.waitForTimeout(2000);

        // Sign In
        console.log('Finding Sign In button...');
        await page.click('button:has-text("Sign In")');
        await page.waitForTimeout(1000);

        // Login
        console.log('Filling login info...');
        await page.fill('input[type="text"]', 'admin');
        await page.fill('input[type="password"]', 'admin');
        await page.keyboard.press('Enter');

        console.log('Waiting for main navigation...');
        await page.waitForTimeout(5000);

        console.log('Clicking sidebar "Chart Builder"...');
        const chartBuilderLink = await page.waitForSelector('text=/Chart Builder/i', { timeout: 10000 });
        await chartBuilderLink.click();
        
        console.log('Waiting for iframe...');
        const iframe = await page.waitForSelector('iframe', { timeout: 15000 });
        
        const content = await page.innerText('body');
        console.log('Body text includes "Embedded Chart Builder":', content.includes('Embedded Chart Builder'));
        
        const iframeSrc = await iframe.getAttribute('src');
        console.log('Iframe src:', iframeSrc);
        
        const box = await iframe.boundingBox();
        console.log('Iframe bounding box:', JSON.stringify(box));

        const screenshotPath = 'test-results/visual-inspection/focused-fix/chart-builder-after-height-fix.png';
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`Screenshot saved to ${screenshotPath}`);

    } catch (e) {
        console.error('Error during verification:', e.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
