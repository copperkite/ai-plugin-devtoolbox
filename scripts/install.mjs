#!/usr/bin/env node
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { apply, propose } from "./install_apply.mjs";
import { runInstallCli } from "./install-cli.mjs";

export { apply, propose };

async function main() {
  const code = await runInstallCli({
    id: "ai-plugin-dev",
    propose,
    apply,
    argv: process.argv,
    stdin: process.stdin,
    stdout: process.stdout,
    stderr: process.stderr,
  });
  process.exit(code);
}

const thisFile = fileURLToPath(import.meta.url);
if (process.argv[1] && resolve(process.argv[1]) === thisFile) {
  main();
}
