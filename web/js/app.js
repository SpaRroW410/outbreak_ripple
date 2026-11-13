// App shell: holds UI state, switches screens, and wraps engine calls.
// Presentation only: every rule of the game lives in the Python engine.

import { call, timings } from "./bridge.js";
import { h, setStrings, t } from "./dom.js";
import { renderChain, renderFeed } from "./feed.js";
import { renderResults } from "./results.js";
import { renderBriefing, renderHome } from "./screens.js";
import { renderTurn } from "./turn.js";

const SCREENS = { home: renderHome, briefing: renderBriefing, turn: renderTurn, feed: renderFeed,
  chain: renderChain, results: renderResults };
const NAV = ["briefing", "turn", "feed", "results"];

const app = {
  state: null, // latest get_state / play_turn result from the engine
  feed: [], // all visible events so far
  results: null, // get_diff result, once the run is over
  cardNames: {}, // card id -> name, for event text
  chainEventId: null,
  chainReturn: "feed",
  conceptsViewed: new Set(),
  screen: "home",
  show,
  engine,
  startGame,
};

/** Switch to a screen and move focus to it. */
function show(screen) {
  app.screen = screen;
  document.getElementById("error").textContent = "";
  const main = document.getElementById("screen");
  main.replaceChildren(SCREENS[screen](app));
  renderNav();
  main.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function renderNav() {
  const nav = document.getElementById("nav");
  nav.hidden = app.state === null;
  nav.setAttribute("aria-label", t("nav.label"));
  nav.replaceChildren(...NAV.map((screen) => h("button", {
    type: "button", "data-screen": screen,
    "aria-current": app.screen === screen ? "page" : null,
    onclick: () => show(screen),
  }, t(`nav.${screen}`))));
}

/** Call the engine, showing a status line while waiting and any error it reports. */
async function engine(cmd, args = {}, statusKey = null) {
  const status = document.getElementById("status");
  const error = document.getElementById("error");
  error.textContent = "";
  if (statusKey) status.textContent = t(statusKey);
  try {
    return await call(cmd, args);
  } catch (problem) {
    error.textContent = problem.message;
    throw problem;
  } finally {
    status.textContent = "";
  }
}

async function startGame(seed) {
  app.state = await engine("new_game", { seed }, "app.loading");
  app.feed = [];
  app.results = null;
  app.conceptsViewed = new Set();
  show("briefing");
}

function setUpTheme() {
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  button.textContent = t("home.theme");
  button.addEventListener("click", () => {
    const dark = root.dataset.theme
      ? root.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
  });
}

async function main() {
  const [content, build] = await Promise.all([
    fetch("content.json").then((response) => response.json()),
    fetch("build.json").then((response) => response.json()),
  ]);
  setStrings(content.i18n.en);
  for (const card of content.cards) app.cardNames[card.id] = card.name;
  document.title = t("app.title");
  document.getElementById("app-title").textContent = t("app.title");
  document.getElementById("disclaimer").textContent = t("app.disclaimer");
  document.getElementById("version").textContent = t("home.version", {
    engine: build.engine_version, content: build.content_version });
  setUpTheme();
  show("home");
}

// Hook for the automated UI test (timings of engine calls). Not used by the app itself.
window.outbreakRipple = { call, timings, app };

main().catch((problem) => {
  document.getElementById("error").textContent = `${t("app.load_failed")} ${problem.message}`;
});
