const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const networkRequests = [];
    page.on('request', request => {
        const url = request.url();
        if (url.includes('superset') || url.includes('embedded') || url.includes('/api/')) {
            networkRequests.push(`${request.method()} ${url}`);
        }
    });

    try {
        console.log('Navigating to http://localhost:3000');
        await page.goto('http://localhost:3000');

        console.log('Logging in...');
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'admin');
        await page.click('button:has-text("Sign In")');
        await page.waitForNavigation();

        console.log('Opening Chart Builder...');
        await page.click('text=Chart Builder');
        
        console.log('Waiting 10 seconds for page to settle...');
        await new Promise(resolve => setTimeout(resolve, 10000));

        console.log('\n--- Visible Text in Main Content ---');
        const mainContent = await page.textContent('main');
        console.log(mainContent ? mainContent.trim() : 'No main content found');

        const selectors = [
            '.superset-workspace-card',
            '.superset-embedded-mount',
            '.superset-embedded-mount iframe',
            'iframe',
            'text=Embedded analytics unavailable',
            'text=Superset dashboard not configured'
        ];

        console.log('\n--- Selector Existence ---');
        for (const selector of selectors) {
            const count = await page.locator(selector).count();
            console.log(`${selector}: ${count}`);
        }

        console.log('\n--- Iframes Analysis ---');
        const iframes = page.locator('iframe');
        const iframeCount = await iframes.count();
        for (let i = 0; i < iframeCount; i++) {
            const iframe = iframes.nth(i);
            const src = await iframe.getAttribute('src');
            const box = await iframe.boundingBox();
            const visible = await iframe.isVisible();
            console.log(`Iframe ${i}:`);
            console.log(`  src: ${src}`);
            console.log(`  visible: ${visible}`);
            if (box) {
                console.log(`  dimensions: ${box.width}x${box.height}`);
            }
        }

        console.log('\n--- .superset-workspace-card innerHTML (first 1500 chars) ---');
        const workspaceCard = page.locator('.superset-workspace-card').first();
        if (await workspaceCard.count() > 0) {
            const innerHTML = await workspaceCard.innerHTML();
            console.log(innerHTML.substring(0, 1500));
        } else {
            console.log('Not found');
        }

        console.log('\n--- Relevant Network Requests ---');
        networkRequests.forEach(req => console.log(req));

        await page.screenshot({ path: 'test-results/visual-inspection/chart-builder-dom-inspect.png', fullPage: true });
        console.log('\nScreenshot saved to test-results/visual-inspection/chart-builder-dom-inspect.png');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
})();
