import { strict as assert } from "node:assert/strict";
import { highlightText, escapeHtml } from "../src/utils/resultRendering.js";

function createDom() {
  const document = {
    createElement(tagName) {
      return new FakeElement(tagName);
    },
    createTextNode(value) {
      return new FakeElement("#text", value);
    },
  };

  return { document };
}

class FakeElement {
  constructor(tagName, value = "") {
    this.tagName = String(tagName).toUpperCase();
    this.className = "";
    this.textContent = value;
    this.children = [];
    this.parentNode = null;
    this.queryText = value;
  }

  append(...nodes) {
    for (const node of nodes) {
      node.parentNode = this;
      this.children.push(node);
      if (node.textContent) {
        this.queryText += node.textContent;
      } else if (node.children) {
        this.queryText += node.children.map((child) => child.textContent || child.queryText || "").join("");
      }
    }
  }

  querySelector(selector) {
    if (selector === "script") {
      return this.children.some((child) => child.tagName === "SCRIPT") ? new FakeElement("script") : null;
    }
    if (selector === "mark") {
      return this.children.find((child) => child.tagName === "MARK") ?? null;
    }
    return null;
  }
}

let passed = 0;
let failed = 0;

globalThis.describe = (name, fn) => {
  const tests = [];
  globalThis.it = (testName, testFn) => tests.push({ name: testName, fn: testFn });
  fn();
  for (const t of tests) {
    try {
      t.fn();
      console.log(`✓ ${t.name}`);
      passed++;
    } catch (e) {
      console.log(`✗ ${t.name}`);
      console.error(`  ${e.message}`);
      failed++;
    }
  }
};

globalThis.it = () => {};

function withDom(fn) {
  const { document } = createDom();
  const originalDocument = globalThis.document;
  globalThis.document = document;
  try {
    return fn();
  } finally {
    globalThis.document = originalDocument;
  }
}

describe("highlightText", () => {
  it("wraps exact match in mark", () => {
    withDom(() => {
      const result = highlightText("hello world", ["world"], "hl");
      assert.equal(result.tagName, "SPAN");
      const mark = result.querySelector("mark");
      assert.ok(mark, "should contain a mark element");
      assert.equal(mark.textContent, "world");
      assert.equal(result.queryText, "hello world");
    });
  });

  it("does not create script elements from XSS payloads", () => {
    withDom(() => {
      const result = highlightText('<img src=x onerror=alert(1)>', ["x"], "hl");
      assert.equal(result.querySelector("script"), null);
      assert.equal(result.tagName, "SPAN");
    });
  });

  it("handles case-insensitive matching", () => {
    withDom(() => {
      const result = highlightText("Contact CONTACT contact", ["contact"], "hl");
      const marks = result.children.filter((c) => c.tagName === "MARK");
      assert.equal(marks.length, 3);
      assert.equal(marks[0].textContent, "Contact");
      assert.equal(marks[1].textContent, "CONTACT");
      assert.equal(marks[2].textContent, "contact");
    });
  });

  it("prioritizes longer matches when overlapping", () => {
    withDom(() => {
      const result = highlightText("abcdef", ["abc", "abcdef"], "hl");
      const marks = result.children.filter((c) => c.tagName === "MARK");
      assert.equal(marks.length, 1);
      assert.equal(marks[0].textContent, "abcdef");
    });
  });

  it("handles empty string", () => {
    withDom(() => {
      const result = highlightText("", ["x"], "hl");
      assert.equal(result.tagName, "SPAN");
      assert.equal(result.queryText, "");
      assert.equal(result.children.length, 0);
    });
  });

  it("handles no matches", () => {
    withDom(() => {
      const result = highlightText("hello world", ["xyz"], "hl");
      assert.equal(result.querySelector("mark"), null);
      assert.equal(result.queryText, "hello world");
    });
  });

  it("handles null text", () => {
    withDom(() => {
      const result = highlightText(null, ["x"], "hl");
      assert.equal(result.tagName, "SPAN");
      assert.equal(result.queryText, "");
    });
  });

  it("handles Korean text", () => {
    withDom(() => {
      const result = highlightText("아이피유테크 홍길동", ["홍길동"], "hl");
      const mark = result.querySelector("mark");
      assert.ok(mark);
      assert.equal(mark.textContent, "홍길동");
      assert.equal(result.queryText, "아이피유테크 홍길동");
    });
  });

  it("handles emoji", () => {
    withDom(() => {
      const result = highlightText("hello 🎉 world", ["🎉"], "hl");
      const mark = result.querySelector("mark");
      assert.ok(mark);
      assert.equal(mark.textContent, "🎉");
    });
  });

  it("produces clean textContent without HTML tags", () => {
    withDom(() => {
      const result = highlightText("<script>alert(1)</script>", ["script"], "hl");
      assert.equal(result.querySelector("script"), null);
    });
  });
});

describe("escapeHtml", () => {
  it("escapes special chars", () => {
    assert.equal(escapeHtml("<img src=x>"), "&lt;img src=x&gt;");
    assert.equal(escapeHtml('"quote&'), "&quot;quote&amp;");
  });

  it("handles empty string", () => {
    assert.equal(escapeHtml(""), "");
  });
});

if (failed > 0) {
  console.error(`\n${failed} test(s) failed.`);
  process.exit(1);
} else {
  console.log(`\nAll ${passed} test(s) passed.`);
}
