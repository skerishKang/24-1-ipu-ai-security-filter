const assert = require("node:assert/strict");
const http = require("node:http");
const { spawn } = require("node:child_process");
const path = require("node:path");
const { chromium } = require("playwright");

const FRONTEND_DIR = "G:\\Ddrive\\BatangD\\task\\workdiary\\24-1-ipu-ai-firewall\\frontend";
const BASE_URL = "http://127.0.0.1:4241";
const SERVER_START_TIMEOUT_MS = 10000;

const fileUploadResponse = {
  session_id: "session-file-001",
  original_text: "아이피유테크 홍길동 이사 contact@ipu.co.kr",
  replaced_text: "[ORG_01] [PERSON_01] [EMAIL_01]",
  detections: [
    { type: "organization", label: "ORG", value: "아이피유테크" },
    { type: "person", label: "PERSON", value: "홍길동 이사" },
    { type: "email", label: "EMAIL", value: "contact@ipu.co.kr" },
  ],
  replacements: [
    { original: "아이피유테크", replaced: "[ORG_01]", type: "organization", reason: "mock" },
    { original: "홍길동 이사", replaced: "[PERSON_01]", type: "person", reason: "mock" },
    { original: "contact@ipu.co.kr", replaced: "[EMAIL_01]", type: "email", reason: "mock" },
  ],
  report: {
    total_detections: 3,
    risk_level: "moderate-risk",
    strategy: "strict_token",
    review_status: "review-required",
  },
  copy_ready_prompt: "External AI prompt",
};

const audioUploadResponse = {
  session_id: "session-audio-001",
  original_text: "아이피유테크 홍길동 이사가 contact@ipu.co.kr 로 연락합니다.",
  replaced_text: "아이피유테크 [PERSON_ALIAS_01]가 [EMAIL_ALIAS_01] 로 연락합니다.",
  detections: [
    { type: "PERSON", label: "홍길동 이사", start: 6, end: 12, score: 0.88, note: "mock" },
    { type: "EMAIL", label: "contact@ipu.co.kr", start: 15, end: 33, score: 0.88, note: "mock" },
  ],
  replacements: [
    { original: "홍길동 이사", replaced: "[PERSON_ALIAS_01]", type: "PERSON", reason: "mock" },
    { original: "contact@ipu.co.kr", replaced: "[EMAIL_ALIAS_01]", type: "EMAIL", reason: "mock" },
  ],
  report: {
    total_detections: 2,
    risk_level: "moderate-risk",
    strategy: "alias",
    review_status: "review-required",
  },
  copy_ready_prompt: "Audio prompt",
};

const restoreResponse = {
  session_id: "session-file-001",
  restored_text: "아이피유테크 홍길동 이사 contact@ipu.co.kr",
  restored: true,
};

const missingOcrToolResponse = {
  detail: "스캔형 PDF OCR을 위한 로컬 도구가 없습니다. tesseract 와 pdftoppm 설치 후 다시 시도해 주세요.",
};

