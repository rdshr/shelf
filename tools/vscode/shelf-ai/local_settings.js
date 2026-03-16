const fs = require("fs");
const path = require("path");

const LOCAL_SETTINGS_REL_PATH = path.join(".shelf", "settings.jsonc");

function stripJsonComments(input) {
  const text = String(input || "");
  let output = "";
  let index = 0;
  let inString = false;
  let inLineComment = false;
  let inBlockComment = false;
  let escapeNext = false;
  let stringQuote = "\"";

  while (index < text.length) {
    const char = text[index];
    const next = text[index + 1] || "";

    if (inLineComment) {
      if (char === "\n") {
        inLineComment = false;
        output += char;
      }
      index += 1;
      continue;
    }

    if (inBlockComment) {
      if (char === "*" && next === "/") {
        inBlockComment = false;
        index += 2;
        continue;
      }
      if (char === "\n") {
        output += char;
      }
      index += 1;
      continue;
    }

    if (inString) {
      output += char;
      if (escapeNext) {
        escapeNext = false;
      } else if (char === "\\") {
        escapeNext = true;
      } else if (char === stringQuote) {
        inString = false;
      }
      index += 1;
      continue;
    }

    if (char === "/" && next === "/") {
      inLineComment = true;
      index += 2;
      continue;
    }

    if (char === "/" && next === "*") {
      inBlockComment = true;
      index += 2;
      continue;
    }

    if (char === "\"" || char === "'") {
      inString = true;
      stringQuote = char;
      output += char;
      index += 1;
      continue;
    }

    output += char;
    index += 1;
  }

  return output;
}

function stripTrailingCommas(input) {
  const text = String(input || "");
  let output = "";
  let index = 0;
  let inString = false;
  let escapeNext = false;
  let stringQuote = "\"";

  while (index < text.length) {
    const char = text[index];
    if (inString) {
      output += char;
      if (escapeNext) {
        escapeNext = false;
      } else if (char === "\\") {
        escapeNext = true;
      } else if (char === stringQuote) {
        inString = false;
      }
      index += 1;
      continue;
    }

    if (char === "\"" || char === "'") {
      inString = true;
      stringQuote = char;
      output += char;
      index += 1;
      continue;
    }

    if (char === ",") {
      let lookahead = index + 1;
      while (lookahead < text.length && /\s/.test(text[lookahead])) {
        lookahead += 1;
      }
      const trailingTarget = text[lookahead] || "";
      if (trailingTarget === "}" || trailingTarget === "]") {
        index += 1;
        continue;
      }
    }

    output += char;
    index += 1;
  }

  return output;
}

function sanitizeJsonc(input) {
  return stripTrailingCommas(stripJsonComments(input));
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizeLocalShelfSettings(payload) {
  if (!isPlainObject(payload)) {
    return {};
  }

  const values = {};
  const assign = (key, value) => {
    const normalizedKey = String(key || "").trim();
    if (!normalizedKey.startsWith("shelf.")) {
      return;
    }
    values[normalizedKey] = value;
  };

  for (const [key, value] of Object.entries(payload)) {
    if (key === "shelf" && isPlainObject(value)) {
      for (const [childKey, childValue] of Object.entries(value)) {
        assign(`shelf.${String(childKey || "").trim()}`, childValue);
      }
      continue;
    }
    assign(key, value);
  }

  return values;
}

function readLocalShelfSettings(repoRoot) {
  const root = String(repoRoot || "").trim();
  const filePath = path.join(root, LOCAL_SETTINGS_REL_PATH);
  const result = {
    filePath,
    values: {},
    exists: fs.existsSync(filePath),
    error: "",
  };

  if (!result.exists) {
    return result;
  }

  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const parsed = JSON.parse(sanitizeJsonc(raw));
    if (!isPlainObject(parsed)) {
      result.error = `${LOCAL_SETTINGS_REL_PATH} must be a JSON object.`;
      return result;
    }
    result.values = normalizeLocalShelfSettings(parsed);
    return result;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    result.error = `Failed to parse ${LOCAL_SETTINGS_REL_PATH}: ${message}`;
    return result;
  }
}

function hasExplicitShelfSettingOverride(inspected) {
  if (!inspected || typeof inspected !== "object") {
    return false;
  }

  return [
    "workspaceFolderValue",
    "workspaceValue",
    "globalValue",
    "workspaceFolderLanguageValue",
    "workspaceLanguageValue",
    "globalLanguageValue",
  ].some((field) => inspected[field] !== undefined);
}

function getShelfSetting(config, localValues, key, fallback) {
  const settingKey = String(key || "").trim();
  if (!settingKey) {
    return fallback;
  }

  const inspected = typeof config?.inspect === "function"
    ? config.inspect(settingKey)
    : undefined;
  if (hasExplicitShelfSettingOverride(inspected)) {
    const explicitValue = config.get(settingKey);
    return explicitValue === undefined ? fallback : explicitValue;
  }

  const localKey = `shelf.${settingKey}`;
  if (isPlainObject(localValues) && Object.prototype.hasOwnProperty.call(localValues, localKey)) {
    return localValues[localKey];
  }

  const configValue = config?.get?.(settingKey);
  return configValue === undefined ? fallback : configValue;
}

module.exports = {
  LOCAL_SETTINGS_REL_PATH,
  getShelfSetting,
  hasExplicitShelfSettingOverride,
  normalizeLocalShelfSettings,
  readLocalShelfSettings,
  stripJsonComments,
  stripTrailingCommas,
  sanitizeJsonc,
};
