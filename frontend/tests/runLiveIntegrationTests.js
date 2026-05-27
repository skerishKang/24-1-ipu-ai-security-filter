const assert = require("node:assert/strict");
const http = require("node:http");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { chromium } = require("playwright");

const BACKEND_URL = "http://127.0.0.1:8241";
const FRONTEND_URL = "http://127.0.0.1:4241";

async function main() {
  const browser = await chromium.launch({ headless: true });

  try {
    await runTest(browser, "전문가 모드 첫 로드 시 backend 연결 상태를 표시한다", async (page) => {
      await page.goto(FRONTEND_URL);
      await page.waitForLoadState("networkidle");
      await switchToExpertMode(page);
      await expectTextIncludes(page.getByTestId("session-source"), "backend");
    });

    await runTest(browser, "전문가 모드 텍스트 요청 후 session/source 에 backend 가 표시된다", async (page) => {
      await page.goto(FRONTEND_URL);
      await page.waitForLoadState("networkidle");
      await switchToExpertMode(page);
      await page.getByTestId("text-input").fill("아이피유테크 홍길동 contact@ipu.co.kr");
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "백엔드 응답");
      await expectTextIncludes(page.getByTestId("session-source"), "backend");
    });

    await runTest(browser, "전문가 모드 txt 파일 업로드 후 session/source 에 backend-file 이 표시된다", async (page) => {
      await page.goto(FRONTEND_URL);
      await page.waitForLoadState("networkidle");
      await switchToExpertMode(page);
      await page.getByTestId("input-mode-file").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "sample.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("아이피유테크 홍길동 contact@ipu.co.kr"),
      });
      await page.getByTestId("submit-preview").click();
      
      await expectTextIncludes(page.getByTestId("status-message"), "파일 업로드 결과");
      await expectTextIncludes(page.getByTestId("session-source"), "backend-file");
    });

    await runTest(browser, "전문가 모드에서 현재 치환본을 restore API로 복원할 수 있다", async (page) => {
      await page.goto(FRONTEND_URL);
      await page.waitForLoadState("networkidle");
      await switchToExpertMode(page);
      await page.getByTestId("text-input").fill("아이피유테크 홍길동 contact@ipu.co.kr");
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "백엔드 응답");
      await page.getByTestId("restore-preview").click();

      await expectTextIncludes(page.getByTestId("restore-status"), "복원 테스트가 완료");
      await expectTextIncludes(page.getByTestId("restored-text"), "아이피유테크");
      await expectTextIncludes(page.getByTestId("restored-text"), "contact@ipu.co.kr");
    });

    console.log("\nAll live integration tests passed.");
  } finally {
    await browser.close();
  }
}

async function runTest(browser, name, testFn) {
  const page = await browser.newPage();
  try {
    await testFn(page);
    console.log(`PASS ${name}`);
  } catch (error) {
    console.error(`FAIL ${name}`);
    throw error;
  } finally {
    await page.close();
  }
}

async function expectTextIncludes(locator, expectedText) {
  await locator.waitFor({ state: "visible" });
  await waitFor(async () => {
    const text = (await locator.textContent()) || "";
    assert.match(text, new RegExp(escapeRegExp(expectedText), "i"));
  });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function waitFor(assertion, timeoutMs = 10000) {
  const startedAt = Date.now();
  let lastError = null;

  while (Date.now() - startedAt < timeoutMs) {
    try {
      await assertion();
      return;
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }

  throw lastError || new Error("Timed out while waiting for condition.");
}

async function switchToExpertMode(page) {
  await page.getByRole("button", { name: "전문가 모드" }).click();
  await page.getByTestId("session-source").waitFor({ state: "visible" });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
