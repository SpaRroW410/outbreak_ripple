// Tiny DOM and text helpers shared by every screen. No game rules here.

let strings = {};

/** Install the string table (content/i18n/<lang>.json). */
export function setStrings(table) {
  strings = table;
}

/** Look up a string and fill {placeholders} from `vars`. */
export function t(key, vars = {}) {
  const template = strings[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (match, name) => (name in vars ? String(vars[name]) : match));
}

/** Create an element: h("p", {class: "muted"}, "text", childNode, ...). */
export function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (value === false || value === null || value === undefined) continue;
    if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
    else if (value === true) node.setAttribute(name, "");
    else node.setAttribute(name, String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

/** Sentence describing an event, from the event.<kind> string. */
export function eventText(event, cardNames = {}) {
  const vars = { place: event.place_name, ...event.payload };
  if (event.payload.card) vars.card = cardNames[event.payload.card] ?? event.payload.card;
  return t(`event.${event.kind}`, vars);
}

/** Percentage text from a 0..1 share. */
export function percent(share) {
  return Math.round(share * 100);
}
