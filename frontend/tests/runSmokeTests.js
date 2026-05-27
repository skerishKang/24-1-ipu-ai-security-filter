const assert = require("node:assert/strict");
const http = require("node:http");
const { spawn } = require("node:child_process");
const path = require("node:path");
const { chromium } = require("playwright");

const FRONTEND_DIR = path.resolve(__dirname, "..");
const BASE_URL = "http://127.0.0.1:4241";
const SERVER_START_TIMEOUT_MS = 10000;

const fileUploadResponse = {
  session_id: "session-file-001",
  restore_token: "restore-token-file-001",
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
  restore_token: "restore-token-audio-001",
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

      await expectVisible(page.getByRole("heading", { name: "문서 검토 콘솔" }));
      await expectVisible(page.getByRole("heading", { name: "1. 문서 입력" }));
      await expectVisible(page.getByRole("heading", { name: "2. 비식별 결과" }));
      await expectVisible(page.getByRole("heading", { name: "3. 정책 판정" }));
      await expectVisible(page.getByRole("heading", { name: "4. 외부 전달 보조" }));
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

      await expectTextIncludes(page.getByTestId("status-message"), "읽을 수 있는 내용이 있는 파일을 선택하세요.");
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

      await expectTextIncludes(page.getByTestId("restore-status"), "복원 테스트가 완료되었습니다.");
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

      await expectTextIncludes(page.getByTestId("status-message"), "스캔 PDF 처리를 위한 OCR 도구가 준비되지 않았습니다.");
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

      await expectTextIncludes(page.getByTestId("status-message"), "음성 기반 점검 결과를 보여주고 있습니다.");
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
    console.log(`✓ ${name}`);
  } finally {
    await page.close();
  }
}

async function startStaticServer() {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const requestUrl = new URL(req.url, BASE_URL);
      const pathname = requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname;
      const filePath = path.join(FRONTEND_DIR, pathname);
      if (!filePath.startsWith(FRONTEND_DIR)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }

      require("node:fs").readFile(filePath, (error, data) => {
        if (error) {
          res.writeHead(404);
          res.end("Not found");
          return;
        }
        const ext = path.extname(filePath);
        const contentType = ext === ".html" ? "text/html" : ext === ".js" ? "text/javascript" : "text/plain";
        res.writeHead(200, { "Content-Type": contentType });
        res.end(data);
      });
    });

    server.on("error", reject);
    server.listen(4241, "127.0.0.1", () => resolve(server));
    setTimeout(() => reject(new Error("Static server startup timed out")), SERVER_START_TIMEOUT_MS);
  });
}

async function stopStaticServer(server) {
  return new Promise((resolve) => server.close(resolve));
}

async function switchToExpertMode(page) {
  const expertModeButton = page.getByRole("button", { name: "전문가 모드" });
  if (await expertModeButton.isVisible()) {
    await expertModeButton.click();
  }
}

async function expectVisible(locator) {
  assert.equal(await locator.isVisible(), true);
}

async function expectTextIncludes(locator, expectedText) {
  const text = await locator.textContent();
  assert.ok(text && text.includes(expectedText), `Expected "${text}" to include "${expectedText}"`);
}
