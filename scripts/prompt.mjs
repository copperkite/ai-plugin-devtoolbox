/**
 * Interactive questionnaire: clear prompts, visible defaults, recap, confirm.
 */

export function formatDisplayedValue(value) {
  if (value === undefined || value === null || value === "") {
    return "";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  return String(value);
}

export function formatChoices(question) {
  return (question.choices ?? []).map((choice) =>
    typeof choice === "string" ? { value: choice, label: choice } : choice,
  );
}

/**
 * `askIf` is one rule or a list of rules that must all hold:
 * `{ id, includes }` for a set answer, `{ id, equals }` for any other.
 */
export function shouldAskQuestion(question, answers) {
  const rules = question.askIf === undefined ? [] : [question.askIf].flat();
  return rules.every((rule) => {
    const current = answers[rule.id];
    if (rule.includes !== undefined) {
      return Array.isArray(current) && current.includes(rule.includes);
    }
    if (rule.equals !== undefined) {
      return current === rule.equals;
    }
    return true;
  });
}

export function parseConfirm(line, defaultYes = true) {
  const trimmed = line.trim().toLowerCase();
  if (trimmed === "") {
    return defaultYes;
  }
  if (trimmed === "y" || trimmed === "yes") {
    return true;
  }
  if (trimmed === "n" || trimmed === "no") {
    return false;
  }
  return null;
}

export function formatSummaryLines(questions, answers) {
  const lines = [];
  for (const question of questions) {
    if (!Object.hasOwn(answers, question.id)) {
      continue;
    }
    const shown = formatDisplayedValue(answers[question.id]);
    lines.push(`  ${question.prompt}: ${shown === "" ? "(none)" : shown}`);
  }
  return lines;
}

function parseEnum(line, question, choices) {
  const def = question.default;
  if (line === "" && def !== undefined && def !== null) {
    return def;
  }
  const asNumber = Number.parseInt(line, 10);
  if (Number.isInteger(asNumber) && asNumber >= 1 && asNumber <= choices.length) {
    return choices[asNumber - 1].value;
  }
  const match = choices.find((choice) => choice.value === line || choice.label === line);
  return match ? match.value : line;
}

function parseSet(line, question, choices) {
  const def = question.default;
  if (line === "" && def !== undefined && def !== null) {
    return def;
  }
  if (line.toLowerCase() === "all") {
    return choices.map((choice) => choice.value);
  }
  if (line.toLowerCase() === "none") {
    return [];
  }
  return line
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const asNumber = Number.parseInt(part, 10);
      if (Number.isInteger(asNumber) && asNumber >= 1 && asNumber <= choices.length) {
        return choices[asNumber - 1].value;
      }
      return part;
    });
}

function parseBool(line, question) {
  const def = question.default;
  if (line === "" && def !== undefined && def !== null) {
    return def;
  }
  const lower = line.toLowerCase();
  return lower === "y" || lower === "yes" || lower === "true";
}

function parseString(line, question) {
  const def = question.default;
  if (line === "" && def !== undefined && def !== null) {
    return def;
  }
  return line;
}

function writeBlock(stdout, lines) {
  stdout.write(`${lines.join("\n")}\n`);
}

function promptLines(question) {
  const choices = formatChoices(question);
  const defHint = formatDisplayedValue(question.default);
  const lines = [""];
  if (question.help) {
    lines.push(question.help);
  }
  lines.push(question.prompt);
  if (question.type === "enum" || question.type === "set") {
    for (const [index, choice] of choices.entries()) {
      const isDefault = question.type === "enum" && choice.value === question.default;
      lines.push(`  ${index + 1}) ${choice.label}${isDefault ? " (default)" : ""}`);
    }
  }
  if (question.type === "set") {
    lines.push('  Type numbers (1,3), names, "all", or "none".');
  }
  if (defHint) {
    lines.push(`  Enter keeps: ${defHint}`);
  } else {
    lines.push("  (no default — type a value)");
  }
  return { lines, choices };
}

export async function promptQuestions(questions, { stdout, readline }) {
  const rl = readline;
  const answers = {};
  for (const question of questions) {
    if (!shouldAskQuestion(question, answers)) {
      continue;
    }
    const { lines, choices } = promptLines(question);
    writeBlock(stdout, lines);
    const line = (await rl.question("> ")).trim();
    if (question.type === "enum") {
      answers[question.id] = parseEnum(line, question, choices);
      continue;
    }
    if (question.type === "set") {
      answers[question.id] = parseSet(line, question, choices);
      continue;
    }
    if (question.type === "bool") {
      answers[question.id] = parseBool(line, question);
      continue;
    }
    answers[question.id] = parseString(line, question);
  }
  return answers;
}

export async function confirmInstall(questions, answers, { stdout, readline, effects = [] }) {
  stdout.write("\nYour choices:\n");
  writeBlock(stdout, formatSummaryLines(questions, answers));
  if (effects.length > 0) {
    stdout.write("\nWhat will happen:\n");
    writeBlock(
      stdout,
      effects.map((line) => `  - ${line}`),
    );
  }
  stdout.write("\n");
  for (;;) {
    const line = await readline.question("Start the install? [Y/n] ");
    const parsed = parseConfirm(line, true);
    if (parsed === null) {
      stdout.write("Please answer y or n.\n");
      continue;
    }
    return parsed;
  }
}
