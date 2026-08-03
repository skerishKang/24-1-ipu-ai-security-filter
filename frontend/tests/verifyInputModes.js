import { chromium } from "playwright";

const FRONTEND_URL = "http://127.0.0.1:4241";

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log("=== 텍스트 모드 검증 ===\n");
  await page.goto(FRONTEND_URL);
  await page.waitForLoadState("networkidle");
  
  // 브라우저 캐시 방지를 위해 강제 새로고침
  await page.evaluate(() => location.reload());
  await page.waitForLoadState("networkidle");
  
  // 텍스트 모드 선택
  await page.getByTestId("input-mode-text").check();
  await page.waitForTimeout(500);

  // 텍스트 섹션 hidden 확인
  const textSection = page.locator(".input-panel__section").nth(0);
  const textSectionHidden = await textSection.getAttribute("hidden");
  console.log(`텍스트 섹션 hidden: ${textSectionHidden}`);

  // 텍스트 모드 전체 내용
  console.log("텍스트 모드 입력 패널 내용:");
  const textModeContent = await page.locator(".panel").first().innerText();
  console.log(textModeContent);

  // 파일 관련 문구 확인
  const textModeFilePhrases = [
    "선택된 파일 없음",
    "지원 형식: .txt",
    ".txt 파일을 여기로",
    "파일 업로드"
  ];
  console.log("\n텍스트 모드에서 숨겨야 할 문구 확인:");
  for (const phrase of textModeFilePhrases) {
    const visibleCount = await page.locator(`text=${phrase}`).count();
    console.log(`  "${phrase}": ${visibleCount}회`);
  }

  // 스크린샷
  await page.screenshot({ path: "tests/screenshots/text-mode.png", fullPage: true });
  console.log("\n스크린샷: tests/screenshots/text-mode.png");

  console.log("\n=== 파일 모드 검증 ===\n");
  
  // 파일 모드 선택
  await page.getByTestId("input-mode-file").check();
  await page.waitForTimeout(1000); // 상태 변경 대기

  // 파일 섹션 hidden 확인
  const fileSection = page.locator(".input-panel__section").nth(1);
  const fileSectionHidden = await fileSection.getAttribute("hidden");
  console.log(`파일 섹션 hidden: ${fileSectionHidden}`);

  // 파일 모드 전체 내용
  console.log("파일 모드 입력 패널 내용:");
  const fileModeContent = await page.locator(".panel").first().innerText();
  console.log(fileModeContent);

  // 중복 확인
  const phrases = ["선택된 파일 없음", "지원 형식", ".txt 파일을 여기로"];
  console.log("\n중복 확인:");
  for (const phrase of phrases) {
    const count = await page.locator(`text=${phrase}`).count();
    console.log(`  "${phrase}": ${count}회`);
  }

  // 줄 단위 분석
  console.log("\n줄 단위 분석:");
  const lines = fileModeContent.split('\n').filter(line => line.trim());
  lines.forEach((line, i) => {
    console.log(`${i+1}. "${line.substring(0, 60)}"`);
  });

  // 스크린샷
  await page.screenshot({ path: "tests/screenshots/file-mode.png", fullPage: true });
  console.log("\n스크린샷: tests/screenshots/file-mode.png");

  await browser.close();
}

main().catch(console.error);
