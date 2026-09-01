import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const BASE_URL = "http://127.0.0.1:4241";
const TEMPLATE_MODE_URL = `${BASE_URL}/frontend/template-mode.html`;
const SERVER_START_TIMEOUT_MS = 10000;
const EXPECTED_TEMPLATE_SMOKE_TEST_COUNT = 4;
let executedTemplateSmokeTestCount = 0;

async function main() {
  const server = await startStaticServer();
  const browser = await chromium.launch({ headless: true });

  try {
    await runTest(browser, "approved template catalog loads all selectable templates", async (page) => {
      await page.goto(TEMPLATE_MODE_URL);

      await expectVisible(page.getByRole("heading", { name: "템플릿 기반 입력 폼 실험" }));
      await expectVisible(page.getByRole("heading", { name: "1. 템플릿 입력 폼" }));
      await expectVisible(page.getByRole("heading", { name: "2. 문서 초안 미리보기" }));

      const selector = page.locator("[data-role='template-selector']");
      await expectVisible(selector);
      assert.equal(await selector.locator("option").count(), 3);
      await expectTextIncludes(page.locator("body"), "계약 검토 의뢰서 v1.1.0");
    });

    await runTest(browser, "sample values fill required fields and rebuild the draft", async (page) => {
      await page.goto(TEMPLATE_MODE_URL);

      await expectTextIncludes(page.locator("body"), "입력이 필요합니다");
      await page.getByRole("button", { name: "샘플 값 채우기" }).click();

      await expectTextIncludes(page.locator("body"), "초안이 모두 채워졌습니다.");
      await expectTextIncludes(page.locator(".template-preview__document-body"), "입력 필요", 500, false);
    });

    await runTest(browser, "switching templates resets stale values and renders the next schema", async (page) => {
      await page.goto(TEMPLATE_MODE_URL);

      await page.getByRole("button", { name: "샘플 값 채우기" }).click();
      await expectTextIncludes(page.locator("body"), "초안이 모두 채워졌습니다.");

      await page.locator("[data-role='template-selector']").selectOption("customer-inquiry-intake");

      await expectTextIncludes(page.locator("body"), "고객 문의 접수서 v1.1.0");
      await expectTextIncludes(page.locator("body"), "입력이 필요합니다");
      await expectTextIncludes(page.locator(".template-preview__document-body"), "계약 검토 의뢰서", 500, false);
    });

    await runTest(browser, "user template values are escaped in preview output", async (page) => {
      await page.goto(TEMPLATE_MODE_URL);
      await page.addScriptTag({ content: "window.__ipuTemplateSmokeXss = false;" });

      const attack = `<img src=x onerror=\"window.__ipuTemplateSmokeXss = true\"><script>window.__ipuTemplateSmokeXss = true</script>`;
      const textInput = page.locator(
        "textarea.template-form__textarea, input.template-form__input:not([type='date'])",
      ).first();
      await expectVisible(textInput);
      await textInput.fill(attack);

      await expectTextIncludes(page.locator(".template-preview__document-body"), "<img src=x");
      const executed = await page.evaluate(() => window.__ipuTemplateSmokeXss);
      assert.equal(executed, false);
      assert.equal(await page.locator(".template-preview__document-body img").count(), 0);
      assert.equal(await page.locator(".template-preview__document-body script").count(), 0);
    });

    assert.equal(
      executedTemplateSmokeTestCount,
      EXPECTED_TEMPLATE_SMOKE_TEST_COUNT,
      `Expected ${EXPECTED_TEMPLATE_SMOKE_TEST_COUNT} template smoke tests to run, got ${executedTemplateSmokeTestCount}.`,
    );
    console.log("\nAll template mode smoke tests passed.");
  } finally {
    await browser.close();
    await stopStaticServer(server);
  }
}

async function runTest(browser, name, testFn) {
  executedTemplateSmokeTestCount += 1;
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
      const pathname = requestUrl.pathname === "/" ? "/frontend/template-mode.html" : requestUrl.pathname;
      const filePath = path.join(PROJECT_ROOT, pathname);
      if (!filePath.startsWith(PROJECT_ROOT)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }

      fs.readFile(filePath, (error, data) => {
        if (error) {
          res.writeHead(404);
          res.end("Not found");
          return;
        }
        res.writeHead(200, { "Content-Type": contentTypeFor(filePath) });
        res.end(data);
      });
    });

    server.on("error", reject);
    server.listen(4241, "127.0.0.1", () => resolve(server));
    setTimeout(() => reject(new Error("Static server startup timed out")), SERVER_START_TIMEOUT_MS);
  });
}

function contentTypeFor(filePath) {
  switch (path.extname(filePath)) {
    case ".html":
      return "text/html";
    case ".js":
      return "text/javascript";
    case ".json":
      return "application/json";
    case ".css":
      return "text/css";
    default:
      return "text/plain";
  }
}

async function stopStaticServer(server) {
  return new Promise((resolve) => server.close(resolve));
}

async function expectVisible(locator) {
  assert.equal(await locator.isVisible(), true);
}

async function expectTextIncludes(locator, expectedText, timeoutMs = 2000, shouldInclude = true) {
  const start = Date.now();
  while (true) {
    const text = await locator.textContent();
    const includes = Boolean(text && text.includes(expectedText));
    if (includes === shouldInclude) {
      return;
    }
    if (Date.now() - start > timeoutMs) {
      assert.equal(includes, shouldInclude, `Expected "${text}" ${shouldInclude ? "to include" : "not to include"} "${expectedText}"`);
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
