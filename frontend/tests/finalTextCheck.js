const { chromium } = require("playwright");

const FRONTEND_URL = "http://127.0.0.1:4241";

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log("=== Final Verification of Text Changes ===\n");
  await page.goto(FRONTEND_URL);
  await page.waitForLoadState("networkidle");
  // Wait a bit more for any dynamic content
  await page.waitForTimeout(1000);

  const bodyText = await page.textContent("body");

  console.log("Checking for updated text in the page...\n");

  // 1. Eyebrow: "IPU Easy Mode"
  const eyebrowOK = bodyText.includes("IPU Easy Mode");
  console.log(`Eyebrow "IPU Easy Mode": ${eyebrowOK ? "✅" : "❌"}`);

  // 2. Hero title: "안전하게 바꿔서 쓰기"
  const heroTitleOK = bodyText.includes("안전하게 바꿔서 쓰기");
  console.log(`Hero title "안전하게 바꿔서 쓰기": ${heroTitleOK ? "✅" : "❌"}`);

  // 3. Hero description: contains "민감한 정보가 묻어있더라도"
  const heroDescOK = bodyText.includes("민감한 정보가 묻어있더라도");
  console.log(`Hero description contains "민감한 정보가 묻어있더라도": ${heroDescOK ? "✅" : "❌"}`);

  // 4. Input panel title: "내용 입력"
  const inputTitleOK = bodyText.includes("내용 입력");
  console.log(`Input panel title "내용 입력": ${inputTitleOK ? "✅" : "❌"}`);

  // 5. Input panel description: contains "주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져"
  const inputDescOK = bodyText.includes("주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져");
  console.log(`Input panel description contains "주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져": ${inputDescOK ? "✅" : "❌"}`);

  // 6. Meta text: contains ".txt 파일도 바로 업로드할 수 있어요"
  const metaTextOK = bodyText.includes(".txt 파일도 바로 업로드할 수 있어요");
  console.log(`Meta text contains ".txt 파일도 바로 업로드할 수 있어요": ${metaTextOK ? "✅" : "❌"}`);

  // 7. Text mode section header: "✏️ 글 직접 입력"
  const textSectionHeaderOK = bodyText.includes("✏️ 글 직접 입력");
  console.log(`Text mode section header "✏️ 글 직접 입력": ${textSectionHeaderOK ? "✅" : "❌"}`);

  // 8. Text mode section hint: "편지, 메모, 채팅 내용을 그대로 붙여넣으세요"
  const textSectionHintOK = bodyText.includes("편지, 메모, 채팅 내용을 그대로 붙여넣으세요");
  console.log(`Text mode section hint "편지, 메모, 채팅 내용을 그대로 붙여넣으세요": ${textSectionHintOK ? "✅" : "❌"}`);

  // 9. File mode section header: "📁 파일로 올리기"
  const fileSectionHeaderOK = bodyText.includes("📁 파일로 올리기");
  console.log(`File mode section header "📁 파일로 올리기": ${fileSectionHeaderOK ? "✅" : "❌"}`);

  // 10. File mode section hint: "컴퓨터에 있는 .txt 파일을 올리면 편해요"
  const fileSectionHintOK = bodyText.includes("컴퓨터에 있는 .txt 파일을 올리면 편해요");
  console.log(`File mode section hint "컴퓨터에 있는 .txt 파일을 올리면 편해요": ${fileSectionHintOK ? "✅" : "❌"}`);

  // 11. File label: "📄 .txt 파일만 지원"
  const fileLabelOK = bodyText.includes("📄 .txt 파일만 지원");
  console.log(`File label "📄 .txt 파일만 지원": ${fileLabelOK ? "✅" : "❌"}`);

  // 12. Dropzone header: "📁 파일을 여기에 끌어다 놓거나"
  const dropzoneHeaderOK = bodyText.includes("📁 파일을 여기에 끌어다 놓거나");
  console.log(`Dropzone header "📁 파일을 여기에 끌어다 놓거나": ${dropzoneHeaderOK ? "✅" : "❌"}`);

  // 13. Dropzone hint: "버튼으로 선택해도 돼요"
  const dropzoneHintOK = bodyText.includes("버튼으로 선택해도 돼요");
  console.log(`Dropzone hint "버튼으로 선택해도 돼요": ${dropzoneHintOK ? "✅" : "❌"}`);

  // 14. Simple result panel title: "결과 확인"
  const resultPanelTitleOK = bodyText.includes("결과 확인");
  console.log(`Result panel title "결과 확인": ${resultPanelTitleOK ? "✅" : "❌"}`);

  // 15. Simple result panel description: contains "🔒 가려진 내용을 확인하고 복사하세요"
  const resultPanelDescOK = bodyText.includes("🔒 가려진 내용을 확인하고 복사하세요");
  console.log(`Result panel description contains "🔒 가려진 내용을 확인하고 복사하세요": ${resultPanelDescOK ? "✅" : "❌"}`);

  // 16. Simple result panel badge: contains "개 보호"
  const resultPanelBadgeOK = bodyText.includes("개 보호");
  console.log(`Result panel badge contains "개 보호": ${resultPanelBadgeOK ? "✅" : "❌"}`);

  // 17. Safe card label: "🔒 가려진 결과"
  const safeCardLabelOK = bodyText.includes("🔒 가려진 결과");
  console.log(`Safe card label "🔒 가려진 결과": ${safeCardLabelOK ? "✅" : "❌"}`);

  // 18. Original details summary: "👀 원문 보기"
  const originalDetailsOK = bodyText.includes("👀 원문 보기");
  console.log(`Original details summary "👀 원문 보기": ${originalDetailsOK ? "✅" : "❌"}`);

  // 19. Action status: "이거 복사하면 끝!"
  const actionStatusOK = bodyText.includes("이거 복사하면 끝!");
  console.log(`Action status "이거 복사하면 끝!": ${actionStatusOK ? "✅" : "❌"}`);

  // 20. Action button: "결과 복사"
  const actionButtonOK = bodyText.includes("결과 복사");
  console.log(`Action button "결과 복사": ${actionButtonOK ? "✅" : "❌"}`);

  // 21. Mode hint (when in text mode): "✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요"
  // We need to check if we are in text mode by default. Let's check the radio button state.
  const textModeRadio = await page.locator("[data-testid='input-mode-text']");
  const isTextModeChecked = await textModeRadio.isChecked();
  let modeHintOK = false;
  if (isTextModeChecked) {
    const modeHintText = await page.locator(".input-panel__mode-hint").textContent();
    modeHintOK = modeHintText.includes("✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요");
    console.log(`Mode hint (text mode) "✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요": ${modeHintOK ? "✅" : "❌"}`);
  } else {
    console.log(`Mode hint (text mode) "✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요": ℹ️ (not in text mode)`);
  }

  // 22. Mode hint (when in file mode): "📁 파일을 올리면 민감 정보가 가려져요"
  // Switch to file mode and check
  const fileModeRadio = await page.locator("[data-testid='input-mode-file']");
  await fileModeRadio.check();
  await page.waitForTimeout(500);
  const modeHintTextFile = await page.locator(".input-panel__mode-hint").textContent();
  const modeHintFileOK = modeHintTextFile.includes("📁 파일을 올리면 민감 정보가 가려져요");
  console.log(`Mode hint (file mode) "📁 파일을 올리면 민감 정보가 가려져요": ${modeHintFileOK ? "✅" : "❌"}`);

  // Switch back to text mode for any further checks
  await textModeRadio.check();
  await page.waitForTimeout(500);

  // Take a screenshot for visual verification
  await page.screenshot({ path: "tests/screenshots/final-verification.png", fullPage: true });
  console.log("\nScreenshot saved: tests/screenshots/final-verification.png");

  // Count the checks
  const checks = [
    eyebrowOK, heroTitleOK, heroDescOK, inputTitleOK, inputDescOK, metaTextOK,
    textSectionHeaderOK, textSectionHintOK, fileSectionHeaderOK, fileSectionHintOK,
    fileLabelOK, dropzoneHeaderOK, dropzoneHintOK, resultPanelTitleOK, resultPanelDescOK,
    resultPanelBadgeOK, safeCardLabelOK, originalDetailsOK, actionStatusOK, actionButtonOK,
    modeHintFileOK
  ];
  const passed = checks.filter(v => v === true).length;
  const total = checks.length;
  console.log(`\nPassed ${passed}/${total} checks`);

  if (passed === total) {
    console.log("🎉 All text updates are present!");
    await browser.close();
    process.exit(0);
  } else {
    console.log("❌ Some text updates are missing or incorrect.");
    await browser.close();
    process.exit(1);
  }
}

main().catch(err => {
  console.error("Test failed with error:", err);
  process.exit(1);
});