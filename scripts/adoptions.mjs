/**
 * `.agent-adoptions.json` at the project directory root: one object, one key per plugin id.
 * This copy is local to the plugin; do not import it from another plugin tree.
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const ADOPTIONS_FILE = ".agent-adoptions.json";

export function readAdoptionsFile(projectDir) {
  const path = join(projectDir, ADOPTIONS_FILE);
  if (!existsSync(path)) {
    return {};
  }
  try {
    const data = JSON.parse(readFileSync(path, "utf8"));
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return {};
    }
    return data;
  } catch {
    return {};
  }
}

export function readPluginSlice(projectDir, pluginId) {
  const slice = readAdoptionsFile(projectDir)[pluginId];
  if (!slice || typeof slice !== "object" || Array.isArray(slice)) {
    return null;
  }
  return slice;
}

export function writePluginSlice(projectDir, pluginId, slice) {
  const all = readAdoptionsFile(projectDir);
  all[pluginId] = slice;
  writeFileSync(join(projectDir, ADOPTIONS_FILE), `${JSON.stringify(all, null, 2)}\n`);
}
