import { SAMPLES, spacingOrder, comparisonChoices, readingObservation, observationExport } from "./review-model.mjs";

/** @typedef {import('./review-model.mjs').ObservedFont & {family:string,style:string,nf:boolean}} ReviewFont */
/** @param {string} id @returns {HTMLElement} */
function element(id) {
  const found = document.getElementById(id);
  if (!found) throw new Error(`Missing review control: ${id}`);
  return found;
}

const ui = {
  face: /** @type {HTMLSelectElement} */ (element("face")),
  mode: /** @type {HTMLSelectElement} */ (element("comparison-mode")),
  drawing: /** @type {HTMLSelectElement} */ (element("drawing")),
  fixed: /** @type {HTMLSelectElement} */ (element("fixed-spacing")),
  size: /** @type {HTMLSelectElement} */ (element("size")),
  ground: /** @type {HTMLSelectElement} */ (element("ground")),
  sample: /** @type {HTMLSelectElement} */ (element("sample")),
  a: /** @type {HTMLTextAreaElement} */ (element("text-a")),
  b: /** @type {HTMLTextAreaElement} */ (element("text-b")),
  notes: /** @type {HTMLTextAreaElement} */ (element("notes")),
  preference: /** @type {HTMLFieldSetElement} */ (element("preference")),
  save: /** @type {HTMLButtonElement} */ (element("save")),
  reveal: /** @type {HTMLButtonElement} */ (element("reveal")),
  export: /** @type {HTMLButtonElement} */ (element("export")),
  form: /** @type {HTMLFormElement} */ (element("observation")),
};

/** @type {ReviewFont[]} */ let fonts = [];
/** @type {ReviewFont[]} */ let baselineFaces = [];
/** @type {import('./review-model.mjs').ReadingCondition[]} */ let activeChoices = [];
/** @type {ReturnType<typeof readingObservation>[]} */ const observations = [];
/** @type {Map<string,Promise<FontFace>>} */ const loadedFaces = new Map();
const ratedComparisons = new Set();
let order = spacingOrder(Math.random), comparison = 1, revealed = false, loadSerial = 0;

/** @param {boolean} ready */
function setReady(ready) {
  ui.a.disabled = ui.b.disabled = ui.save.disabled = ui.preference.disabled = !ready;
}

