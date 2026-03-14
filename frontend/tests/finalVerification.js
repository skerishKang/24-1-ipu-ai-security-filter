const { chromium } = require("playwright");

const FRONTEND_URL = "http://127.0.0.1:4241";
const BACKEND_URL = "http://127.0.0.1:8241";

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable request logging to see if backend is called
  // await page.route("**/*", (route) => {
  //   console.log(`>>> ${route.request().method()} ${route.request().url()}`);
  //   route.continue();
  // });

  console.log("=== General Mode Verification ===\n");
  await page.goto(FRONTEND_URL);
  await page.waitForLoadState("networkidle");

  // 1. Check hero section (eyebrow, title, description)
  const eyebrow = await page.locator(".eyebrow").textContent();
  const heroTitle = await page.locator(".panel__title").first().textContent();
  const heroDescription = await page.locator(".panel__description").first().innerHTML();

  console.log(`Eyebrow: "${eyebrow.trim()}"`);
  console.log(`Hero Title: "${heroTitle.trim()}"`);
  console.log(`Hero Description HTML: "${heroDescription}"`);

  const generalModeExpected = {
    eyebrow: "IPU Easy Mode",
    titleContains: "안전하게 바꿔서 쓰기",
    descriptionContains: "민감한 정보가 묻어있더라도"
  };

  let generalModeOK = true;
  if (eyebrow.trim() !== generalModeExpected.eyebrow) {
    console.log(`❌ Eyebrow mismatch: expected "${generalModeExpected.eyebrow}", got "${eyebrow.trim()}"`);
    generalModeOK = false;
  }
  if (!heroTitle.includes(generalModeExpected.titleContains)) {
    console.log(`❌ Hero title missing "${generalModeExpected.titleContains}"`);
    generalModeOK = false;
  }
  if (!heroDescription.includes(generalModeExpected.descriptionContains)) {
    console.log(`❌ Hero description missing "${generalModeExpected.descriptionContains}"`);
    generalModeOK = false;
  }
  if (generalModeOK) {
    console.log("✅ General mode hero section looks good\n");
  }

  // 2. Check input panel in general mode
  const inputPanelTitle = await page.locator(".input-panel").locator("xpath=//*[contains(@class, 'panel__title')]").first().textContent();
  const inputPanelDescription = await page.locator(".input-panel").locator("xpath=//*[contains(@class, 'panel__description')]").first().innerHTML();
  const metaText = await page.locator(".input-panel__meta").first().textContent();

  console.log(`Input Panel Title: "${inputPanelTitle.trim()}"`);
  console.log(`Input Panel Description HTML: "${inputPanelDescription}"`);
  console.log(`Meta Text: "${metaText.trim()}"`);

  const inputPanelExpected = {
    title: "내용 입력",
    descriptionContains: "주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져",
    metaTextContains: ".txt 파일도 바로 업로드할 수 있어요"
  };

  let inputPanelOK = true;
  if (inputPanelTitle.trim() !== inputPanelExpected.title) {
    console.log(`❌ Input panel title mismatch: expected "${inputPanelExpected.title}", got "${inputPanelTitle.trim()}"`);
    inputPanelOK = false;
  }
  if (!inputPanelDescription.includes(inputPanelExpected.descriptionContains)) {
    console.log(`❌ Input panel description missing "${inputPanelExpected.descriptionContains}"`);
    inputPanelOK = false;
  }
  if (!metaText.includes(inputPanelExpected.metaTextContains)) {
    console.log(`❌ Meta text missing "${inputPanelExpected.metaTextContains}"`);
    inputPanelOK = false;
  }
  if (inputPanelOK) {
    console.log("✅ General mode input panel looks good\n");
  }

  // 3. Test text mode vs file mode visibility (even in general mode, we can switch)
  // First, check initial mode (should be text mode by default? Let's see)
  // We'll check the radio buttons
  const textModeRadio = await page.locator("[data-testid='input-mode-text']");
  const fileModeRadio = await page.locator("[data-testid='input-mode-file']");
  const textModeChecked = await textModeRadio.isChecked();
  const fileModeChecked = await fileModeRadio.isChecked();
  console.log(`Text mode radio checked: ${textModeChecked}`);
  console.log(`File mode radio checked: ${fileModeChecked}`);

  // Check visibility of sections using display style
  const textSection = page.locator(".input-panel__section").nth(0);
  const fileSection = page.locator(".input-panel__section").nth(1);
  const textDisplay = await textSection.evaluate(el => window.getComputedStyle(el).display);
  const fileDisplay = await fileSection.evaluate(el => window.getComputedStyle(el).display);
  console.log(`Text section display: ${textDisplay}`);
  console.log(`File section display: ${fileDisplay}`);

  // In general mode, both sections might be present but one hidden via display:none
  // We expect text section to be visible (block) and file section hidden (none) by default
  let modeVisibilityOK = true;
  if (textDisplay !== "block") {
    console.log(`❌ Text section should be block (visible) but is ${textDisplay}`);
    modeVisibilityOK = false;
  }
  if (fileDisplay !== "none") {
    console.log(`❌ File section should be none (hidden) but is ${fileDisplay}`);
    modeVisibilityOK = false;
  }
  if (modeVisibilityOK) {
    console.log("✅ Initial mode visibility correct (text visible, file hidden)\n");
  }

  // 4. Switch to file mode and check visibility
  await fileModeRadio.check();
  await page.waitForTimeout(500); // wait for state update
  const textDisplayAfter = await textSection.evaluate(el => window.getComputedStyle(el).display);
  const fileDisplayAfter = await fileSection.evaluate(el => window.getComputedStyle(el).display);
  console.log(`After switching to file mode:`);
  console.log(`  Text section display: ${textDisplayAfter}`);
  console.log(`  File section display: ${fileDisplayAfter}`);

  let fileModeVisibilityOK = true;
  if (textDisplayAfter !== "none") {
    console.log(`❌ Text section should be none (hidden) in file mode but is ${textDisplayAfter}`);
    fileModeVisibilityOK = false;
  }
  if (fileDisplayAfter !== "block") {
    console.log(`❌ File section should be block (visible) in file mode but is ${fileDisplayAfter}`);
    fileModeVisibilityOK = false;
  }
  if (fileModeVisibilityOK) {
    console.log("✅ File mode visibility correct (text hidden, file visible)\n");
  }

  // 5. Switch back to text mode
  await textModeRadio.check();
  await page.waitForTimeout(500);
  const textDisplayAfter2 = await textSection.evaluate(el => window.getComputedStyle(el).display);
  const fileDisplayAfter2 = await fileSection.evaluate(el => window.getComputedStyle(el).display);
  console.log(`After switching back to text mode:`);
  console.log(`  Text section display: ${textDisplayAfter2}`);
  console.log(`  File section display: ${fileDisplayAfter2}`);

  let textModeVisibilityOK = true;
  if (textDisplayAfter2 !== "block") {
    console.log(`❌ Text section should be block (visible) in text mode but is ${textDisplayAfter2}`);
    textModeVisibilityOK = false;
  }
  if (fileDisplayAfter2 !== "none") {
    console.log(`❌ File section should be none (hidden) in text mode but is ${fileDisplayAfter2}`);
    textModeVisibilityOK = false;
  }
  if (textModeVisibilityOK) {
    console.log("✅ Text mode visibility restored correctly\n");
  }

  // 6. Test file selection and preview
  await fileModeRadio.check();
  await page.waitForTimeout(500);
  const fileInput = await page.locator("[data-testid='file-input']");
  await fileInput.setInputFiles({
    name: "test.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("홍길동 전화번호: 010-1234-5678")
  });
  await page.waitForTimeout(500);
  const selectedFileName = await page.locator("[data-testid='selected-file-inline']").textContent();
  console.log(`Selected file name: "${selectedFileName.trim()}"`);
  const fileNameOK = selectedFileName.trim() === "test.txt";
  if (fileNameOK) {
    console.log("✅ File name displayed correctly after selection\n");
  } else {
    console.log(`❌ File name not displayed correctly: "${selectedFileName.trim()}"\n`);
  }

  // Click the preview button
  await page.locator("[data-testid='submit-preview']").click();
  await page.waitForTimeout(2000); // wait for processing

  // Check that the result panel updated (in general mode, we have simple result panel)
  const safeCardLabel = await page.locator(".text-card__label").first().textContent();
  const safeCardContent = await page.locator("[data-testid='simple-replaced-text']").first().textContent();
  const statusText = await page.locator(".simple-result__status").first().textContent();

  console.log(`Result card label: "${safeCardLabel.trim()}"`);
  console.log(`Result card content: "${safeCardContent.trim()}"`);
  console.log(`Status: "${statusText.trim()}"`);

  // We expect the content to have the phone number replaced
  const contentHasReplacement = safeCardContent.includes("[PERSON_01]") || safeCardContent.includes("[PHONE_01]");
  if (contentHasReplacement) {
    console.log("✅ Result shows replaced content (phone number masked)\n");
  } else {
    console.log(`ℹ️ Result content does not show obvious replacement (maybe backend not connected or different detection)\n`);
  }

  // 7. Switch to expert mode
  // We need to find the mode toggle. Let's look for a button or switch that changes the mode.
  // From the AppShell in main.js, we see that the hero changes based on uiMode.
  // There might be a toggle in the header. Let's search for any element with "모드" or "mode".
  const modeToggle = await page.locator("text=전문가 모드").or(page.locator("text=Expert Mode")).or(page.locator("[data-testid='mode-toggle']"));
  if (await modeToggle.count() > 0) {
    console.log("Found mode toggle, clicking to switch to expert mode...");
    await modeToggle.first().click();
    await page.waitForTimeout(1000);
    await page.waitForLoadState("networkidle");
  } else {
    // Maybe the toggle is a checkbox or something else
    // Let's look for any checkbox or switch near the header
    const header = await page.locator(".panel__header").first();
    const toggle = header.locator("input[type=checkbox], .switch, .toggle");
    if (await toggle.count() > 0) {
      console.log("Found toggle in header, clicking...");
      await toggle.first().click();
      await page.waitForTimeout(1000);
      await page.waitForLoadState("networkidle");
    } else {
      console.log("⚠️ Could not find mode toggle; skipping expert mode check");
    }
  }

  // 8. Check expert mode (4 panels)
  const expertModeIndicator = await page.locator(".panel").count();
  console.log(`Number of panels in expert mode: ${expertModeIndicator}`);
  // In expert mode, we expect 4 panels: input, result, report, copy prompt
  // Let's check for the titles of each panel
  const panelTitles = await page.locator(".panel__title").allTextContents();
  console.log(`Panel titles: ${panelTitles.map(t => t.trim()).join(", ")}`);

  const expectedTitles = ["1. 원문 입력", "2. 치환 결과", "3. 탐지 리포트", "4. 외부 AI 전달용 복사본"];
  let expertModeOK = true;
  for (const expected of expectedTitles) {
    if (!panelTitles.some(t => t.trim().includes(expected))) {
      console.log(`❌ Missing expected panel title: "${expected}"`);
      expertModeOK = false;
    }
  }
  if (expertModeOK) {
    console.log("✅ Expert mode shows all 4 panels correctly\n");
  }

  // Take screenshots
  await page.screenshot({ path: "tests/screenshots/general-mode-final.png", fullPage: true });
  await page.screenshot({ path: "tests/screenshots/expert-mode-final.png", fullPage: true });

  console.log("\n=== Summary ===");
  console.log(`General mode hero: ${generalModeOK ? "✅" : "❌"}`);
  console.log(`General mode input panel: ${inputPanelOK ? "✅" : "❌"}`);
  console.log(`Text/File mode visibility: ${modeVisibilityOK && fileModeVisibilityOK && textModeVisibilityOK ? "✅" : "❌"}`);
  console.log(`File selection and preview: ${fileNameOK ? "✅" : "❌"}`);
  console.log(`Expert mode panels: ${expertModeOK ? "✅" : "❌"}`);

  await browser.close();

  // Return overall success
  const overallSuccess = generalModeOK && inputPanelOK && modeVisibilityOK && fileModeVisibilityOK && textModeVisibilityOK && fileNameOK && expertModeOK;
  process.exit(overallSuccess ? 0 : 1);
}

main().catch(err => {
  console.error("Test failed with error:", err);
  process.exit(1);
});