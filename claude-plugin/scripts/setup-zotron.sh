#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CODEX_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
if [ -z "${PLUGIN_ROOT}" ]; then
  PLUGIN_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "MISSING_UV"
  echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

if [ ! -d "${PLUGIN_ROOT}/python" ]; then
  echo "BROKEN_PLUGIN: missing ${PLUGIN_ROOT}/python"
  exit 1
fi

if [ ! -x "${PLUGIN_ROOT}/bin/zotron" ]; then
  echo "BROKEN_PLUGIN: missing executable ${PLUGIN_ROOT}/bin/zotron"
  exit 1
fi

BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"
for name in zotron zotron-rag zotron-ocr; do
  ln -sfn "${PLUGIN_ROOT}/bin/${name}" "${BIN_DIR}/${name}"
done

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *)
    echo "PATH_HINT: add ${BIN_DIR} to PATH if zotron is not found in new shells."
    ;;
esac

echo "Zotron CLI shims linked in ${BIN_DIR}."

if "${PLUGIN_ROOT}/bin/zotron" ping >/tmp/zotron-ping.json 2>/tmp/zotron-ping.err; then
  cat /tmp/zotron-ping.json
  echo "Zotron bridge is live."
  exit 0
fi

XPI_SRC="${PLUGIN_ROOT}/xpi/zotron.xpi"
if [ ! -f "${XPI_SRC}" ]; then
  echo "BUNDLED_XPI_MISSING: ${XPI_SRC}"
  exit 1
fi

case "$(uname -s)" in
  Darwin*)
    DOWNLOADS="${HOME}/Downloads"
    DISPLAY_PATH="${DOWNLOADS}/zotron.xpi"
    ;;
  Linux*)
    if grep -qi microsoft /proc/version 2>/dev/null && ! command -v zotero >/dev/null 2>&1 && command -v powershell.exe >/dev/null 2>&1; then
      WIN_DL="$(powershell.exe -NoProfile -Command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path" 2>/dev/null | tr -d '\r\n')"
      if [ -n "${WIN_DL}" ] && command -v wslpath >/dev/null 2>&1; then
        DOWNLOADS="$(wslpath -u "${WIN_DL}")"
        DISPLAY_PATH="${WIN_DL}\\zotron.xpi"
      else
        DOWNLOADS="${HOME}/Downloads"
        DISPLAY_PATH="${DOWNLOADS}/zotron.xpi"
      fi
    else
      DOWNLOADS="$(xdg-user-dir DOWNLOAD 2>/dev/null || echo "${HOME}/Downloads")"
      DISPLAY_PATH="${DOWNLOADS}/zotron.xpi"
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    WIN_DL="$(powershell.exe -NoProfile -Command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path" 2>/dev/null | tr -d '\r\n')"
    DOWNLOADS="$(cygpath -u "${WIN_DL}")"
    DISPLAY_PATH="${WIN_DL}\\zotron.xpi"
    ;;
  *)
    DOWNLOADS="${HOME}/Downloads"
    DISPLAY_PATH="${DOWNLOADS}/zotron.xpi"
    ;;
esac

mkdir -p "${DOWNLOADS}"
cp "${XPI_SRC}" "${DOWNLOADS}/zotron.xpi"

echo "Zotron bridge is not live yet."
if [ -s /tmp/zotron-ping.err ]; then
  echo "Last ping error:"
  sed -n '1,12p' /tmp/zotron-ping.err
fi
echo
echo "XPI placed at:"
echo "${DISPLAY_PATH}"
echo
echo "In Zotero:"
echo "1. Tools -> Plugins"
echo "2. Gear icon -> Install Add-on From File"
echo "3. Choose zotron.xpi from the path above"
echo "4. Install, then restart Zotero"
echo
echo "After restart, verify with:"
echo "zotron ping"