/** @param {ArrayBuffer} buffer @returns {Promise<string>} */
async function fontDigest(buffer) {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

/** @param {ReviewFont} entry @param {number} index @returns {Promise<FontFace>} */
async function fetchReviewFace(entry, index) {
  const response = await fetch(entry.file);
  if (!response.ok) throw new Error(`Could not load ${entry.label}`);
  const buffer = await response.arrayBuffer();
  if (await fontDigest(buffer) !== entry.sha256) throw new Error("Font differs from the reviewed file; rebuild this reviewer.");
  const font = await new FontFace(`TalhaReview${index}`, buffer).load();
  document.fonts.add(font);
  return font;
}

/** @param {ReviewFont} entry @param {number} index @returns {Promise<FontFace>} */
function reviewFace(entry, index) {
  if (!loadedFaces.has(entry.file)) {
    loadedFaces.set(entry.file, fetchReviewFace(entry, index).catch(error => {
      loadedFaces.delete(entry.file);
      throw error;
    }));
  }
  return /** @type {Promise<FontFace>} */ (loadedFaces.get(entry.file));
}

/** @returns {Promise<void>} */
async function chooseFace() {
  const serial = ++loadSerial, entry = baselineFaces[Number(ui.face.value)];
  setReady(false);
  element("font-status").textContent = `Loading ${entry.label} samples…`;
  try {
    const choices = selectedChoices(entry);
    const assigned = order.map(index => choices[index]);
    const loaded = await Promise.all(assigned.map(item => reviewFace(/** @type {ReviewFont} */ (item.font), fonts.findIndex(font => font.file === item.font.file))));
    if (serial !== loadSerial) return;
    [ui.a, ui.b].forEach((sample, index) => { sample.style.fontFamily = loaded[index].family; });
    activeChoices = choices;
    applyReadingSettings();
    await document.fonts.ready;
    await new Promise(resolve => requestAnimationFrame(resolve));
    if (serial !== loadSerial) return;
    setReady(true);
    fontStatus(entry);
  } catch (error) {
    if (serial === loadSerial) element("font-status").textContent = `Font unavailable: ${error instanceof Error ? error.message : String(error)}`;
  }
}

/** @param {ReviewFont} baseline @returns {[import('./review-model.mjs').ReadingCondition,import('./review-model.mjs').ReadingCondition]} */
function selectedChoices(baseline) {
  const key = baseline.pair ?? baseline.file.split("/").at(-1);
  const candidate = fonts.find(font => font.group === "candidate" && font.pair === key);
  return comparisonChoices(ui.mode.value, ui.drawing.value, Number(ui.fixed.value), baseline, candidate);
}

/** @param {ReviewFont} entry */
function fontStatus(entry) {
  const iconNote = ui.sample.value === "columns" && !entry.nf ? " Choose an NF face for the icon row." : "";
  element("font-status").textContent = `${entry.label} — samples ready.${iconNote}`;
}

/** @returns {void} */
function applyReadingSettings() {
  document.body.classList.toggle("dark", ui.ground.value === "dark");
  [ui.a, ui.b].forEach((sample, index) => {
    sample.style.fontSize = `${ui.size.value}px`;
    const selected = activeChoices[order[index]];
    if (selected) sample.style.fontFeatureSettings = Object.entries(selected.features).map(([tag,value]) => `"${tag}" ${value}`).join(", ");
  });
  ["a", "b"].forEach((label, index) => {
    const selected = activeChoices[order[index]];
    const description = selected ? `${selected.font.group === "candidate" ? "Stem candidate" : "Baseline"} · SS11 ${selected.features.ss11 ? "on" : "off"}` : "";
    element(`assignment-${label}`).textContent = revealed ? description : "Assignment hidden";
  });
  comparisonSettings();
}

/** @returns {void} */
function comparisonSettings() {
  const paired = fonts.some(font => font.group === "candidate");
  if (!paired) { ui.mode.value = "spacing"; ui.drawing.value = "baseline"; }
  const stems = ui.mode.value === "letterforms";
  ui.mode.disabled = !paired;
  ui.drawing.disabled = stems || !paired;
  ui.fixed.disabled = !stems;
  element("comparison-note").textContent = stems ? `Letterforms: two drawing versions, both with SS11 ${ui.fixed.value === "1" ? "on" : "off"}.` : "Spacing: the same drawings with SS11 off/on.";
}

/** @returns {void} */
function chooseSample() {
  ui.a.value = ui.b.value = SAMPLES[/** @type {keyof typeof SAMPLES} */ (ui.sample.value)];
  const entry = baselineFaces[Number(ui.face.value)];
  if (entry && !ui.a.disabled) fontStatus(entry);
}

/** @returns {void} */
function newComparison() {
  comparison += 1;
  order = spacingOrder(Math.random);
  revealed = false;
  ui.reveal.disabled = true;
  ui.form.reset();
  chooseFace();
  element("saved-status").textContent = `New comparison. ${observations.length} saved observations kept.`;
}

/** @param {SubmitEvent} event */
function saveObservation(event) {
  event.preventDefault();
  const choice = /** @type {HTMLInputElement|null} */ (document.querySelector("input[name=preference]:checked"));
  if (!choice || ui.a.disabled) return;
  observations.push(readingObservation({
    font: baselineFaces[Number(ui.face.value)], size: Number(ui.size.value),
    ground: ui.ground.value, text: ui.a.value, preference: choice.value,
    notes: ui.notes.value, order, revealed, comparison, mode:ui.mode.value,
    choices:activeChoices, timestamp: new Date().toISOString(),
  }));
  ratedComparisons.add(comparison);
  ui.reveal.disabled = ui.export.disabled = false;
  ui.form.reset();
  renderJournal();
}

/** @returns {void} */
function renderJournal() {
  const body = element("journal");
  body.replaceChildren();
  for (const observation of observations) {
    const row = document.createElement("tr");
    for (const value of [observation.face, observation.mode, `${observation.size_px} px`, observation.ground, observation.preference, observation.revealed_before_rating ? "No" : "Yes"]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    body.append(row);
  }
  element("empty-journal").hidden = true;
  element("journal-table").hidden = false;
  element("saved-status").textContent = `${observations.length} observation${observations.length === 1 ? "" : "s"} saved in this page`;
}

/** @returns {void} */
function exportObservations() {
  const url = URL.createObjectURL(new Blob([observationExport(observations)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `talha-reading-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** @returns {void} */
function connectControls() {
  ui.face.addEventListener("change", chooseFace);
  ui.mode.addEventListener("change", newComparison);
  ui.drawing.addEventListener("change", chooseFace);
  ui.fixed.addEventListener("change", chooseFace);
  ui.size.addEventListener("change", applyReadingSettings);
  ui.ground.addEventListener("change", applyReadingSettings);
  ui.sample.addEventListener("change", () => { chooseSample(); chooseFace(); });
  ui.a.addEventListener("input", () => { ui.b.value = ui.a.value; });
  ui.b.addEventListener("input", () => { ui.a.value = ui.b.value; });
  ui.form.addEventListener("submit", saveObservation);
  element("new-comparison").addEventListener("click", newComparison);
  ui.export.addEventListener("click", exportObservations);
  ui.reveal.addEventListener("click", () => {
    if (ratedComparisons.has(comparison)) { revealed = true; applyReadingSettings(); }
  });
}

/** @returns {Promise<void>} */
async function startReview() {
  try {
    const response = await fetch("fonts.json");
    if (!response.ok) throw new Error("Candidate manifest unavailable.");
    fonts = await response.json();
    baselineFaces = fonts.filter(entry => entry.group !== "candidate");
    baselineFaces.forEach((entry, index) => { const option = new Option(entry.label, String(index)); ui.face.add(option); });
    const regular = baselineFaces.findIndex(entry => entry.file.endsWith("/TalhaMono-Regular.otf"));
    ui.face.value = String(regular < 0 ? 0 : regular);
    ui.face.disabled = false;
    connectControls();
    chooseSample();
    applyReadingSettings();
    await chooseFace();
  } catch (error) {
    element("font-status").textContent = "Reviewer unavailable. Start the local server described in README.txt, then reload.";
  }
}

await startReview();
