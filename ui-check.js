const { chromium } = require("@playwright/test");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/usr/bin/chromium-browser",
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({ viewport: { width: 1720, height: 1080 } });
  await page.goto("http://frontend", { waitUntil: "networkidle" });

  await page.evaluate(() => {
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (input, init) => {
      const rawUrl = typeof input === "string" ? input : input.url;
      const url = rawUrl.replace("http://localhost:3001", "http://frontend");
      const jsonResponse = (data) => new Response(JSON.stringify(data), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.includes("/api/auth/token")) {
        return jsonResponse({ access_token: "mock-access", refresh_token: "mock-refresh", token_type: "bearer" });
      }
      if (url.includes("/api/auth/me")) {
        return jsonResponse({ success: true, data: { username: "admin", email: "admin@biolink.local", full_name: "Administrator", role: "admin", scopes: ["admin", "read", "write", "delete"], disabled: false, created_at: new Date().toISOString(), last_login: new Date().toISOString() } });
      }
      if (url.includes("/api/analytics/cohort-filters")) {
        return jsonResponse({ success: true, data: { genders: [{ label: "Male", count: 1200 }, { label: "Female", count: 900 }], nationalities: [{ label: "Egyptian", count: 1800 }, { label: "Sudanese", count: 300 }], regions: [{ label: "Cairo", count: 840 }, { label: "Alexandria", count: 560 }], diagnoses: [], riskFactors: [], dataTypes: [{ label: "Imaging", count: 1300 }, { label: "Echocardiography", count: 1180 }, { label: "Cardiac MRI", count: 620 }, { label: "Clinical Labs", count: 1500 }, { label: "Genomics", count: 410 }] } });
      }
      if (url.includes("/api/patients")) {
        return jsonResponse({ success: true, data: [{ id: 1, dna_id: "DNA-0001", age: 54, gender: "Male", nationality: "Egyptian", enrollment_date: "2025-01-10", current_city: "Cairo", heart_rate: 72, systolic_bp: 130, diastolic_bp: 85, bmi: 28.1, hba1c: 6.2, echo_ef: 58, mri_ef: 55, current_city_category: "Urban", has_mri: true, has_echo: true, data_completeness: 86 }] });
      }
      if (url.includes("/api/analytics/overview")) {
        return jsonResponse({ success: true, data: { totalPatients: 2100, maleCount: 1200, femaleCount: 900, ageDataCount: 2000, hasAgeData: true, averageAge: "51", dataCompleteness: "82", withMri: 620, withEcho: 1180, withBothEchoMri: 500, withEcg: 950 } });
      }
      return originalFetch(input, init);
    };
  });

  await page.fill("input[placeholder=\"Enter your username\"]", "admin");
  await page.fill("input[placeholder=\"Enter your password\"]", "admin");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(2800);

  const registryTab = page.locator("button:has-text(\"Patient Registry\"), a:has-text(\"Patient Registry\"), [role=tab]:has-text(\"Patient Registry\")").first();
  if (await registryTab.count()) {
    await registryTab.click();
    await page.waitForTimeout(1500);
  }

  await page.screenshot({ path: "/app/outputs/ui-registry-visual-check.png", fullPage: true });
  const toolbar = page.locator(".registry-toolbar").first();
  if (await toolbar.count()) {
    await toolbar.screenshot({ path: "/app/outputs/ui-registry-toolbar-check.png" });
  }
  await browser.close();
})();
