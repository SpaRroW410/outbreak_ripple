// Bridge to the engine: the only place the UI talks to the Pyodide web worker.
// API commands are documented in docs/API.md.

const worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
const waiting = new Map();
let nextId = 1;

/** Milliseconds the engine took for the most recent command (for the performance test). */
export const timings = {};

worker.addEventListener("message", (message) => {
  const { id, reply, ms, cmd } = message.data;
  const pending = waiting.get(id);
  if (!pending) return;
  waiting.delete(id);
  timings[cmd] = ms;
  if (reply.ok) pending.resolve(reply.result);
  else pending.reject(new Error(reply.error));
});

worker.addEventListener("error", (event) => {
  for (const pending of waiting.values()) pending.reject(new Error(event.message));
  waiting.clear();
});

/** Send one command to the engine; resolves with its result or rejects with its error. */
export function call(cmd, args = {}) {
  return new Promise((resolve, reject) => {
    const id = nextId++;
    waiting.set(id, { resolve, reject });
    worker.postMessage({ id, request: { cmd, args } });
  });
}
