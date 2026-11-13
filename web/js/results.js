// Results: scores, comparison with the no-action baseline, top cause chains and export.

import { eventText, h, percent, t } from "./dom.js";

function comparisonTable(results) {
  const rows = [
    ["results.cases", results.player.cases, results.baseline.cases],
    ["results.reported", results.player.reported_cases, results.baseline.reported_cases],
    ["results.deaths", results.player.deaths, results.baseline.deaths],
    ["results.coverage", `${percent(results.player.coverage)}%`,
      `${percent(results.baseline.coverage)}%`],
    ["results.gap", `${percent(results.player.coverage_gap)}%`,
      `${percent(results.baseline.coverage_gap)}%`],
    ["results.trust", `${percent(results.player.mean_trust)}%`,
      `${percent(results.baseline.mean_trust)}%`],
    ["results.outbreaks", results.player.outbreaks, results.baseline.outbreaks],
    ["results.stockouts", results.player.stockouts, results.baseline.stockouts],
  ];
  // The wrapper lets the table scroll sideways when text is very large.
  return h("div", { class: "scroll", tabindex: "0", role: "region",
    "aria-label": t("results.table_caption") }, h("table", {},
    h("caption", {}, t("results.table_caption")),
    h("thead", {}, h("tr", {}, h("th", { scope: "col" }, t("results.metric")),
      h("th", { scope: "col", class: "num" }, t("results.you")),
      h("th", { scope: "col", class: "num" }, t("results.baseline")))),
    h("tbody", {}, rows.map(([key, mine, base]) => h("tr", {},
      h("th", { scope: "row" }, t(key)), h("td", { class: "num" }, mine),
      h("td", { class: "num" }, base))))));
}

function kindList(titleKey, counts) {
  const kinds = Object.keys(counts);
  if (kinds.length === 0) return null;
  return h("div", {}, h("h3", {}, t(titleKey)),
    h("ul", {}, kinds.map((kind) => h("li", {},
      `${counts[kind]} × ${t(`event.${kind}`, { place: "…", cases: "…", deaths: "…",
        doses: "…", immune_percent: "…", villages: "…", card: "…" })}`))));
}

function chainPanel(app, chain, index) {
  const last = chain.events[chain.events.length - 1];
  const panel = h("section", { class: "block" },
    h("ol", { class: "chain" }, chain.events.map((event) => h("li", {},
      `${t("feed.week", { tick: event.tick })}: ${eventText(event, app.cardNames)}`))),
    h("button", { type: "button", class: "plain", "data-chain": index, onclick: () => {
      app.chainEventId = last.id;
      app.chainReturn = "results";
      app.show("chain");
    } }, t("chain.heading")));
  if (chain.concept) {
    app.conceptsViewed.add(chain.concept.id);
    panel.append(h("div", { class: "concept" },
      h("h3", {}, `${t("results.concept")}: ${chain.concept.title} `,
        h("span", { class: "tag" }, t(`results.badge.${chain.concept.badge}`))),
      h("p", {}, chain.concept.body),
      h("p", { class: "muted" }, t("results.competency", {
        topic: chain.concept.competency.working_topic }))));
  }
  return panel;
}

async function exportSession(app) {
  const data = await app.engine("export_session", {
    concepts_viewed: Array.from(app.conceptsViewed) });
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const link = h("a", { href: URL.createObjectURL(blob),
    download: `outbreak-ripple-${data.seed}.json` });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

function fill(app, section, results) {
  const health = results.health_score;
  const ripple = results.ripple_score;
  const parts = [
    h("ul", { class: "stats" },
      h("li", {}, h("strong", { class: health.total >= 0 ? "score good" : "score bad",
        id: "health-score" }, health.total), t("results.health")),
      h("li", {}, h("strong", { class: "score", id: "ripple-score" }, ripple.total),
        t("results.ripple"))),
    h("p", { class: "muted" }, t("results.parts", { deaths: health.deaths_part,
      cases: health.cases_part, coverage: health.coverage_part, equity: health.equity_part })),
    h("p", { class: "muted" }, `${t("results.ripple_detail", ripple)}. ${
      t("results.ripple_size", { count: results.ripple_size })}.`),
    comparisonTable(results),
    h("h3", {}, t("results.chains")),
    h("p", { class: "muted" }, t("results.chain_note")),
    results.chains.length === 0 ? h("p", {}, t("results.no_chains"))
      : results.chains.map((chain, index) => chainPanel(app, chain, index)),
    kindList("results.prevented", results.prevented),
    kindList("results.added", results.added),
    h("button", { type: "button", class: "wide", id: "export",
      onclick: () => exportSession(app).catch(() => {}) }, t("results.export")),
    h("button", { type: "button", class: "plain wide", id: "again",
      onclick: () => app.show("home") }, t("results.again"))];
  section.append(...parts.flat().filter((part) => part !== null));
}

/** Results screen; asks the engine for the baseline comparison on first view. */
export function renderResults(app) {
  const section = h("section", { class: "stack" }, h("h2", {}, t("results.heading")));
  if (!app.state.finished) {
    section.append(h("p", {}, t("results.not_ready")));
  } else if (app.results) {
    fill(app, section, app.results);
  } else {
    app.engine("get_diff", {}, "results.working").then((results) => {
      app.results = results;
      if (app.screen === "results") fill(app, section, results);
    }).catch(() => {});
  }
  return section;
}
