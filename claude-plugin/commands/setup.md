---
description: Set up Zotron — verify the XPI plugin is reachable on localhost:23119; if not, drop the bundled XPI into the user's Downloads folder and walk them through Zotero's "Install Add-on From File" flow.
---

# /zotron:setup — Zotron bootstrap

Run this when the user has just installed the `zotron` Claude Code plugin and needs to get the Zotero side wired up.

## Goal

End state: `system.ping` over `localhost:23119/zotron/rpc` returns `{"pong": true, ...}` and the user can ask Claude to do real Zotero work.

## Why we don't fully automate the install

We tried. Zotero 7+ does not accept XPI files via command line (`zotero.exe path/to.xpi` triggers data import, not plugin install — Zotero's CLI inherits Mozilla-toolkit flags but no `--install`), exposes no `zotero://install` URL handler, and no HTTP install endpoint on port 23119. Profile-side-loading via `<profile>/extensions/<id>.xpi` is documented but Zotero's startupCache routinely ignores newly-dropped files. Every "automatic" path is fragile.

What we **can** reliably do: drop the bundled XPI into the user's actual Downloads folder (auto-detected, including drive relocations like `E:\Downloads`), then walk them through Zotero's native install dialog. One file pick, one restart.

## Procedure

### 1. Check `uv` is available

The bundled `zotron` / `zotron-rag` / `zotron-ocr` shims invoke `uv run`. If `uv` is missing, nothing else matters.

```bash
command -v uv >/dev/null || echo "MISSING_UV"
```

If missing, point the user at https://docs.astral.sh/uv/getting-started/installation/ and stop — single-command install: `curl -LsSf https://astral.sh/uv/install.sh | sh`. Do not proceed until `uv` is on PATH.

### 2. Ping the bridge

```bash
curl -sf -X POST http://localhost:23119/zotron/rpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"system.ping","params":{},"id":1}' \
  && echo OK || echo DOWN
```

- **OK** → bridge is live. Run `zotron ping` to print version, confirm to the user, stop.
- **DOWN** → continue. The XPI is missing or Zotero isn't running.

### 3. Confirm Zotero is running

Ask the user: *"Is Zotero open?"*

- **No** → tell them to start Zotero, wait ~5s, re-ping (step 2). If still DOWN → step 4.
- **Yes** → XPI isn't installed → step 4.

### 4. Verify the bundled XPI is intact

```bash
test -f "${CLAUDE_PLUGIN_ROOT}/xpi/zotron.xpi" && echo OK || echo BUNDLED_XPI_MISSING
```

If `BUNDLED_XPI_MISSING`, the plugin install is broken. Tell the user:
> Reinstall the plugin: `/plugin uninstall zotron@zotron` then `/plugin install zotron@zotron`.

### 5. Find the user's real Downloads folder and drop the XPI

Detect platform, resolve the actual Downloads path (handling drive relocation and OneDrive redirect on Windows), copy the bundled XPI there.

```bash
XPI_SRC="${CLAUDE_PLUGIN_ROOT}/xpi/zotron.xpi"

case "$(uname -s)" in
  Darwin*)
    DOWNLOADS="$HOME/Downloads"
    DISPLAY_PATH="$DOWNLOADS/zotron.xpi"
    ;;

  Linux*)
    if grep -qi microsoft /proc/version 2>/dev/null && ! command -v zotero >/dev/null 2>&1; then
      # WSL → Windows-host Zotero. Resolve the canonical Downloads path
      # via Shell.Application — handles E:\Downloads, OneDrive redirect,
      # any %USERPROFILE%-relative variation. Returns a real filesystem path.
      WIN_DL=$(powershell.exe -NoProfile -Command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path" 2>/dev/null | tr -d '\r\n')
      if [ -z "$WIN_DL" ]; then
        echo "Could not resolve Windows Downloads path (PowerShell interop failed)."
        echo "Manual fallback: copy ${XPI_SRC} somewhere your Zotero can read, then install via Tools → Plugins."
        return 1 2>/dev/null || exit 1
      fi
      DOWNLOADS=$(wslpath -u "$WIN_DL")
      DISPLAY_PATH="$WIN_DL\\zotron.xpi"
    else
      # Native Linux (or WSLg with Linux Zotero on PATH).
      DOWNLOADS="$(xdg-user-dir DOWNLOAD 2>/dev/null || echo "$HOME/Downloads")"
      DISPLAY_PATH="$DOWNLOADS/zotron.xpi"
    fi
    ;;

  MINGW*|MSYS*|CYGWIN*)
    # Native Windows shell.
    WIN_DL=$(powershell.exe -NoProfile -Command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path" 2>/dev/null | tr -d '\r\n')
    DOWNLOADS=$(cygpath -u "$WIN_DL")
    DISPLAY_PATH="$WIN_DL\\zotron.xpi"
    ;;

  *)
    echo "Unknown platform: $(uname -s). Manually copy ${XPI_SRC} somewhere Zotero can read."
    return 1 2>/dev/null || exit 1
    ;;
esac

mkdir -p "$DOWNLOADS"
cp "$XPI_SRC" "$DOWNLOADS/zotron.xpi"
echo "XPI placed at: $DISPLAY_PATH"
```

The `DISPLAY_PATH` is what you tell the user verbatim — it's the path **as their Zotero will see it** (Windows-style on Windows/WSL, POSIX on Linux/Mac).

### 6. Walk the user through the install dialog

Tell the user **verbatim**, substituting `DISPLAY_PATH` from step 5:

> The XPI is now at:
>
> ```
> <DISPLAY_PATH>
> ```
>
> In Zotero:
> 1. **Tools → Plugins** (Zotero 7) or **Tools → Add-ons** (Zotero 6 — but verify with the user; only Zotero 8.0+ is officially supported).
> 2. Click the gear icon (⚙) at the top right of that window.
> 3. Choose **Install Add-on From File…**.
> 4. Navigate to the path above and pick `zotron.xpi`.
> 5. Click **Install**, then **Restart Zotero** when prompted.
>
> Tell me when Zotero has restarted.

Then wait.

### 7. Verify

After the user confirms restart, ping again (step 2). Expected: `OK`.

If still `DOWN`:
- `Tools → Plugins` should list **Zotron** as enabled. If it's there but disabled, click **Enable**.
- Port 23119 connection refused? Zotero's HTTP server is off — `Edit → Settings → Advanced → Config Editor` → set `extensions.zotero.httpServer.enabled = true`, restart Zotero.
- "Not compatible" warning? Verify Zotero version is 8.0+; only that range is tested. Earlier versions may still work but are unsupported.

**Not the issue:** the `Edit → Settings → Advanced` checkbox **"Allow other applications on this computer to communicate with Zotero" / "Available at http://localhost:23119/api/"** binds to `httpServer.localAPI.enabled` and gates **only** Zotero's official `/api/*` REST endpoint. Custom plugin endpoints registered via `Zotero.Server.Endpoints[…]` (which is how `/zotron/rpc` works) bypass that check entirely — leaving the checkbox off is fine.

Once `system.ping` returns `OK`, run `zotron system.libraries` to print the user's library names. Hand off to the `zotero` skill.

## Skip when

- The user says they already installed the XPI manually → just run step 2 (ping) and confirm.
