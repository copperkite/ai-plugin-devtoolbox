import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { apply, propose } from "./install_apply.mjs";
import { inferShape, mergeAdopted } from "./install_propose.mjs";

test("inferShape reads docs layout", () => {
  const root = mkdtempSync(join(tmpdir(), "shape-"));
  assert.equal(inferShape(root).shape, "single-file");
  mkdirSync(join(root, "docs"));
  writeFileSync(join(root, "docs", "PRODUCT.md"), "# x\n");
  assert.equal(inferShape(root).shape, "flat");
});

test("mergeAdopted never invents a domain that was not picked", () => {
  const merged = mergeAdopted(null, { adopted: ["testing"], "documentation.shape": "tree" });
  assert.deepEqual(merged.adopted, { testing: true });
});

test("apply records picks and scaffolds flat docs without overwriting", () => {
  const projectDir = mkdtempSync(join(tmpdir(), "adopt-"));
  writeFileSync(join(projectDir, "package.json"), JSON.stringify({ name: "demo-lib", scripts: { test: "echo" } }));
  writeFileSync(join(projectDir, "README.md"), "keep me\n");
  const result = apply(projectDir, {
    adopted: ["documentation", "testing"],
    "documentation.shape": "flat",
  });
  assert.equal(result.ok, true);
  const record = JSON.parse(readFileSync(join(projectDir, ".agent-adoptions.json"), "utf8"));
  assert.deepEqual(record["ai-plugin-dev"].adopted.documentation, { shape: "flat" });
  assert.equal(record["ai-plugin-dev"].adopted.testing, true);
  assert.equal(readFileSync(join(projectDir, "README.md"), "utf8"), "keep me\n");
  assert.equal(existsSync(join(projectDir, "docs", "PRODUCT.md")), true);
  assert.equal(existsSync(join(projectDir, "docs", "TESTING.md")), true);
  assert.equal(existsSync(join(projectDir, "docs", "RUNBOOKS.md")), false);
  const product = readFileSync(join(projectDir, "docs", "PRODUCT.md"), "utf8");
  assert.match(product, /last_verified: \d{4}-\d{2}-\d{2}/);
  assert.match(product, /<!-- PROJECT: goal/);
});

test("propose on a recorded project-dir asks only the gap", () => {
  const projectDir = mkdtempSync(join(tmpdir(), "gap-"));
  writeFileSync(
    join(projectDir, ".agent-adoptions.json"),
    JSON.stringify({ "ai-plugin-dev": { adopted: { testing: true } } }, null, 2),
  );
  const proposal = propose(projectDir);
  assert.equal(proposal.named, "needs-answers");
  const adoptedQ = proposal.questions.find((question) => question.id === "adopted");
  assert.ok(adoptedQ.choices.every((choice) => choice.value !== "testing"));
});

test("propose plans the files apply would create and keeps a foreign index", () => {
  const projectDir = mkdtempSync(join(tmpdir(), "plan-"));
  mkdirSync(join(projectDir, "docs"));
  writeFileSync(join(projectDir, "docs", "INDEX.md"), "# Their own index\n");
  writeFileSync(join(projectDir, "README.md"), "keep me\n");
  const proposal = propose(projectDir);
  const paths = Object.fromEntries(proposal.plan.files.map((file) => [file.path, file.action]));
  assert.equal(paths["README.md"], undefined, "existing files are not in the plan");
  assert.equal(paths["docs/INDEX.md"], "kept-foreign");
  assert.equal(paths["docs/PRODUCT.md"], "created");
  assert.equal(existsSync(join(projectDir, "docs", "PRODUCT.md")), false, "propose writes nothing");

  const result = apply(projectDir, { adopted: ["documentation"], "documentation.shape": "flat" });
  assert.equal(result.ok, true);
  assert.equal(result.index.named, "kept-foreign");
  assert.equal(readFileSync(join(projectDir, "docs", "INDEX.md"), "utf8"), "# Their own index\n");
  assert.equal(existsSync(join(projectDir, "docs", "PRODUCT.md")), true);
});
