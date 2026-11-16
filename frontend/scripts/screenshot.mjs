/**
 * Captures README screenshots from a running app.
 *
 *   node scripts/screenshot.mjs
 *
 * Expects the backend on :8000 and `npm run start` on :3000.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const project = path.resolve(here, "..");
const out = path.resolve(project, "..", "docs", "screenshots");
const sample = path.resolve(project, "..", "samples", "sample-po.pdf");

fs.mkdirSync(out, { recursive: true });

// Reuse the locally installed Chrome/Edge instead of downloading a browser.
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL ?? "chrome" });
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
  colorScheme: "dark",
});

const shot = async (name) => {
  await page.screenshot({ path: path.join(out, name) });
  console.log(`saved ${name}`);
};

await page.goto("http://127.0.0.1:3000", { waitUntil: "networkidle" });
await page.waitForTimeout(600);
await shot("01-upload.png");

await page.setInputFiles('input[type="file"]', sample);
await page.waitForSelector("textarea", { timeout: 30000 });
await page.waitForTimeout(900);
await shot("02-ready.png");

await page.fill("textarea", "When must the delivery arrive, and what is the penalty for lateness?");
await page.keyboard.press("Enter");

// Wait until the streamed answer stops growing.
let previous = "";
for (let attempt = 0; attempt < 60; attempt += 1) {
  await page.waitForTimeout(400);
  const current = await page.evaluate(() => document.body.innerText);
  if (current === previous && attempt > 3) break;
  previous = current;
}

await shot("03-answer.png");

const passages = page.getByRole("button", { name: /show passages/i });
if (await passages.count()) {
  await passages.first().click();
  await page.waitForTimeout(400);
  await shot("04-sources.png");
}

await browser.close();
console.log("done");