async function main() {
  const server = await startStaticServer();
  const browser = await chromium.launch({ headless: true });

  try {
    await runTest(browser, "첫 로드에서 4영역과 fallback 상태를 표시한다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });

      await page.goto(BASE_URL);
      await switchToExpertMode(page);

      await expectVisible(page.getByRole("heading", { name: "보안 치환 워크벤치" }));
      await expectVisible(page.getByRole("heading", { name: "1. 원문 입력" }));
      await expectVisible(page.getByRole("heading", { name: "2. 치환 결과" }));
      await expectVisible(page.getByRole("heading", { name: "3. 탐지 리포트" }));
      await expectVisible(page.getByRole("heading", { name: "4. 외부 AI용 복사 프롬프트" }));
      await expectTextIncludes(page.getByTestId("status-message"), "mock fallback");
      await expectTextIncludes(page.getByTestId("session-source"), "mock-fallback");
    });

    await runTest(browser, "바이너리 hwp 선택 시 변환 안내 메시지를 보여준다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });

      await page.goto(BASE_URL);
      await page.getByTestId("input-mode-file").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "sample.hwp",
        mimeType: "application/x-hwp",
        buffer: Buffer.from("fake"),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), ".hwp");
      await expectTextIncludes(page.getByTestId("status-message"), ".hwpx");
    });

    await runTest(browser, "빈 txt 파일 업로드 시 빈 파일 상태 메시지를 보여준다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });

      await page.goto(BASE_URL);
      await page.getByTestId("input-mode-file").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "empty.txt",
        mimeType: "text/plain",
        buffer: Buffer.from(""),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "내용이 있는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일");
    });

    await runTest(browser, "txt 파일 업로드 성공 시 결과 패널과 상태 메시지를 갱신한다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });
      await page.route("**/api/v1/mode/manual-preview/file", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(fileUploadResponse),
        });
      });

      await page.goto(BASE_URL);
      await switchToExpertMode(page);
      await page.getByTestId("input-mode-file").check();
      await page.getByTestId("policy-select").selectOption("strict_token");
      await page.getByTestId("file-input").setInputFiles({
        name: "sample.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("아이피유테크 홍길동 이사 contact@ipu.co.kr"),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "파일 업로드 결과");
      await expectTextIncludes(page.getByTestId("session-source"), "backend-file");
      await expectTextIncludes(page.getByTestId("replaced-text"), "[EMAIL_01]");
    });

    await runTest(browser, "전문가 모드에서 restore 버튼이 복원 결과를 보여준다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(fileUploadResponse),
        });
      });
      await page.route("**/api/v1/mode/manual-preview/restore", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(restoreResponse),
        });
      });

      await page.goto(BASE_URL);
      await switchToExpertMode(page);
      await page.getByTestId("text-input").fill("아이피유테크 홍길동 이사 contact@ipu.co.kr");
      await page.getByTestId("submit-preview").click();
      await page.getByTestId("restore-preview").click();

      await expectTextIncludes(page.getByTestId("restore-status"), "복원 테스트가 성공");
      await expectTextIncludes(page.getByTestId("restored-text"), "contact@ipu.co.kr");
    });

    await runTest(browser, "OCR 도구가 없는 스캔형 PDF 실패 시 안내 문구를 보여준다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });
      await page.route("**/api/v1/mode/manual-preview/file", async (route) => {
        await route.fulfill({
          status: 415,
          contentType: "application/json",
          body: JSON.stringify(missingOcrToolResponse),
        });
      });

      await page.goto(BASE_URL);
      await page.getByTestId("input-mode-file").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "scan.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("fake-scan"),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "tesseract");
      await expectTextIncludes(page.getByTestId("status-message"), "pdftoppm");
    });

    await runTest(browser, "전문가 모드에서 음성 업로드 성공 시 backend-audio 상태를 보여준다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });
      await page.route("**/api/v1/mode/manual-preview/audio", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(audioUploadResponse),
        });
      });

      await page.goto(BASE_URL);
      await switchToExpertMode(page);
      await page.getByTestId("input-mode-audio").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "sample.wav",
        mimeType: "audio/wav",
        buffer: Buffer.from("fake-audio"),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "음성 업로드 결과");
      await expectTextIncludes(page.getByTestId("session-source"), "backend-audio");
      await expectTextIncludes(page.getByTestId("replaced-text"), "[EMAIL_ALIAS_01]");
    });

    await runTest(browser, "일반인 모드에서도 음성 업로드를 선택할 수 있다", async (page) => {
      await page.route("**/api/v1/mode/manual-preview", async (route) => {
        await route.abort();
      });
      await page.route("**/api/v1/mode/manual-preview/audio", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(audioUploadResponse),
        });
      });

      await page.goto(BASE_URL);
      await expectVisible(page.getByTestId("input-mode-audio"));
      await page.getByTestId("input-mode-audio").check();
      await page.getByTestId("file-input").setInputFiles({
        name: "sample.wav",
        mimeType: "audio/wav",
        buffer: Buffer.from("fake-audio"),
      });
      await page.getByTestId("submit-preview").click();

      await expectTextIncludes(page.getByTestId("status-message"), "음성 전사 결과");
      await expectTextIncludes(page.getByTestId("simple-replaced-text"), "[EMAIL_ALIAS_01]");
    });

    console.log("\nAll frontend smoke tests passed.");
  } finally {
    await browser.close();
    await stopStaticServer(server);
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

async function expectVisible(locator) {
  await locator.waitFor({ state: "visible" });
  assert.equal(await locator.isVisible(), true);
}

async function expectTextIncludes(locator, expectedText) {
  await locator.waitFor({ state: "visible" });
  await waitFor(async () => {
    const text = (await locator.textContent()) || "";
    assert.match(text, new RegExp(escapeRegExp(expectedText), "i"));
  });
}

async function switchToExpertMode(page) {
  await page.getByRole("button", { name: "전문가 모드" }).click();
  await page.getByTestId("session-source").waitFor({ state: "visible" });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function startStaticServer() {
  if (await isServerReady(BASE_URL)) {
    return null;
  }

  const server = spawn("python", ["-m", "http.server", "4241", "--directory", FRONTEND_DIR], {
    cwd: FRONTEND_DIR,
    stdio: "ignore",
  });

  await waitFor(async () => {
    assert.equal(await isServerReady(BASE_URL), true);
  }, SERVER_START_TIMEOUT_MS);

  return server;
}

async function stopStaticServer(server) {
  if (!server) {
    return;
  }

  server.kill("SIGTERM");
  await new Promise((resolve) => {
    server.once("exit", () => resolve());
    setTimeout(resolve, 1000);
  });
}

async function isServerReady(url) {
  return new Promise((resolve) => {
    const request = http.get(url, (response) => {
      response.resume();
      resolve(response.statusCode >= 200 && response.statusCode < 500);
    });
    request.on("error", () => resolve(false));
  });
}

async function waitFor(assertion, timeoutMs = 5000) {
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

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
