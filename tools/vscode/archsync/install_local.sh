#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VSIX_PATH="$(find "${SCRIPT_DIR}/releases" -maxdepth 1 -type f -name 'archsync-*.vsix' | sort -V | tail -n 1)"

if [[ -z "${VSIX_PATH}" ]]; then
  echo "No VSIX package found under ${SCRIPT_DIR}/releases" >&2
  exit 1
fi

code --install-extension "${VSIX_PATH}" --force
echo "Installed ${VSIX_PATH}"
