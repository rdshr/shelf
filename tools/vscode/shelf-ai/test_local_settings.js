const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const localSettings = require("./local_settings");

function withTempDir(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-local-settings-"));
  try {
    run(root);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
}

function writeLocalSettings(root, text) {
  const dir = path.join(root, ".shelf");
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "settings.jsonc"), text, "utf8");
}

function createConfigStub({ defaultValues = {}, explicitValues = {} } = {}) {
  return {
    inspect(key) {
      if (Object.prototype.hasOwnProperty.call(explicitValues, key)) {
        return { workspaceValue: explicitValues[key] };
      }
      return { workspaceValue: undefined };
    },
    get(key) {
      if (Object.prototype.hasOwnProperty.call(explicitValues, key)) {
        return explicitValues[key];
      }
      return defaultValues[key];
    },
  };
}

function testJsoncSanitizer() {
  const text = `{
    // comment
    "shelf": {
      "guardMode": "strict",
      "enableOnSave": false, // inline
    },
    "shelf.validationDebounceMs": 120,
  }`;
  const parsed = JSON.parse(localSettings.sanitizeJsonc(text));
  assert.strictEqual(parsed.shelf.guardMode, "strict");
  assert.strictEqual(parsed.shelf.enableOnSave, false);
  assert.strictEqual(parsed["shelf.validationDebounceMs"], 120);
}

function testReadLocalSettings() {
  withTempDir((root) => {
    writeLocalSettings(root, `{
      "shelf": {
        "guardMode": "strict",
        "validationDebounceMs": 300
      },
      "shelf.enableOnSave": false,
      "ignored": true
    }`);

    const snapshot = localSettings.readLocalShelfSettings(root);
    assert.strictEqual(snapshot.exists, true);
    assert.strictEqual(snapshot.error, "");
    assert.strictEqual(snapshot.values["shelf.guardMode"], "strict");
    assert.strictEqual(snapshot.values["shelf.validationDebounceMs"], 300);
    assert.strictEqual(snapshot.values["shelf.enableOnSave"], false);
    assert.strictEqual(snapshot.values.ignored, undefined);
  });
}

function testReadLocalSettingsError() {
  withTempDir((root) => {
    writeLocalSettings(root, "{ invalid jsonc ");
    const snapshot = localSettings.readLocalShelfSettings(root);
    assert.strictEqual(snapshot.exists, true);
    assert(snapshot.error.includes("Failed to parse"), "parse error message should be surfaced");
    assert.deepStrictEqual(snapshot.values, {});
  });
}

function testSettingPrecedence() {
  const localValues = {
    "shelf.guardMode": "strict",
    "shelf.enableOnSave": false,
  };
  const defaultValues = {
    guardMode: "normal",
    enableOnSave: true,
    validationDebounceMs: 250,
  };

  const fallbackConfig = createConfigStub({ defaultValues });
  assert.strictEqual(
    localSettings.getShelfSetting(fallbackConfig, localValues, "guardMode"),
    "strict",
    "local .shelf setting should override package default when VSCode setting is not explicitly set"
  );
  assert.strictEqual(
    localSettings.getShelfSetting(fallbackConfig, localValues, "validationDebounceMs"),
    250,
    "fallback should keep package default when local key is not defined"
  );

  const explicitConfig = createConfigStub({
    defaultValues,
    explicitValues: {
      guardMode: "normal",
      enableOnSave: true,
    },
  });
  assert.strictEqual(
    localSettings.getShelfSetting(explicitConfig, localValues, "guardMode"),
    "normal",
    "explicit VSCode setting should override .shelf value"
  );
  assert.strictEqual(
    localSettings.getShelfSetting(explicitConfig, localValues, "enableOnSave"),
    true,
    "explicit VSCode setting should keep highest priority"
  );
}

function main() {
  testJsoncSanitizer();
  testReadLocalSettings();
  testReadLocalSettingsError();
  testSettingPrecedence();
}

main();
