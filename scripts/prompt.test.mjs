import assert from "node:assert/strict";
import { test } from "node:test";
import {
  confirmInstall,
  formatSummaryLines,
  parseConfirm,
  promptQuestions,
  shouldAskQuestion,
} from "./prompt.mjs";

test("parseConfirm treats empty as yes and rejects other text", () => {
  assert.equal(parseConfirm(""), true);
  assert.equal(parseConfirm("Y"), true);
  assert.equal(parseConfirm("n"), false);
  assert.equal(parseConfirm("maybe"), null);
});

test("shouldAskQuestion honors askIf includes", () => {
  const question = { id: "documentation.shape", askIf: { id: "adopted", includes: "documentation" } };
  assert.equal(shouldAskQuestion(question, { adopted: ["git"] }), false);
  assert.equal(shouldAskQuestion(question, { adopted: ["documentation", "git"] }), true);
  assert.equal(shouldAskQuestion({ id: "packageName" }, {}), true);
});

test("shouldAskQuestion honors equals and lists of rules", () => {
  const one = { id: "cloneUrl", askIf: { id: "provenance", equals: "clone" } };
  assert.equal(shouldAskQuestion(one, { provenance: "clone" }), true);
  assert.equal(shouldAskQuestion(one, { provenance: "template" }), false);
  assert.equal(shouldAskQuestion(one, {}), false);
  const both = {
    id: "packageName",
    askIf: [
      { id: "provenance", equals: "template" },
      { id: "template", equals: "stack-ts-lib" },
    ],
  };
  assert.equal(shouldAskQuestion(both, { provenance: "template", template: "stack-ts-lib" }), true);
  assert.equal(shouldAskQuestion(both, { provenance: "template", template: "other" }), false);
});

test("formatSummaryLines lists only answered questions with their prompts", () => {
  const lines = formatSummaryLines(
    [
      { id: "packageName", prompt: "npm package name" },
      { id: "adopted", prompt: "Which conventions to record?" },
      { id: "skipped", prompt: "Skipped" },
    ],
    { packageName: "my-app", adopted: ["git", "testing"] },
  );
  assert.deepEqual(lines, [
    "  npm package name: my-app",
    "  Which conventions to record?: git, testing",
  ]);
});

test("promptQuestions keeps defaults on empty input then confirmInstall can refuse", async () => {
  const chunks = [];
  const stdout = { write: (chunk) => chunks.push(chunk) };
  const queued = ["", "n"];
  const readline = { question: async () => queued.shift() ?? "" };
  const questions = [{ id: "packageName", type: "string", prompt: "npm package name", default: "app" }];
  const answers = await promptQuestions(questions, { stdout, readline });
  assert.equal(answers.packageName, "app");
  const confirmed = await confirmInstall(questions, answers, { stdout, readline });
  assert.equal(confirmed, false);
  assert.match(chunks.join(""), /Enter keeps: app/);
  assert.match(chunks.join(""), /Your choices:/);
});
