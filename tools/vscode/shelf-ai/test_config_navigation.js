const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const {
  findCurrentTomlSection,
  isProjectConfigFile,
  resolveConfigToCodeTarget,
} = require("./config_navigation");

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text);
}

function setMtime(filePath, timeMs) {
  const time = new Date(timeMs);
  fs.utimesSync(filePath, time, time);
}

function createFixtureRepo() {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-config-navigation-"));
  const projectFilePath = path.join(repoRoot, "projects", "demo", "project.toml");
  const frameworkFilePath = path.join(repoRoot, "framework", "demo", "L1-M0-demo-module.md");
  const codeLayerPath = path.join(repoRoot, "src", "project_runtime", "code_layer.py");
  const canonicalPath = path.join(repoRoot, "projects", "demo", "generated", "canonical.json");

  writeFile(
    projectFilePath,
    `
[project]
project_id = "demo"

[framework]

[[framework.modules]]
role = "demo"
framework_file = "framework/demo/L1-M0-demo-module.md"

[exact.demo.chat]
enabled = true
`
  );
  writeFile(frameworkFilePath, "# demo module\n");
  writeFile(
    codeLayerPath,
    `
def demo_runtime(boundary_context):
    _require_boundary_context_value(boundary_context, "CHAT")
`
  );

  const staticParamCodeTarget = {
    target_kind: "code_correspondence",
    layer: "code",
    file_path: "src/project_runtime/code_layer.py",
    start_line: 3,
    end_line: 3,
    symbol: "exact_export.modules.demo_l1_m0.static_params.chat",
    label: "chat static param",
    is_primary: true,
    is_editable: true,
    is_deprecated_alias: false,
  };
  const staticParamConfigTarget = {
    target_kind: "config_source",
    layer: "config",
    file_path: "projects/demo/project.toml",
    start_line: 10,
    end_line: 10,
    symbol: "exact.demo.chat",
    label: "exact.demo.chat",
    is_primary: false,
    is_editable: true,
    is_deprecated_alias: false,
  };
  const boundaryConfigTarget = {
    target_kind: "config_source",
    layer: "config",
    file_path: "projects/demo/project.toml",
    start_line: 10,
    end_line: 10,
    symbol: "exact.demo.chat",
    label: "exact.demo.chat",
    is_primary: true,
    is_editable: true,
    is_deprecated_alias: false,
  };

  writeFile(
    canonicalPath,
    JSON.stringify(
      {
        framework: {
          modules: [
            {
              module_id: "demo.L1.M0",
              framework_file: "framework/demo/L1-M0-demo-module.md",
            },
          ],
        },
        config: {
          modules: [
            {
              module_id: "demo.L1.M0",
              source_ref: {
                file_path: "projects/demo/project.toml",
                line: 1,
              },
              compiled_config_export: {
                boundary_bindings: [
                  {
                    boundary_id: "CHAT",
                    primary_exact_path: "exact.demo.chat",
                    primary_communication_path: "communication.demo.chat",
                  },
                ],
              },
            },
          ],
        },
        code: {
          modules: [
            {
              module_id: "demo.L1.M0",
              source_ref: {
                file_path: "src/project_runtime/code_layer.py",
                line: 1,
              },
              code_bindings: {
                implementation_slots: [
                  {
                    boundary_id: "CHAT",
                    slot_kind: "module_static_param",
                    source_ref: {
                      file_path: "src/project_runtime/code_layer.py",
                      line: 3,
                    },
                    source_symbol: "exact.demo.chat",
                    anchor_path: "exact_export.modules.demo_l1_m0.static_params.chat",
                  },
                ],
              },
            },
          ],
        },
        correspondence: {
          correspondence_schema_version: 1,
          objects: [
            {
              object_kind: "static_param",
              object_id: "demo::static_param::chat",
              owner_module_id: "demo.L1.M0",
              display_name: "chat",
              materialization_kind: "static_class",
              primary_nav_target_kind: "code_correspondence",
              primary_edit_target_kind: "code_correspondence",
              correspondence_anchor: staticParamCodeTarget,
              implementation_anchor: staticParamCodeTarget,
              navigation_targets: [
                staticParamCodeTarget,
                staticParamConfigTarget,
              ],
            },
            {
              object_kind: "boundary",
              object_id: "demo::boundary::chat",
              owner_module_id: "demo.L1.M0",
              display_name: "CHAT",
              materialization_kind: "static_class",
              primary_nav_target_kind: "config_source",
              primary_edit_target_kind: "config_source",
              correspondence_anchor: boundaryConfigTarget,
              implementation_anchor: boundaryConfigTarget,
              navigation_targets: [boundaryConfigTarget],
            },
          ],
          tree: [],
          validation_summary: {
            passed: true,
            rule_count: 0,
            error_count: 0,
            issues: [],
            issue_count_by_object: {},
          },
        },
      },
      null,
      2
    )
  );

  const baseTime = Date.now() - 60_000;
  setMtime(projectFilePath, baseTime);
  setMtime(frameworkFilePath, baseTime);
  setMtime(codeLayerPath, baseTime);
  setMtime(canonicalPath, baseTime + 5_000);

  return {
    repoRoot,
    projectFilePath,
    cleanup: () => fs.rmSync(repoRoot, { recursive: true, force: true }),
  };
}

