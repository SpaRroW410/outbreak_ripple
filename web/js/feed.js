// Feed (what happened) and the chain viewer (why it happened).

import { eventText, h, t } from "./dom.js";

function openChain(app, eventId, returnTo) {
  app.chainEventId = eventId;
  app.chainReturn = returnTo;
  app.show("chain");
}

/** Feed: visible events, newest turn first, each with a "Why?" button. */
export function renderFeed(app) {
  const section = h("section", { class: "stack" }, h("h2", {}, t("feed.heading")));
  if (app.feed.length === 0) {
    section.append(h("p", {}, t("feed.empty")));
    return section;
  }
  const list = h("ul", { class: "feed" });
  for (const event of app.feed.slice().reverse()) {
    list.append(h("li", { class: event.kind === "player.action" ? "mine" : null },
      h("span", { class: "muted" }, `${t("feed.week", { tick: event.tick })}: `),
      eventText(event, app.cardNames), " ",
      event.causes.length > 0
        ? h("button", { type: "button", class: "plain", "data-why": event.id,
          "aria-label": `${t("feed.why")} ${eventText(event, app.cardNames)}`,
          onclick: () => openChain(app, event.id, "feed") }, t("feed.why"))
        : null));
  }
  section.append(h("button", { type: "button", class: "wide", id: "feed-next",
    onclick: () => app.show(app.state.finished ? "results" : "briefing") },
  app.state.finished ? t("turn.see_results") : t("nav.briefing")), list);
  return section;
}

// One collapsible node; its causes are added the first time it is opened.
function causeNode(event, byId, cardNames, open) {
  const label = `${t("feed.week", { tick: event.tick })}: ${eventText(event, cardNames)}`;
  if (event.causes.length === 0) return h("p", {}, label);
  const details = h("details", { open });
  details.append(h("summary", {}, label));
  let filled = false;
  const fill = () => {
    if (filled || !details.open) return;
    filled = true;
    for (const causeId of event.causes) {
      const cause = byId.get(causeId);
      details.append(cause ? causeNode(cause, byId, cardNames, false)
        : h("p", {}, t("chain.no_cause")));
    }
    for (const influenceId of event.influences) {
      const influence = byId.get(influenceId);
      if (influence) {
        details.append(h("p", { class: "muted influence" },
          `${t("chain.influence")} ${eventText(influence, cardNames)}`));
      }
    }
  };
  details.addEventListener("toggle", fill);
  fill();
  return details;
}

/** Chain viewer: a collapsible tree of causes for one event. */
export function renderChain(app) {
  const section = h("section", { class: "stack" },
    h("h2", {}, t("chain.heading")),
    h("p", { class: "muted" }, t("chain.intro")),
    h("button", { type: "button", class: "plain", id: "chain-back",
      onclick: () => app.show(app.chainReturn) }, t("chain.back")));
  const tree = h("div", { id: "chain-tree" });
  section.append(tree);
  app.engine("get_chain", { event_id: app.chainEventId }).then((chain) => {
    const byId = new Map(chain.nodes.map((node) => [node.id, node]));
    tree.append(causeNode(byId.get(chain.event_id), byId, app.cardNames, true));
  }).catch(() => {});
  return section;
}
