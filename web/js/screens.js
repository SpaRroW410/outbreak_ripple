// Home and Briefing screens.

import { h, percent, t } from "./dom.js";

function randomSeed() {
  const letters = "abcdefghjkmnpqrstuvwxyz23456789";
  const values = crypto.getRandomValues(new Uint8Array(6));
  return Array.from(values, (value) => letters[value % letters.length]).join("");
}

function todaySeed() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** Home: start a run from a seed. */
export function renderHome(app) {
  const input = h("input", { type: "text", id: "seed", value: randomSeed(), autocomplete: "off",
    autocapitalize: "none", spellcheck: "false", maxlength: "40" });
  const start = () => app.startGame(input.value.trim() || randomSeed()).catch(() => {});
  return h("section", { class: "stack" },
    h("h2", {}, t("home.heading")),
    h("p", {}, t("home.intro")),
    h("p", { class: "muted" }, t("app.tagline")),
    h("label", { for: "seed" }, t("home.seed_label")),
    input,
    h("button", { type: "button", class: "plain wide", id: "daily",
      onclick: () => { input.value = todaySeed(); } }, t("home.daily")),
    h("button", { type: "button", class: "wide", id: "start", onclick: start }, t("home.start")));
}

function tile(village) {
  const label = t("briefing.tile", {
    name: village.name, cases: village.reported_cases, coverage: percent(village.coverage),
    trust: percent(village.trust), outbreak: village.outbreak ? t("briefing.tile_outbreak") : "",
  });
  return h("li", { class: village.outbreak ? "tile outbreak" : "tile", "aria-label": label },
    h("strong", {}, village.name), h("br"),
    `${village.reported_cases} · ${percent(village.coverage)}% · ${percent(village.trust)}%`,
    village.outbreak ? h("span", { class: "flag" }, " !") : null);
}

function blockPanel(block) {
  const notes = [t("briefing.stock", { doses: block.vaccine_stock }),
    block.cold_chain_ok ? t("briefing.cold_ok") : t("briefing.cold_broken")];
  if (block.overloaded) notes.push(t("briefing.overloaded"));
  return h("section", { class: "block" },
    h("h3", {}, t("briefing.block", { name: block.name })),
    h("p", { class: "muted" }, notes.join(" · ")),
    h("ul", { class: "tiles" }, block.villages.map(tile)));
}

/** Briefing: district dashboard as a schematic tile grid. */
export function renderBriefing(app) {
  const state = app.state;
  const stat = (key, value) => h("li", {}, h("strong", {}, value), t(key));
  return h("section", { class: "stack" },
    h("h2", {}, t("briefing.heading", { district: state.district.name })),
    h("p", {}, t("briefing.week", { tick: state.tick, ticks: state.ticks,
      turn: Math.min(state.turn + 1, state.turns), turns: state.turns })),
    h("ul", { class: "stats" },
      stat("briefing.reported", state.totals.reported_cases),
      stat("briefing.deaths", state.totals.deaths),
      stat("briefing.coverage", `${percent(state.totals.coverage)}%`),
      stat("briefing.budget", state.budget)),
    h("p", { class: "muted" }, t("briefing.note")),
    h("button", { type: "button", class: "wide", id: "go-turn",
      onclick: () => app.show(state.finished ? "results" : "turn") },
    state.finished ? t("turn.see_results") : t("briefing.go_turn")),
    h("p", { class: "muted" }, t("briefing.legend")),
    state.district.blocks.map(blockPanel));
}
