#!/usr/bin/env bash
set -euo pipefail

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

major_node_version() {
  node -p "process.versions.node.split('.')[0]"
}

package_vsix() {
  local script_dir="$1"
  local output_path="$2"
  local major_version

  major_version="$(major_node_version)"
  if [[ "${major_version}" =~ ^[0-9]+$ ]] && (( major_version >= 20 )); then
    (
      cd "${script_dir}"
      npx --yes @vscode/vsce package -o "${output_path}"
    )
    return
  fi

  echo "Node ${major_version} detected; packaging VSIX with temporary Node 20 toolchain..."
  (
    cd "${script_dir}"
    TARGET_VSIX="${output_path}" \
      npx --yes -p node@20 -p @vscode/vsce bash -lc 'vsce package -o "$TARGET_VSIX"'
  )
}

resolve_code_bin() {
  if [[ -n "${CODE_BIN:-}" ]]; then
    echo "${CODE_BIN}"
    return
  fi

  if command -v code >/dev/null 2>&1; then
    echo "code"
    return
  fi

  if command -v code-insiders >/dev/null 2>&1; then
    echo "code-insiders"
    return
  fi

  echo "Could not find a VS Code CLI. Set CODE_BIN to your editor command." >&2
  exit 1
}

installed_version() {
  local code_bin="$1"
  "${code_bin}" --list-extensions --show-versions 2>/dev/null \
    | sed -n -E 's/^(rdshr|local)\.(shelf-ai|archsync)@(.+)$/\3/p' \
    | head -n 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_BIN="$(resolve_code_bin)"

require_command node
require_command npx

VERSION="$(cd "${SCRIPT_DIR}" && node -p "require('./package.json').version")"
RELEASES_DIR="${SCRIPT_DIR}/releases"
VSIX_PATH="${RELEASES_DIR}/shelf-ai-${VERSION}.vsix"
PREVIOUS_VERSION="$(installed_version "${CODE_BIN}" || true)"

mkdir -p "${RELEASES_DIR}"

echo "Packaging Shelf AI ${VERSION}..."
package_vsix "${SCRIPT_DIR}" "${VSIX_PATH}"

if [[ -n "${PREVIOUS_VERSION}" ]]; then
  echo "Installed version before update: ${PREVIOUS_VERSION}"
else
  echo "Shelf AI is not currently installed."
fi

# Clean up existing installs so the remote host doesn't keep multiple stale versions around.
"${CODE_BIN}" --uninstall-extension local.strict-mapping-guard >/dev/null 2>&1 || true
"${CODE_BIN}" --uninstall-extension local.mapping >/dev/null 2>&1 || true
"${CODE_BIN}" --uninstall-extension local.shelf-ai >/dev/null 2>&1 || true
"${CODE_BIN}" --uninstall-extension rdshr.shelf-ai >/dev/null 2>&1 || true
"${CODE_BIN}" --uninstall-extension local.archsync >/dev/null 2>&1 || true
"${CODE_BIN}" --uninstall-extension rdshr.archsync >/dev/null 2>&1 || true
"${CODE_BIN}" --install-extension "${VSIX_PATH}" --force

CURRENT_VERSION="$(installed_version "${CODE_BIN}" || true)"
if [[ "${CURRENT_VERSION}" != "${VERSION}" ]]; then
  echo "Install verification failed: expected ${VERSION}, got ${CURRENT_VERSION:-<none>}." >&2
  exit 1
fi

echo "Installed Shelf AI ${CURRENT_VERSION} from ${VSIX_PATH}"
