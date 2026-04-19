const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'test-results/visual-inspection/final-pass';
if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

const runtimeIssues = {
  consoleErrors: [],
  pageErrors: [],
  failedRequests: []
};

async function setupPage(context) {
  const page = await context.newPage();
  page.on('console', msg => {
    if (msg.type() === 'error') runtimeIssues.consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => {
    runtimeIssues.pageErrors.push(err.message);
  });
  page.on('requestfailed', request => {
    runtimeIssues.failedRequests.push(`${request.method()} ${request.url()}: ${request.failure().errorText}`);
  });
  return page;
}

async function login(page) {
  console.log('Navigating to http://localhost:3000...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  
  try {
    // Attempt to fill by placeholder or label
    await page.fill('input[placeholder*="Username" i], input[name="username"], label:has-text("Username") + input', 'admin');
    await page.fill('input[placeholder*="Password" i], input[name="password"], label:has-text("Password") + input', 'admin');
    await page.click('button:has-text("Sign In")');
  } catch (e) {
    const body = await page.innerText('body');
    console.error('Login interaction failed:', e.message);
    console.log('Page Body Content:', body.substring(0, 1000));
    process.exit(1);
  }

  try {
    await Promise.race([
      page.waitForSelector('.app-sidebar-shell', { timeout: 15000 }),
      page.waitForURL(url => url.pathname !== '/', { timeout: 15000 })
    ]);
  } catch (e) {
    const body = await page.innerText('body');
    console.error('Login failed or timed out. Dashboard/Sidebar not visible.');
    console.log('Page Body Content:', body.substring(0, 1000));
    process.exit(1);
  }
}

(async () => {
  const browser = await chromium.launch();
  
  // 1. Desktop Pass
  const desktopContext = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
  const page = await setupPage(desktopContext);
  
  await login(page);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'post-login-home.png') });
  
  console.log('Navigating to Chart Builder...');
  await page.click('text=Chart Builder');
  
  const outcome = await Promise.race([
    page.waitForSelector('.superset-embedded-mount iframe', { timeout: 45000 }).then(() => 'embedded'),
    page.waitForSelector('text=Embedded analytics unavailable', { timeout: 45000 }).then(() => 'fallback'),
    page.waitForSelector('text=Superset dashboard not configured', { timeout: 45000 }).then(() => 'not_configured')
  ]).catch(() => 'timeout');

  console.log('Chart Builder Outcome:', outcome);
  console.log('Current URL:', page.url());
  
  if (outcome === 'embedded') {
    const iframeSrc = await page.getAttribute('.superset-embedded-mount iframe', 'src');
    console.log('Iframe Src:', iframeSrc);
  }
  
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'chart-builder-final.png') });

  console.log('Navigating to Patient Registry...');
  // Click Patient Registry in sidebar
  await page.click('text=Patient Registry');
  await Promise.race([
    page.waitForSelector('table tr', { timeout: 15000 }),
    page.waitForSelector('text=No patients found', { timeout: 15000 })
  ]).catch(() => console.log('Wait for registry table/text timed out.'));
  
  await page.screenshot({ path: path.join(ARTIFACT_DIR, 'registry-final.png') });

  // 2. Mobile Pass
  console.log('Starting Mobile Pass...');
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
  });
  const mobilePage = await setupPage(mobileContext);
  await login(mobilePage);
  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, 'mobile-home-final.png') });
  
  // Try to open mobile nav if a hamburger/menu button exists
  const menuButton = await mobilePage.$('button[aria-label*="menu" i], button:has(svg), .mobile-menu-button');
  if (menuButton) {
    await menuButton.click();
    await new Promise(r => setTimeout(r, 1000));
    await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, 'mobile-nav-final.png') });
  }

  // Finalize
  fs.writeFileSync(path.join(ARTIFACT_DIR, 'runtime-issues.json'), JSON.stringify(runtimeIssues, null, 2));
  
  console.log('\nCreated files:');
  fs.readdirSync(ARTIFACT_DIR).forEach(file => console.log(`- ${path.join(ARTIFACT_DIR, file)}`));

  await browser.close();
})();
