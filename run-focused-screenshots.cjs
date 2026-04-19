const { chromium, devices } = require('playwright');
const path = require('path');

(async () => {
    const outputDir = 'test-results/visual-inspection/focused';
    const browser = await chromium.launch();
    
    try {
        const desktopContext = await browser.newContext({
            viewport: { width: 1440, height: 1100 }
        });
        const desktopPage = await desktopContext.newPage();
        
        console.log('Starting desktop pass (login)...');
        await desktopPage.goto('http://localhost:3000', { waitUntil: 'load' });
        
        // Wait for inputs and fill
        await desktopPage.waitForSelector('input', { timeout: 10000 });
        await desktopPage.getByLabel(/email/i).fill('admin');
        await desktopPage.getByLabel(/password/i).fill('admin');
        await desktopPage.getByRole('button', { name: /log in/i }).click();
        
        await desktopPage.waitForSelector('.app-sidebar-shell', { timeout: 20000 });
        console.log('Sidebar detected.');

        // Patient Registry
        await desktopPage.getByRole('button', { name: 'Patient Registry' }).click();
        await desktopPage.waitForFunction(() => {
            const rows = document.querySelectorAll('.registry-row').length > 1;
            const noPatients = document.body.innerText.includes('No patients found');
            const isLoading = document.body.innerText.includes('Loading patients...');
            return (rows || noPatients) && !isLoading;
        }, { timeout: 15000 });
        await desktopPage.screenshot({ path: path.join(outputDir, 'focused-registry.png') });
        console.log('Saved: focused-registry.png');

        const patientLink = desktopPage.locator('.registry-link').first();
        if (await patientLink.isVisible()) {
            await patientLink.scrollIntoViewIfNeeded();
            await patientLink.click();
            await desktopPage.waitForTimeout(2000);
            await desktopPage.screenshot({ path: path.join(outputDir, 'focused-patient.png') });
            console.log('Saved: focused-patient.png');
        }

        // Chart Builder
        await desktopPage.getByRole('button', { name: 'Chart Builder' }).click();
        const chartState = await Promise.race([
            desktopPage.waitForSelector('iframe[title="Superset"]', { state: 'visible' }).then(() => 'iframe'),
            desktopPage.waitForSelector('text="Superset URL not set"', { state: 'visible' }).then(() => 'fallback')
        ]);
        await desktopPage.screenshot({ path: path.join(outputDir, 'focused-charts.png') });
        console.log(`Saved: focused-charts.png (Resolved to: ${chartState})`);
        
        await desktopContext.close();

        // Mobile
        const mobileContext = await browser.newContext({...devices['iPhone 13']});
        const mobilePage = await mobileContext.newPage();
        console.log('Starting mobile pass...');
        await mobilePage.goto('http://localhost:3000', { waitUntil: 'load' });
        await mobilePage.waitForSelector('input', { timeout: 10000 });
        await mobilePage.getByLabel(/email/i).fill('admin');
        await mobilePage.getByLabel(/password/i).fill('admin');
        await mobilePage.getByRole('button', { name: /log in/i }).click();

        await mobilePage.waitForFunction(() => document.body.innerText.toUpperCase().includes('BIOLINK'), { timeout: 15000 });
        await mobilePage.screenshot({ path: path.join(outputDir, 'focused-mobile-home.png') });
        console.log('Saved: focused-mobile-home.png');

        const menuButton = mobilePage.getByRole('button', { name: /Open navigation menu/i });
        await menuButton.click();
        await mobilePage.waitForTimeout(1000);
        await mobilePage.screenshot({ path: path.join(outputDir, 'focused-mobile-nav.png') });
        console.log('Saved: focused-mobile-nav.png');

    } catch (err) {
        console.error('Failure:', err);
        process.exit(1);
    } finally {
        await browser.close();
    }
    console.log('Visual inspection task complete.');
})();
