// Records a captioned video of the web UI, for demos from a cloud session
// (where you can't open the app in your own browser).
//
// 1. Start the app:   streamlit run app.py --server.headless true
// 2. Record:          node demo/record_demo.js
// 3. The video is saved in demo/output/ (git ignores it).
//
// It runs about 3 searches: roughly $0.08 in API costs (one fresh web search).
// Needs Node.js with Playwright (pre-installed in Claude Code cloud sessions).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const URL = 'http://localhost:8501';
const OUT = path.join(__dirname, 'output');
const pause = (page, seconds) => page.waitForTimeout(seconds * 1000);

// Shows a caption bar at the bottom of the video, so viewers know what is happening.
async function caption(page, text) {
  await page.evaluate((t) => {
    let bar = document.getElementById('demo-caption');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'demo-caption';
      // left:300px = start right of the sidebar, so the sidebar doesn't cover the text
      bar.style.cssText = 'position:fixed;left:300px;right:0;bottom:0;z-index:999999;padding:12px 24px;' +
        'background:rgba(17,24,39,.92);color:#fff;font:600 18px system-ui,sans-serif;text-align:center';
      document.body.appendChild(bar);
    }
    bar.textContent = t;
  }, text);
}

// Clicks an example button, then "Find cheapest flights", and waits for the answer.
async function runExample(page, button, waitFor) {
  await page.getByRole('button', { name: button }).click();
  await pause(page, 1);
  await page.getByRole('button', { name: 'Find cheapest flights' }).click();
  await page.getByText(waitFor).first().waitFor({ timeout: 150000 });
  await pause(page, 1);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: OUT, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();
  await page.goto(URL);
  await page.getByText('Cheapest Flight Finder').first().waitFor();

  // 1. The problem
  await caption(page, 'Problem: cheap fares hide bag fees. This agent finds the 3 cheapest flights + true total, with sources.');
  await pause(page, 6);

  // 2. Memory: save a preference
  await caption(page, 'Memory: I save my preference of 1 checked bag. The agent uses it on every search.');
  const bags = page.getByLabel('Checked bags');
  await bags.fill('1');
  await bags.press('Enter');
  await page.getByRole('button', { name: 'Save preferences' }).click();
  await pause(page, 4);

  // 3. A live search (fresh, about 30 seconds)
  await caption(page, 'Live run: understand the trip (Haiku) -> search the web (Sonnet) -> check every price -> add bag fees (RAG)...');
  await page.getByText('Use cache (30 min)').click();  // cache off: force a fresh search
  await runExample(page, 'LAX → New York', /Found flights|No reliable prices/);
  await caption(page, 'Results: fare + bag fee = true total. Every price links to its source; warnings say what to double-check.');
  await pause(page, 7);

  // 4. Observability: how the agent worked
  await page.getByText('How the agent worked').first().scrollIntoViewIfNeeded();
  await caption(page, 'Observability: every run is traced: steps, tool calls, model calls, tokens, time and cost.');
  await pause(page, 8);

  // 5. Cost: the same trip again comes from the cache
  await page.getByText('Cheapest Flight Finder').first().scrollIntoViewIfNeeded();
  await page.getByText('Use cache (30 min)').click();  // cache back on
  await caption(page, 'Cost: the same trip again is served from the cache...');
  await runExample(page, 'LAX → New York', 'Found flights');
  await page.getByText('How the agent worked').first().scrollIntoViewIfNeeded();
  await caption(page, 'Cache hit: about 1 second and $0.0002, instead of about 30 seconds and $0.07.');
  await pause(page, 7);

  // 6. Guardrails
  await page.getByText('Cheapest Flight Finder').first().scrollIntoViewIfNeeded();
  await caption(page, 'Guardrail: a date in the past is rejected before any web search.');
  await runExample(page, 'Past date', 'in the past');
  await pause(page, 5);
  await caption(page, 'Guardrail: booking or paying is refused before any AI call ($0).');
  await runExample(page, 'Booking request', "can't book or pay");
  await pause(page, 5);

  // 7. Past runs
  await page.getByRole('tab', { name: /Past runs/ }).click();
  await caption(page, 'Every run is saved as a trace file, so speed and cost can be compared over time.');
  await pause(page, 7);

  await caption(page, 'Next steps: a real flight-price API, flexible dates, price alerts. Thanks for watching!');
  await pause(page, 4);

  const video = page.video();
  await context.close();  // finishes writing the video file
  await browser.close();
  const file = path.join(OUT, 'demo.webm');
  fs.renameSync(await video.path(), file);
  console.log('Saved video:', file);
})();
