const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    try {
        console.log('Navigating to http://localhost:3000...');
        await page.goto('http://localhost:3000', { waitUntil: 'load', timeout: 60000 });
        
        console.log('Logging in...');
        const userInp = await page.waitForSelector('input[name="username"], input[type="text"]', { timeout: 30000 });
        await userInp.fill('admin');
        await page.fill('input[type="password"]', 'admin');
        await page.click('button:has-text("Sign In")');
        
        console.log('Waiting for URL change or dashboard element...');
        try {
            await page.waitForTimeout(5000); 
            console.log('Current URL:', page.url());
        } catch(e) {}

        console.log('Attempting to click Chart Builder...');
        const chartBuilderLink = await page.waitForSelector('text=/Chart Builder/i', { timeout: 60000 });
        await chartBuilderLink.click();
        
        console.log('Waiting for iframe...');
        const iframeSelector = 'iframe[title="Superset"]';
        await page.waitForSelector(iframeSelector, { timeout: 60000 });
        const iframe = await page.$(iframeSelector);
        
        const iframeSrc = await iframe.getAttribute('src');
        console.log('Iframe src:', iframeSrc);
        
        const iframeBox = await iframe.boundingBox();
        console.log('Iframe bounding box:', JSON.stringify(iframeBox, null, 2));
        
        const cardSelector = '[data-slot="card"]';
        const card = await page.$(cardSelector);
        if (card) {
            const cardBox = await card.boundingBox();
            console.log('Card bounding box:', JSON.stringify(cardBox, null, 2));
        }

        const cardContentSelector = '[data-slot="card-content"]';
        const cardContent = await page.$(cardContentSelector);
        if (cardContent) {
            const cardContentBox = await cardContent.boundingBox();
            console.log('Card content bounding box:', JSON.stringify(cardContentBox, null, 2));
            
            const parentMetrics = await cardContent.evaluate(el => {
                const s = window.getComputedStyle(el);
                return { height: s.height, minHeight: s.minHeight };
            });
            console.log('Card-content (parent) computed metrics:', JSON.stringify(parentMetrics, null, 2));
        }
        
        const iframeMetrics = await iframe.evaluate(el => {
            const s = window.getComputedStyle(el);
            return { height: s.height, minHeight: s.minHeight };
        });
        console.log('Iframe computed metrics:', JSON.stringify(iframeMetrics, null, 2));
        
        const screenshotPath = 'test-results/visual-inspection/focused-fix/chart-builder-after-direct-style-fix.png';
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log('Screenshot saved to:', screenshotPath);
        
    } catch (e) {
        console.error('Error during verification:', e);
        await page.screenshot({ path: 'test-results/visual-inspection/focused-fix/error.png', fullPage: true });
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
