import test from "node:test";
import assert from "node:assert/strict";
import { SAMPLES, spacingOrder, comparisonChoices, readingObservation, observationExport } from "../tools/reading_ui/review-model.mjs";

function input() {
  return { font: { file:"fonts/TalhaMono-Regular.otf", label:"Talha Mono · Regular", sha256:"reviewed", version:"beta.6" },
    size:15, ground:"light", text:SAMPLES.prose, preference:"A", notes:"Clearer little", order:[1,0],
    revealed:false, comparison:1, timestamp:"2026-10-23T12:00:00Z" };
}

test("every randomized comparison has one ordinary and one SS11 sample", () => {
  assert.deepEqual(spacingOrder(() => 0), [0,1]);
  assert.deepEqual(spacingOrder(() => 0.99), [1,0]);
});

test("a saved observation freezes its assignment and exact font identity", () => {
  const value = input(), saved = readingObservation(value);
  value.order.reverse(); value.font.sha256 = "changed"; value.notes = "changed";
  assert.equal(saved.conditions.A.features.ss11, 1);
  assert.equal(saved.conditions.B.features.ss11, 0);
  assert.equal(saved.conditions.A.font.sha256, "reviewed");
  assert.equal(saved.notes, "Clearer little");
  assert.equal(saved.revealed_before_rating, false);
});

test("unblinded ratings remain explicitly identifiable", () => {
  assert.equal(readingObservation({ ...input(), revealed:true }).revealed_before_rating, true);
});

test("invalid ratings and mismatched feature assignments are rejected", () => {
  for (const override of [{preference:""},{size:0},{ground:"unknown"},{order:[0,0]},{order:[1,1]},{order:[0,1,0]}]) {
    assert.throws(() => readingObservation({ ...input(), ...override }));
  }
});

test("export preserves editable Unicode text without inventing a speed score", () => {
  const value = input(); value.text = "mi\u0303\u0301\t<script>\nml\u0323";
  const saved = readingObservation(value), report = JSON.parse(observationExport([saved]));
  assert.equal(report.schema, "talha-reading-review/v2");
  assert.equal(report.observations[0].text, value.text);
  assert.deepEqual(report.observations[0].conditions.A.features, {calt:1,liga:1,ss11:1});
  assert.equal("reading_speed" in report.observations[0], false);
});

test("spacing and letterform modes isolate the intended factor", () => {
  const baseline = input().font, candidate = {...baseline, file:"candidate.otf", sha256:"new"};
  const spacing = comparisonChoices("spacing", "candidate", 0, baseline, candidate);
  assert.deepEqual(spacing.map(item => item.font.sha256), ["new","new"]);
  assert.deepEqual(spacing.map(item => item.features.ss11), [0,1]);
  const drawings = comparisonChoices("letterforms", "baseline", 1, baseline, candidate);
  assert.deepEqual(drawings.map(item => item.font.sha256), ["reviewed","new"]);
  assert.deepEqual(drawings.map(item => item.features.ss11), [1,1]);
});

test("paired observations retain independent immutable font hashes and features", () => {
  const value = input(), candidate = {...value.font, file:"candidate.otf", sha256:"new"};
  value.mode = "letterforms";
  value.choices = comparisonChoices("letterforms", "baseline", 1, value.font, candidate);
  const saved = readingObservation(value);
  value.choices[1].font.sha256 = "changed"; value.choices[1].features.ss11 = 0;
  assert.equal(saved.conditions.A.font.sha256, "new");
  assert.equal(saved.conditions.B.font.sha256, "reviewed");
  assert.equal(saved.conditions.A.features.ss11, 1);
});

test("confounded comparisons and unavailable candidate versions are rejected", () => {
  const value = input(), candidate = {...value.font, sha256:"new"};
  const drawings = comparisonChoices("letterforms", "baseline", 0, value.font, candidate);
  assert.throws(() => readingObservation({...value, mode:"spacing", choices:drawings}));
  const spacing = comparisonChoices("spacing", "baseline", 0, value.font, candidate);
  assert.throws(() => readingObservation({...value, mode:"letterforms", choices:spacing}));
  assert.throws(() => comparisonChoices("letterforms", "baseline", 0, value.font, undefined));
  assert.throws(() => comparisonChoices("spacing", "candidate", 0, value.font, undefined));
});

test("samples exercise tabs, accents, ligatures, confusable letters and NF icons", () => {
  assert.ok(SAMPLES.code.includes("\t"));
  assert.ok(SAMPLES.code.includes("!="));
  assert.ok(SAMPLES.accents.includes("mi\u0303\u0301"));
  assert.ok(SAMPLES.accents.includes("1 l I i"));
  assert.ok(SAMPLES.columns.includes("\uf120"));
});
