/** Pure observation model: no page state, storage, requests, or timing scores. */

export const SAMPLES = Object.freeze({
  prose: "A letra tem ritmo, altura e proporção.\nO antigo tipiti fica perto da estrada.\nA leitura acompanha o trilho da memória.\n\nRead the little list from the runtime.\nA quiet title introduces the next chapter.\nNotice t, r, f, l, 1 and i in these words.",
  code: "function filter(items) {\n\tconst title = 'little list';\n\tif (item != nil && item.length >= 1) {\n\t\treturn items.filter(valid);\n\t}\n}\n\n// t r f l 1 i · -> => != === <= >=\nconst mínimo = 'ação e memória';",
  accents: "mi\u0303\u0301  mĩ́  mi\u0302\u0301  ml\u0323\n\nA leitura tem ritmo, ação e memória.\nFigueiredo · ñande · ñe’ẽ · yandï'pawa\nĽ ľ ď ť  ĵ Ĵ  ǘ Ǘ  İ ı\n\n1 l I i j  t r f  0 O o  rn m",
  columns: "1234567890123456789012345678901234567890\n| item       | count | title          |\n| tipiti     |     1 | little list    |\n| antigo     |    12 | filter runtime |\n| Estrada    |   123 | leitura        |\n\nTabs:\nitem\tcount\ttitle\nlist\t1\tlittle\n\nNerd Fonts faces: \ue0b0 \ue0b2 \ue0a0 \uf120",
});

/** @param {() => number} random @returns {[number, number]} */
export function spacingOrder(random) {
  return random() < 0.5 ? [0, 1] : [1, 0];
}

/** @typedef {{file:string,label:string,sha256:string,version:string,group?:string,pair?:string}} ObservedFont */
/** @typedef {{font:ObservedFont,features:{calt:number,liga:number,ss11:number}}} ReadingCondition */
/** @typedef {{font:ObservedFont,size:number,ground:string,text:string,preference:string,notes:string,order:number[],revealed:boolean,comparison:number,timestamp:string,mode?:string,choices?:ReadingCondition[]}} ObservationInput */

/** @param {ObservedFont} font @param {number} ss11 @returns {ReadingCondition} */
function condition(font, ss11) {
  return { font: { ...font }, features: { calt:1, liga:1, ss11 } };
}

/** @param {string} mode @param {string} drawing @param {number} spacing @param {ObservedFont} baseline @param {ObservedFont|undefined} candidate @returns {[ReadingCondition,ReadingCondition]} */
export function comparisonChoices(mode, drawing, spacing, baseline, candidate) {
  if (mode === "letterforms") {
    if (!candidate || ![0,1].includes(spacing)) throw new Error("Letterforms require paired fonts and a shared SS11 state.");
    return [condition(baseline, spacing), condition(candidate, spacing)];
  }
  if (mode !== "spacing" || !["baseline","candidate"].includes(drawing)) throw new Error("Expected spacing or letterforms with a known drawing version.");
  const font = drawing === "candidate" ? candidate : baseline;
  if (!font) throw new Error("Candidate drawing file unavailable.");
  return [condition(font, 0), condition(font, 1)];
}

/** @param {ReadingCondition[]} choices @param {string} mode */
function validateChoices(choices, mode) {
  if (choices.length !== 2) throw new Error("Expected two reading conditions.");
  if (choices.some(item => Object.values(item.features).some(value => ![0,1].includes(value)))) throw new Error("Expected binary feature states.");
  const [first, second] = choices;
  if (first.features.calt !== second.features.calt || first.features.liga !== second.features.liga) throw new Error("Expected matching calt and liga states.");
  if (mode === "spacing" && (first.font.sha256 !== second.font.sha256 || first.features.ss11 === second.features.ss11)) throw new Error("Spacing comparison requires the same font and opposite SS11 states.");
  if (mode === "letterforms" && first.features.ss11 !== second.features.ss11) throw new Error("Letterform comparison requires the same SS11 state.");
  if (!["spacing","letterforms"].includes(mode)) throw new Error("Expected spacing or letterforms mode.");
}

/** @param {ObservationInput} input */
export function readingObservation(input) {
  if (!["A", "B", "same", "unsure"].includes(input.preference)) throw new Error("Choose A, B, no preference, or unsure.");
  if (![12, 15, 20, 24].includes(input.size)) throw new Error("Expected a reading size of 12, 15, 20, or 24 px.");
  if (!["light", "dark"].includes(input.ground)) throw new Error("Expected a light or dark ground.");
  if (input.order.length !== 2 || [...input.order].sort().join() !== "0,1") throw new Error("Expected two distinct A/B condition indices.");
  const mode = input.mode ?? "spacing";
  const choices = input.choices ?? comparisonChoices("spacing", "baseline", 0, input.font, undefined);
  validateChoices(choices, mode);
  const [first, second] = input.order.map(index => choices[index]);
  return {
    timestamp: input.timestamp, comparison: input.comparison,
    face: input.font.label, mode, size_px: input.size, ground: input.ground,
    text: input.text, preference: input.preference, notes: input.notes,
    conditions: { A: conditionSnapshot(first), B: conditionSnapshot(second) },
    revealed_before_rating: input.revealed,
  };
}

/** @param {ReadingCondition} selected @returns {ReadingCondition} */
function conditionSnapshot(selected) {
  return { font: { ...selected.font }, features: { ...selected.features } };
}

/** @param {ReturnType<typeof readingObservation>[]} observations */
export function observationExport(observations) {
  return JSON.stringify({
    schema: "talha-reading-review/v2",
    purpose: "Personal clarity and preference observations; not a reading-speed study.",
    observations,
  }, null, 2) + "\n";
}
