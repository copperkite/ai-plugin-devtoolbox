/**
 * Propose convention picks for this project directory. Never writes.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { readPluginSlice } from "./adoptions.mjs";

export const PLUGIN_ID = "ai-plugin-dev";

const CATALOG = [
  { value: "documentation", label: "Documentation — shape asked separately" },
  { value: "git", label: "Git — release-branch" },
  { value: "release", label: "Release — semver" },
  { value: "code-wording", label: "Code wording" },
  { value: "testing", label: "Testing" },
];

export function readRecord(projectDir) {
  const slice = readPluginSlice(projectDir, PLUGIN_ID);
  if (!slice) {
    return null;
  }
  if (!slice.adopted || typeof slice.adopted !== "object") {
    return { adopted: {} };
  }
  return slice;
}

export function inferShape(projectDir) {
  const docs = join(projectDir, "docs");
  const single = existsSync(join(projectDir, "DOCUMENTATION.md"));
  if (single && existsSync(docs)) {
    return { shape: null, conflict: true };
  }
  if (single) {
    return { shape: "single-file", conflict: false };
  }
  if (existsSync(docs) && statSync(docs).isDirectory()) {
    const names = readdirSync(docs);
    if (names.some((name) => ["context", "architecture", "decisions", "operations"].includes(name))) {
      return { shape: "tree", conflict: false };
    }
    return { shape: "flat", conflict: false };
  }
  return { shape: countSourceFiles(projectDir) <= 8 ? "single-file" : "flat", conflict: false };
}

function countSourceFiles(root) {
  const ignore = new Set([".git", "node_modules", "dist", "build", ".mason"]);
  let count = 0;
  function walk(dir) {
    if (count > 40) {
      return;
    }
    let names;
    try {
      names = readdirSync(dir);
    } catch {
      return;
    }
    for (const name of names) {
      if (ignore.has(name)) {
        continue;
      }
      const path = join(dir, name);
      let st;
      try {
        st = statSync(path);
      } catch {
        continue;
      }
      if (st.isDirectory()) {
        walk(path);
        continue;
      }
      if (/\.(ts|js|mjs|py|go|rs)$/.test(name) && !name.includes(".test.")) {
        count += 1;
      }
    }
  }
  walk(root);
  return count;
}

export function hasTestCommand(projectDir) {
  const pkg = join(projectDir, "package.json");
  if (existsSync(pkg)) {
    try {
      const data = JSON.parse(readFileSync(pkg, "utf8"));
      if (data?.scripts?.test) {
        return true;
      }
    } catch {
      /* ignore */
    }
  }
  return existsSync(join(projectDir, "Makefile"));
}

export function inferVersionFile(projectDir) {
  if (existsSync(join(projectDir, "src", "plugin.json"))) {
    return "src/plugin.json";
  }
  if (existsSync(join(projectDir, "package.json"))) {
    return "package.json";
  }
  if (existsSync(join(projectDir, "Cargo.toml"))) {
    return "Cargo.toml";
  }
  if (existsSync(join(projectDir, "pyproject.toml"))) {
    return "pyproject.toml";
  }
  return "package.json";
}

function missingDomains(adopted) {
  const have = new Set(Object.keys(adopted ?? {}));
  return CATALOG.filter((entry) => !have.has(entry.value));
}

export function mergeAdopted(existing, answers) {
  const adopted = { ...(existing?.adopted ?? {}) };
  const picked = Array.isArray(answers.adopted) ? answers.adopted : [];
  if (picked.includes("documentation") && !adopted.documentation) {
    adopted.documentation = { shape: answers["documentation.shape"] || "flat" };
  }
  if (picked.includes("git") && !adopted.git) {
    adopted.git = { model: "release-branch" };
  }
  if (picked.includes("release") && !adopted.release) {
    adopted.release = {
      scheme: "semver",
      "version-file": answers["release.versionFile"] || "package.json",
    };
  }
  if (picked.includes("code-wording") && adopted["code-wording"] == null) {
    adopted["code-wording"] = true;
  }
  if (picked.includes("testing") && adopted.testing == null) {
    adopted.testing = true;
  }
  const out = { adopted };
  if (existing?.gates) {
    out.gates = existing.gates;
  }
  return out;
}

/**
 * What apply would write for these picks, without writing. `planFiles` is
 * injected by install_apply to keep this module free of file writes.
 */
export function planFor(projectDir, existing, answers, planFiles) {
  const record = mergeAdopted(existing, answers);
  const shape = record.adopted?.documentation?.shape;
  return {
    record,
    files: planFiles ? planFiles(projectDir, shape) : [],
  };
}

export function propose(projectDirArg, { planFiles } = {}) {
  const projectDir = resolve(projectDirArg || ".");
  const record = readRecord(projectDir);
  const inferred = inferShape(projectDir);
  const notes = [];
  if (inferred.conflict) {
    notes.push("Both DOCUMENTATION.md and docs/ exist. Stop and ask a human; do not merge.");
    return {
      schemaVersion: 1,
      plugin: PLUGIN_ID,
      named: "foreign",
      due: [],
      notes,
      questions: [],
      message: notes[0],
    };
  }

  const adopted = record?.adopted ?? {};
  const gap = missingDomains(adopted);
  const questions = [];
  if (gap.length > 0) {
    questions.push({
      id: "adopted",
      type: "set",
      prompt: "Conventions to adopt (gap only)",
      help: record
        ? "Already recorded keys are kept. Pick only what to add."
        : "Nothing recorded yet. Defaults pick the full catalog.",
      default: gap.map((entry) => entry.value),
      choices: gap,
    });
    if (gap.some((entry) => entry.value === "documentation")) {
      questions.push({
        id: "documentation.shape",
        type: "enum",
        prompt: "Documentation shape",
        askIf: { id: "adopted", includes: "documentation" },
        default: inferred.shape,
        choices: [
          { value: "single-file", label: "single-file" },
          { value: "flat", label: "flat" },
          { value: "tree", label: "tree" },
        ],
      });
    }
    if (gap.some((entry) => entry.value === "release")) {
      questions.push({
        id: "release.versionFile",
        type: "string",
        prompt: "Release version-file",
        askIf: { id: "adopted", includes: "release" },
        default: inferVersionFile(projectDir),
      });
    }
  }

  const named = gap.length === 0 ? "ready" : "needs-answers";
  const defaults = {};
  for (const question of questions) {
    defaults[question.id] = question.default;
  }
  const plan = planFor(projectDir, record, defaults, planFiles);
  return {
    schemaVersion: 1,
    plugin: PLUGIN_ID,
    named,
    due: gap.map((entry) => entry.value),
    notes,
    questions,
    plan: {
      note: "With the defaults above. Files already present are skipped; a docs/INDEX.md this plugin did not generate is kept.",
      files: plan.files.filter((file) => file.action !== "skipped"),
    },
  };
}
