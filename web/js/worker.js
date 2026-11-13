// Web worker: loads Pyodide and the Python engine, then answers JSON API requests.
// All files are fetched from this app's own folder; nothing is loaded from the network.

import { loadPyodide } from "../pyodide/pyodide.mjs";

const here = (path) => new URL(path, import.meta.url).href;

async function start() {
  const pyodide = await loadPyodide({ indexURL: here("../pyodide/") });
  const [engineZip, contentJson] = await Promise.all([
    fetch(here("../engine.zip")).then((response) => response.arrayBuffer()),
    fetch(here("../content.json")).then((response) => response.text()),
  ]);
  pyodide.unpackArchive(engineZip, "zip");
  pyodide.globals.set("content_json", contentJson);
  pyodide.runPython(
    "import json\nfrom engine.api import Session\nsession = Session(json.loads(content_json))",
  );
  return pyodide.globals.get("session");
}

const ready = start();

self.addEventListener("message", async (message) => {
  const { id, request } = message.data;
  let reply;
  let ms = 0;
  try {
    const session = await ready;
    const began = performance.now();
    reply = JSON.parse(session.handle_json(JSON.stringify(request)));
    ms = performance.now() - began;
  } catch (error) {
    reply = { ok: false, error: String(error) };
  }
  self.postMessage({ id, reply, ms, cmd: request.cmd });
});
