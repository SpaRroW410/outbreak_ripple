// Turn screen: the hand of cards, target pickers and the "play turn" button.
// The engine checks the rules; this screen only shows its answer.

import { h, t } from "./dom.js";

function targetPicker(card, state) {
  const select = h("select", { id: `target-${card.id}`, "data-card": card.id });
  if (card.target_kind === "district") {
    select.append(h("option", { value: "D" }, state.district.name));
  } else if (card.target_kind === "block") {
    for (const block of state.district.blocks) {
      select.append(h("option", { value: block.id }, t("briefing.block", { name: block.name })));
    }
  } else {
    for (const block of state.district.blocks) {
      const group = h("optgroup", { label: t("briefing.block", { name: block.name }) });
      for (const village of block.villages) {
        const flag = village.outbreak ? " !" : "";
        group.append(h("option", { value: village.id },
          `${village.name} (${village.reported_cases})${flag}`));
      }
      select.append(group);
    }
  }
  return select;
}

function cardPanel(card, state, onChange) {
  const pick = h("input", { type: "checkbox", id: `pick-${card.id}`, "data-card": card.id,
    onchange: onChange });
  return h("article", { class: card.family === "meddle" ? "card meddle" : "card",
    "data-card": card.id },
  h("h3", {}, card.name),
  h("p", {}, h("span", { class: "tag" }, t(`turn.family.${card.family}`)), " ",
    h("span", { class: "muted" },
      t("turn.cost", { budget: card.budget_cost, points: card.action_points }))),
  h("p", {}, card.description),
  h("label", { for: `target-${card.id}` }, t("turn.target", { card: card.name })),
  targetPicker(card, state),
  h("label", { class: "pick", for: `pick-${card.id}` }, pick, t("turn.select")));
}

/** Turn: choose up to max_cards cards and play the turn. */
export function renderTurn(app) {
  const state = app.state;
  if (state.finished) {
    return h("section", { class: "stack" }, h("h2", {}, t("turn.over")),
      h("button", { type: "button", class: "wide", onclick: () => app.show("results") },
        t("turn.see_results")));
  }
  const play = h("button", { type: "button", class: "wide", id: "play-turn" });
  const section = h("section", { class: "stack" });
  const chosen = () => Array.from(section.querySelectorAll("input[type=checkbox]:checked"));
  const refresh = () => {
    for (const panel of section.querySelectorAll("article")) {
      panel.classList.toggle("chosen", panel.querySelector("input[type=checkbox]").checked);
    }
    play.textContent = t("turn.play", { count: chosen().length });
  };
  play.addEventListener("click", async () => {
    const plays = chosen().map((box) => ({ card_id: box.dataset.card,
      target: section.querySelector(`#target-${box.dataset.card}`).value }));
    play.disabled = true;
    try {
      app.state = await app.engine("play_turn", { plays }, "turn.working");
      app.feed = app.feed.concat(app.state.feed);
      app.show("feed");
    } catch {
      play.disabled = false; // the engine's message is shown in the error line
    }
  });
  section.append(
    h("h2", {}, t("turn.heading", { turn: state.turn + 1, turns: state.turns })),
    h("p", {}, t("turn.rules", { max: state.max_cards, budget: state.budget,
      points: state.action_points })),
    ...state.hand.map((card) => cardPanel(card, state, refresh)),
    play);
  refresh();
  return section;
}
