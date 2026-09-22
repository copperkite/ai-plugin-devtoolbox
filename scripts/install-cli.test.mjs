import assert from "node:assert/strict";
import { test } from "node:test";
import { Writable } from "node:stream";
import {
  defaultsFromQuestions,
  parseAnswersJson,
  parseInstallArgv,
  runInstallCli,
  wantsInteractive,
  wantsJsonDump,
} from "./install-cli.mjs";

function collectStream() {
  let text = "";
  const stream = new Writable({
    write(chunk, _enc, callback) {
      text += String(chunk);
      callback();
    },
  });
  return {
    stream,
    text: () => text,
  };
}

test("parseAnswersJson accepts a bare object or an answers wrapper", () => {
  assert.deepEqual(parseAnswersJson('{"packageName":"x"}').value, { packageName: "x" });
  assert.deepEqual(parseAnswersJson('{"answers":{"packageName":"x"}}').value, { packageName: "x" });
  assert.match(parseAnswersJson("[").error, /Invalid --answers/);
});

test("defaultsFromQuestions skips questions with no default", () => {
  assert.deepEqual(
    defaultsFromQuestions([
      { id: "a", default: "one" },
      { id: "b" },
      { id: "c", default: ["git"] },
    ]),
    { a: "one", c: ["git"] },
  );
});

test("parseInstallArgv reads --project-dir and --yes", () => {
  const values = parseInstallArgv(["node", "cli.mjs", "--project-dir", "/tmp/app", "--yes"]);
  assert.equal(values["project-dir"], "/tmp/app");
  assert.equal(values.yes, true);
});

test("wantsInteractive is true for -i, false for --yes, and follows TTY otherwise", () => {
  assert.equal(wantsInteractive({ interactive: true }, { isTTY: false }), true);
  assert.equal(wantsInteractive({ yes: true }, { isTTY: true }), false);
  assert.equal(wantsInteractive({ propose: true }, { isTTY: true }), false);
  assert.equal(wantsInteractive({}, { isTTY: true }), true);
  assert.equal(wantsInteractive({}, { isTTY: false }), false);
});

test("wantsJsonDump is true only when --json is on the command line", () => {
  assert.equal(wantsJsonDump(["node", "cli.mjs", "--yes"]), false);
  assert.equal(wantsJsonDump(["node", "cli.mjs", "--yes", "--json"]), true);
});

test("--yes writes a status line before propose or apply", async () => {
  const stderr = collectStream();
  const stdout = collectStream();
  let applyCalled = false;
  const code = await runInstallCli({
    id: "test",
    propose: () => ({
      named: "empty",
      questions: [{ id: "packageName", default: "app" }],
      due: ["bootstrap"],
    }),
    apply: () => {
      applyCalled = true;
      assert.match(stderr.text(), /Installing /);
      return { ok: true, named: "ready" };
    },
    argv: ["node", "cli.mjs", "--project-dir", "/tmp/app", "--yes"],
    stdin: process.stdin,
    stdout: stdout.stream,
    stderr: stderr.stream,
  });
  assert.equal(code, 0);
  assert.equal(applyCalled, true);
  assert.match(stderr.text(), /^Installing \/tmp\/app…\n/);
});

test("-i shows a recap and skip apply when the operator answers n", async () => {
  const stdout = collectStream();
  const stderr = collectStream();
  let applyCalled = false;
  const queued = ["", "n"];
  const code = await runInstallCli({
    id: "test",
    propose: () => ({
      named: "empty",
      questions: [{ id: "packageName", type: "string", prompt: "npm package name", default: "app" }],
      due: ["bootstrap"],
    }),
    apply: () => {
      applyCalled = true;
      return { ok: true, named: "ready" };
    },
    argv: ["node", "cli.mjs", "--project-dir", "/tmp/app", "-i"],
    stdin: process.stdin,
    stdout: stdout.stream,
    stderr: stderr.stream,
    openReadline: () => ({
      question: async () => queued.shift() ?? "",
      close() {},
    }),
  });
  assert.equal(code, 0);
  assert.equal(applyCalled, false);
  assert.match(stdout.text(), /npm package name: app/);
  assert.match(stdout.text(), /Install cancelled/);
});

test("--yes loops: a second round asks with fresh defaults, then stops on an unanswerable question", async () => {
  const stdout = collectStream();
  const stderr = collectStream();
  const proposals = [
    { named: "needs-work-line", questions: [{ id: "provenance", default: "template" }] },
    { named: "existing", questions: [{ id: "adopt", type: "bool" }, { id: "repo", default: "me/x" }] },
    { named: "existing", questions: [{ id: "adopt", type: "bool" }, { id: "repo", default: "me/x" }] },
  ];
  const applies = [];
  const code = await runInstallCli({
    id: "test",
    propose: (_dir, answers) => {
      assert.ok(answers);
      return proposals.shift();
    },
    apply: (_dir, answers) => {
      applies.push({ ...answers });
      if (answers.adopt !== true) {
        return { ok: false, named: "needs-answers", missing: ["adopt"] };
      }
      return { ok: true, named: "ready" };
    },
    argv: ["node", "cli.mjs", "--project-dir", "/tmp/app", "--yes"],
    stdin: process.stdin,
    stdout: stdout.stream,
    stderr: stderr.stream,
  });
  assert.equal(code, 2);
  assert.equal(applies.length, 2, "apply ran once per round, then the same missing id stopped the loop");
  assert.deepEqual(applies[1], { provenance: "template", repo: "me/x" });
  assert.match(stdout.text(), /needs-answers/);
});

test("--yes reaches ready across two rounds when every question has a default", async () => {
  const stdout = collectStream();
  const proposals = [
    { named: "needs-work-line", questions: [{ id: "provenance", default: "template" }] },
    { named: "needs-conventions", questions: [{ id: "adopted", default: ["git"] }], effects: ["commit"] },
  ];
  let calls = 0;
  const code = await runInstallCli({
    id: "test",
    propose: () => proposals.shift(),
    apply: (_dir, answers) => {
      calls += 1;
      return answers.adopted ? { ok: true, named: "ready" } : { ok: false, named: "needs-answers", missing: ["adopted"] };
    },
    argv: ["node", "cli.mjs", "--project-dir", "/tmp/app", "--yes"],
    stdin: process.stdin,
    stdout: stdout.stream,
    stderr: collectStream().stream,
  });
  assert.equal(code, 0);
  assert.equal(calls, 2);
});

test("-i prints the effects in the recap", async () => {
  const stdout = collectStream();
  const queued = ["", "y"];
  await runInstallCli({
    id: "test",
    propose: () => ({
      named: "existing",
      questions: [{ id: "repo", type: "string", prompt: "GitHub repository", default: "me/x" }],
      effects: ["Create the private GitHub repository me/x"],
    }),
    apply: () => ({ ok: true, named: "ready", pendingPush: true, branch: "develop" }),
    argv: ["node", "cli.mjs", "--project-dir", "/tmp/app", "-i"],
    stdin: process.stdin,
    stdout: stdout.stream,
    stderr: collectStream().stream,
    openReadline: () => ({ question: async () => queued.shift() ?? "", close() {} }),
  });
  assert.match(stdout.text(), /What will happen:\n  - Create the private GitHub repository me\/x/);
  assert.match(stdout.text(), /Push develop yourself/);
});
