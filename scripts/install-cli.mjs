/**
 * Shared install client: interactive interview by default on a TTY; --yes /
 * --apply for scripts. Renders questions[] from propose, then calls apply. No
 * domain knowledge.
 *
 * Canonical copy: bluewombat-toolbox/installer/src (with prompt.mjs and both
 * test files). Each plugin that opts into the CLI carries a byte-identical
 * copy under src/scripts/, refreshed with `npm run sync-client -- <dir>` from
 * the installer. Edit here, then sync; never edit a copy.
 */
import { createInterface } from "node:readline/promises";
import { parseArgs } from "node:util";
import { resolve } from "node:path";
import { confirmInstall, promptQuestions } from "./prompt.mjs";

export function parseInstallArgv(argv) {
  const { values } = parseArgs({
    args: argv.slice(2),
    options: {
      "project-dir": { type: "string", default: "" },
      propose: { type: "boolean", default: false },
      apply: { type: "boolean", default: false },
      interactive: { type: "boolean", default: false, short: "i" },
      yes: { type: "boolean", default: false },
      answers: { type: "string", default: "" },
      json: { type: "boolean", default: false },
    },
    strict: false,
  });
  return values;
}

export function wantsJsonDump(argv) {
  return argv.slice(2).includes("--json");
}

export function wantsInteractive(values, stdin) {
  if (values.yes || values.apply || values.answers || values.propose) {
    return false;
  }
  if (values.interactive || values.i) {
    return true;
  }
  return Boolean(stdin?.isTTY);
}

export function defaultsFromQuestions(questions) {
  const answers = {};
  for (const question of questions) {
    if (question.default === undefined || question.default === null) {
      continue;
    }
    answers[question.id] = question.default;
  }
  return answers;
}

export function parseAnswersJson(raw) {
  if (!raw) {
    return { value: {} };
  }
  try {
    const data = JSON.parse(raw);
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return { error: "--answers must be a JSON object." };
    }
    if (data.answers && typeof data.answers === "object" && !Array.isArray(data.answers)) {
      return { value: data.answers };
    }
    return { value: data };
  } catch (err) {
    return { error: `Invalid --answers JSON: ${err.message}` };
  }
}

export function writeStatus(stream, line) {
  stream.write(`${line}\n`);
}

function writeJson(stdout, payload) {
  stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
}

function writeHumanStop(stdout, proposal) {
  const detail = proposal.message || proposal.notes?.[0] || proposal.named;
  stdout.write(`Cannot install (${proposal.named}): ${detail}\n`);
}

function writeHumanResult(stdout, result) {
  if (result.ok) {
    stdout.write("\nInstall finished.\n");
    if (result.pendingPush) {
      stdout.write(`Push ${result.branch ?? "your branch"} yourself: the conventions commit is local, and Mason reads the remote.\n`);
    }
    return;
  }
  const detail = result.message ? ` ${result.message}` : "";
  stdout.write(`\nInstall stopped (${result.named}).${detail}\n`);
}

function exitCode(result) {
  if (result.ok) {
    return 0;
  }
  return result.named === "command-failed" ? 1 : 2;
}

function sameMissing(a, b) {
  return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((id, index) => id === b[index]);
}

function stopsHere(proposal) {
  return proposal.named !== "ready" && (proposal.questions ?? []).length === 0;
}

/**
 * propose → ask → confirm → apply, until apply is ok or stops. Apply may
 * return `needs-answers` with the ids it lacks: the next propose asks them
 * with defaults read from the folder as it is now. The same ids missing twice
 * means the operator (or --yes) cannot answer them: stop.
 */
