// Automated UI test (SDD 11): full loop at 390x844 in headless Chromium against dist/.
// Also: axe-core scan of every screen in light and dark, text at 200%, no network
// requests outside the app, and the Pyodide performance measurement.
// Run with `make ui` (needs `npm install` and Playwright; see AGENTS.md).

import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const AXE = path.join(ROOT, "node_modules/axe-core/axe.min.js");
const PORT = 8765;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const failures = [];
const report = { viewport: "390x844", screens_scanned: 0, axe_violations: {}, overflow_at_200: [],
  external_requests: [], console_errors: [], turns_played: 0 };

function check(condition, message) {
  if (!condition) failures.push(message);
}

async function scan(page, screen) {
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => { document.documentElement.dataset.theme = value; }, theme);
    const result = await page.evaluate(() => window.axe.run(document, {
      runOnly: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] }));
    report.screens_scanned += 1;
    for (const violation of result.violations) {
      const key = `${screen}/${theme}/${violation.id}`;
      report.axe_violations[key] = violation.nodes.length;
      failures.push(`axe ${key}: ${violation.help} (${violation.nodes[0].html.slice(0, 120)})`);
    }
  }
}

async function checkTextScale(page, screen, mustSee) {
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  const overflow = await page.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  if (overflow > 1) {
    report.overflow_at_200.push(`${screen}: ${overflow}px`);
    failures.push(`horizontal overflow of ${overflow}px on ${screen} at 200% text`);
  }
  if (mustSee) {
    await page.locator(mustSee).scrollIntoViewIfNeeded();
    check(await page.locator(mustSee).isVisible(), `${mustSee} not visible at 200% on ${screen}`);
  }
  await page.evaluate(() => { document.documentElement.style.fontSize = ""; });
}

async function playLoop(page) {
  await page.goto(`${ORIGIN}/index.html`);
  await page.addScriptTag({ path: AXE });
  await page.waitForSelector("#start");
  await scan(page, "home");
  await checkTextScale(page, "home", "#start");
  await page.fill("#seed", "ui-test");
  const began = Date.now();
  await page.click("#start");
  await page.waitForSelector("#go-turn", { timeout: 120000 });
  report.engine_ready_ms = Date.now() - began;
  await scan(page, "briefing");
  await checkTextScale(page, "briefing", "#go-turn");
  for (let turn = 0; turn < 6; turn += 1) {
    await page.click("nav button[data-screen=turn]");
    await page.waitForSelector("#play-turn");
    check(await page.locator("article.card").count() === 5, `turn ${turn}: expected 5 cards`);
    if (turn === 0) {
      await scan(page, "turn");
      await checkTextScale(page, "turn", "#play-turn");
    }
    // Prefer a "meddle" card: they always leave visible consequences to explain.
    const meddle = page.locator("article.card.meddle input[type=checkbox]");
    const pick = (await meddle.count()) > 0 ? meddle.first()
      : page.locator("article.card input[type=checkbox]").first();
    await pick.check();
    await page.click("#play-turn");
    await page.waitForSelector("#feed-next", { timeout: 60000 });
    report.turns_played += 1;
    if (turn === 0) {
      await scan(page, "feed");
      await checkTextScale(page, "feed", "#feed-next");
    }
  }
  check(await page.locator("ul.feed li").count() > 6, "feed should list events");
  await page.locator("button[data-why]").first().click();
  await page.waitForSelector("#chain-tree details, #chain-tree p");
  await scan(page, "chain");
  await checkTextScale(page, "chain", "#chain-back");
  await page.click("#chain-back");
  await page.click("#feed-next");
  await page.waitForSelector("#health-score", { timeout: 120000 });
  check(await page.locator("table tbody tr").count() === 8, "results table should have 8 rows");
  check(/^-?\d/.test(await page.textContent("#health-score")), "health score should be a number");
  check(await page.locator("ol.chain").count() >= 1, "results should show a cause chain");
  check(await page.locator(".concept").count() >= 1, "a chain should carry a concept card");
  check(!(await page.textContent("body")).includes("[object"), "raw object text in the page");
  await scan(page, "results");
  await checkTextScale(page, "results", "#export");
  const download = page.waitForEvent("download");
  await page.click("#export");
  const file = await download;
  check(file.suggestedFilename() === "outbreak-ripple-ui-test.json", "export file name");
  report.results_ms = await page.evaluate(() => window.outbreakRipple.timings.get_diff);
}

async function measurePerformance(page) {
  const times = [];
  let digest = "";
  for (let i = 0; i < 5; i += 1) {
    const result = await page.evaluate(
      () => window.outbreakRipple.call("benchmark", { seed: "golden-1" }));
    digest = result.digest;
    times.push(await page.evaluate(() => window.outbreakRipple.timings.benchmark));
  }
  times.sort((a, b) => a - b);
  const native = execFileSync("python3", ["-c",
    "from tools.experiments import load_content\nfrom engine.runner import run\n"
    + "print(run(load_content(), 'golden-1', []).log.digest())"], { cwd: ROOT }).toString().trim();
  const performance = {
    what: "one 52-tick baseline run inside Pyodide (seed golden-1), 5 repeats",
    median_ms: Math.round(times[2]), min_ms: Math.round(times[0]), max_ms: Math.round(times[4]),
    budget_ms: 2000, engine_ready_ms: report.engine_ready_ms, results_screen_ms:
      Math.round(report.results_ms),
    environment: `headless Chromium (Playwright) on ${os.cpus()[0].model}, ${os.cpus().length}`
      + ` cores, ${os.platform()} ${os.arch()}; not a phone`,
    same_log_as_native_python: digest === native,
  };
  check(performance.median_ms < 2000, `52-tick run took ${performance.median_ms} ms in Pyodide`);
  return performance;
}

const server = spawn("python3", ["-m", "tools.serve", String(PORT)], { cwd: ROOT });
await new Promise((resolve) => server.stdout.once("data", resolve));
const browser = await chromium.launch();
let performance = {};
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 },
    acceptDownloads: true });
  const page = await context.newPage();
  page.on("request", (request) => {
    if (!request.url().startsWith(ORIGIN) && !request.url().startsWith("blob:")) {
      report.external_requests.push(request.url());
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") report.console_errors.push(message.text());
  });
  page.on("pageerror", (error) => report.console_errors.push(String(error)));
  await playLoop(page);
  performance = await measurePerformance(page);
  check(report.turns_played === 6, "six turns should be played");
  check(report.external_requests.length === 0, `network requests: ${report.external_requests}`);
  check(report.console_errors.length === 0, `console errors: ${report.console_errors}`);
} catch (error) {
  failures.push(`test crashed: ${error.stack}`);
} finally {
  await browser.close();
  server.kill();
}
report.failures = failures;
mkdirSync(path.join(ROOT, "reports"), { recursive: true });
writeFileSync(path.join(ROOT, "reports/ui.json"), `${JSON.stringify(report, null, 2)}\n`);
writeFileSync(path.join(ROOT, "reports/performance.json"),
  `${JSON.stringify(performance, null, 2)}\n`);
console.log(JSON.stringify({ ...report, performance }, null, 2));
process.exit(failures.length === 0 ? 0 : 1);