function findLineBySection(text, sectionName) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].trim() === `[${sectionName}]`) {
      return index;
    }
  }
  return -1;
}

function findLineContaining(text, token) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].includes(token)) {
      return index + 1;
    }
  }
  return -1;
}

function findFirstExactSection(text) {
  const lines = String(text || "").split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const match = /^\s*\[(exact\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\]\s*$/.exec(lines[index] || "");
    if (match) {
      return {
        sectionName: match[1],
        line: index,
      };
    }
  }
  return null;
}

function main() {
  const fixture = createFixtureRepo();
  try {
    const repoRoot = fixture.repoRoot;
    const projectFilePath = fixture.projectFilePath;
    assert(isProjectConfigFile(projectFilePath, repoRoot), "project.toml should be recognized as project config file");

    const text = fs.readFileSync(projectFilePath, "utf8");
    const firstExactSection = findFirstExactSection(text);
    assert(firstExactSection, "at least one exact.<framework>.<boundary> section should exist");
    const exactSectionLine = firstExactSection.line;
    const exactSectionName = firstExactSection.sectionName;
    const boundaryToken = exactSectionName.split(".").pop();
    assert(boundaryToken, "exact section should include boundary token");

    const sectionInfo = findCurrentTomlSection(text, exactSectionLine + 1);
    assert(sectionInfo, "section info should be resolved inside exact boundary section");
    assert.strictEqual(sectionInfo.sectionName, exactSectionName);

    const codeTarget = resolveConfigToCodeTarget({
      repoRoot,
      filePath: projectFilePath,
      text,
      line: exactSectionLine + 1,
      character: 0,
    });
    assert(codeTarget, "config section should resolve to code anchor target");
    assert.strictEqual(codeTarget.boundaryId, boundaryToken.toUpperCase());
    assert(codeTarget.objectId.includes(`::static_param::${boundaryToken}`));
    assert.strictEqual(codeTarget.targetKind, "code_correspondence");
    assert(codeTarget.filePath.endsWith(path.join("src", "project_runtime", "code_layer.py")));
    assert(Number.isInteger(codeTarget.line) && codeTarget.line >= 0, "code target should include valid line");

    const codeLayerPath = path.join(repoRoot, "src", "project_runtime", "code_layer.py");
    const codeLayerText = fs.readFileSync(codeLayerPath, "utf8");
    const expectedBoundaryLine = findLineContaining(
      codeLayerText,
      `_require_boundary_context_value(boundary_context, "${boundaryToken.toUpperCase()}")`
    );
    if (expectedBoundaryLine > 0) {
      assert.strictEqual(
        codeTarget.line,
        expectedBoundaryLine - 1,
        "exact boundary section should resolve to module static params consumer anchor"
      );
    }

    const projectSectionLine = findLineBySection(text, "project");
    assert(projectSectionLine >= 0, "project section should exist");
    const noTarget = resolveConfigToCodeTarget({
      repoRoot,
      filePath: projectFilePath,
      text,
      line: projectSectionLine,
      character: 0,
    });
    assert.strictEqual(noTarget, null, "non-boundary sections should not resolve to code anchors");
  } finally {
    fixture.cleanup();
  }
}

main();