async function runRounds({ projectDir, propose, apply, applyOpts, stdout, jsonDump, ask }) {
  const answers = {};
  let lastMissing = null;
  for (;;) {
    const proposal = propose(projectDir, answers);
    if (stopsHere(proposal)) {
      writeHumanStop(stdout, proposal);
      if (jsonDump) {
        writeJson(stdout, proposal);
      }
      return 2;
    }
    const questions = proposal.questions ?? [];
    if (questions.length > 0) {
      const asked = await ask(questions, proposal);
      if (asked === null) {
        stdout.write("Install cancelled.\n");
        return 0;
      }
      Object.assign(answers, asked);
    }
    const result = apply(projectDir, answers, applyOpts);
    if (result.ok) {
      writeHumanResult(stdout, result);
      if (jsonDump) {
        writeJson(stdout, result);
      }
      return 0;
    }
    if (result.named === "needs-answers" && !sameMissing(result.missing, lastMissing)) {
      lastMissing = result.missing;
      continue;
    }
    writeHumanResult(stdout, result);
    if (jsonDump) {
      writeJson(stdout, result);
    }
    return exitCode(result);
  }
}

/**
 * A `question()` that never loses a line: piped stdin delivers lines faster
 * than questions are asked, and readline drops the ones nobody is waiting for.
 */
function openQueuedReadline({ stdin, stdout }) {
  const rl = createInterface({ input: stdin, output: stdout, terminal: Boolean(stdin.isTTY) });
  const lines = [];
  const waiting = [];
  let closed = false;
  rl.on("line", (line) => {
    const next = waiting.shift();
    if (next) {
      next(line);
    } else {
      lines.push(line);
    }
  });
  rl.on("close", () => {
    closed = true;
    for (const next of waiting.splice(0)) {
      next("");
    }
  });
  return {
    question(prompt) {
      stdout.write(prompt);
      if (lines.length > 0) {
        return Promise.resolve(lines.shift());
      }
      if (closed) {
        return Promise.resolve("");
      }
      return new Promise((resolve) => waiting.push(resolve));
    },
    close() {
      rl.close();
    },
  };
}

async function runInteractive({ projectDir, propose, apply, stdin, stdout, applyOpts, jsonDump, openReadline }) {
  stdout.write(`\nInstall into ${projectDir}\n`);
  const rl = (openReadline ?? openQueuedReadline)({ stdin, stdout });
  try {
    return await runRounds({
      projectDir,
      propose,
      apply,
      applyOpts,
      stdout,
      jsonDump,
      ask: async (questions, proposal) => {
        const answers = await promptQuestions(questions, { stdout, readline: rl });
        const confirmed = await confirmInstall(questions, answers, { stdout, readline: rl, effects: proposal.effects ?? [] });
        return confirmed ? answers : null;
      },
    });
  } finally {
    rl.close();
  }
}

export async function runInstallCli({ id, propose, apply, argv, stdin, stdout, stderr, openReadline }) {
  const log = stderr ?? stdout;
  const values = parseInstallArgv(argv);
  const projectDir = resolve(values["project-dir"] || ".");
  const jsonDump = wantsJsonDump(argv);
  const status = (line) => writeStatus(log, line);
  const applyOpts = {
    onStatus: status,
    inheritOutput: true,
  };

  if (wantsInteractive(values, stdin)) {
    return runInteractive({ projectDir, propose, apply, stdin, stdout, applyOpts, jsonDump, openReadline });
  }

  if (values.propose || (!values.apply && !values.yes && !values.answers)) {
    status(`Checking ${projectDir}…`);
    const proposal = propose(projectDir, {});
    writeJson(stdout, proposal);
    return stopsHere(proposal) ? 2 : 0;
  }

  if (values.yes) {
    status(`Installing ${projectDir}…`);
    return runRounds({
      projectDir,
      propose,
      apply,
      applyOpts,
      stdout,
      jsonDump: true,
      ask: async (questions) => defaultsFromQuestions(questions),
    });
  }

  const parsed = parseAnswersJson(values.answers);
  if (parsed.error) {
    writeJson(stdout, { ok: false, named: "invalid-answers", message: parsed.error, id });
    return 2;
  }
  status(`Installing ${projectDir}…`);
  const result = apply(projectDir, parsed.value, applyOpts);
  writeJson(stdout, result);
  return exitCode(result);
}
