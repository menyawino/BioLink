const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    try {
        await page.goto('http://localhost:3000');
        await page.click('button:has-text("Sign In")');
        await page.fill('input[type="text"]', 'admin');
        await page.fill('input[type="password"]', 'admin');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(5000);

        const chartBuilderLink = await page.waitForSelector('text=/Chart Builder/i', { timeout: 10000 });
        await chartBuilderLink.click();
        await page.waitForSelector('iframe[title="Superset"]', { timeout: 15000 });

        const selectors = [
            '[data-slot="card"]',
            '[data-slot="card-content"]',
            'iframe[title="Superset"]'
        ];

        for (const selector of selectors) {
            console.log(`--- Metrics for: ${selector} ---`);
            const element = await page.$(selector);
            if (element) {
                const box = await element.boundingBox();
                const styles = await element.evaluate(el => {
                    const s = window.getComputedStyle(el);
                    return {
                        height: s.height,
                        minHeight: s.minHeight,
                        display: s.display,
                        flex: s.flex,
                        flexDirection: s.flexDirection
                    };
                });
                console.log('Bounding Box:', JSON.stringify(box, null, 2));
                console.log('Computed Styles:', JSON.stringify(styles, null, 2));
            } else {
                console.log('Element not found');
            }
        }
    } catch (e) {
        console.error('Error:', e.message);
    } finally {
        await browser.close();
    }
})();
