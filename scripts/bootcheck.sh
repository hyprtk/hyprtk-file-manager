#!/usr/bin/env bash
# Headless load check for the whole shell config.
#
# QA used to run only isolated QML tests, so a mistyped component in a dialog
# (TButton instead of DialogButton, 1.9.0) or a missing brace killed the app at
# startup without failing anything: `MainWindow.qml` declares the dialogs, so a
# component that cannot be created takes the entire configuration with it.
#
# This loads shell.qml exactly like the app does and requires the "Configuration
# Loaded" line with no error output. `timeout` killing a healthy shell (124) is
# the success case: it means the UI came up and stayed up.
set -uo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT

QT_QPA_PLATFORM=offscreen QS_APP_ID=hyprtk-file-manager \
    timeout 20 qs -p "$ROOT" >"$LOG" 2>&1
status=$?

if [ "$status" -ne 0 ] && [ "$status" -ne 124 ]; then
    cat "$LOG" >&2
    echo "bootcheck: qs exited with $status" >&2
    exit 1
fi

if ! grep -q 'Configuration Loaded' "$LOG"; then
    cat "$LOG" >&2
    echo "bootcheck: configuration never loaded" >&2
    exit 1
fi

if grep -q 'ERROR' "$LOG"; then
    cat "$LOG" >&2
    echo "bootcheck: errors while loading the configuration" >&2
    exit 1
fi

echo "bootcheck OK"
