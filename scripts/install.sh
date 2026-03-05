#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/mrazeekk/alex-cli.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/alex}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

need_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root (use sudo)."
    exit 1
  fi
}

install_system_deps() {
  echo "[*] Ensuring all system dependencies are installed..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y \
    git \
    sudo \
    "$PYTHON_BIN" \
    "${PYTHON_BIN}-venv" \
    "${PYTHON_BIN}-pip" \
    ca-certificates \
    curl \
    build-essential
}

clone_or_update() {
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[*] Updating repo in $INSTALL_DIR"
    git -C "$INSTALL_DIR" fetch --all --prune
    git -C "$INSTALL_DIR" checkout main >/dev/null 2>&1 || true
    git -C "$INSTALL_DIR" pull --ff-only
  else
    echo "[*] Cloning repo to $INSTALL_DIR"
    [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
}

setup_venv() {
  echo "[*] Creating fresh venv in $INSTALL_DIR/.venv"
  rm -rf "$INSTALL_DIR/.venv"
  
  "$PYTHON_BIN" -m venv "$INSTALL_DIR/.venv"
  "$INSTALL_DIR/.venv/bin/pip" install -U pip
  "$INSTALL_DIR/.venv/bin/pip" install -e "$INSTALL_DIR"
}

install_wrapper() {
  echo "[*] Installing /usr/local/bin/alex wrapper"
  cat > /usr/local/bin/alex <<WRAP
#!/usr/bin/env bash
set -euo pipefail
exec "$INSTALL_DIR/.venv/bin/alex" "\$@"
WRAP
  chmod +x /usr/local/bin/alex
}

install_shell_hook() {
  if [ -f "$INSTALL_DIR/scripts/alex-shell-hook.sh" ]; then
    echo "[*] Installing shell hook to /etc/profile.d/alex-shell-hook.sh"
    cp -f "$INSTALL_DIR/scripts/alex-shell-hook.sh" /etc/profile.d/alex-shell-hook.sh
    chmod 644 /etc/profile.d/alex-shell-hook.sh
  else
    echo "[!] Warning: scripts/alex-shell-hook.sh not found in repo."
  fi
}

final_message() {
  echo
  echo "--- INSTALLATION COMPLETE ---"
  echo "[*] Shell hook installed to /etc/profile.d/alex-shell-hook.sh"
  echo "[*] To apply changes IMMEDIATELY in this terminal, run:"
  echo "    source /etc/profile.d/alex-shell-hook.sh"
  echo
  echo "[*] Otherwise, just open a new terminal window."
  echo "[*] Then run: alex doctor"
  echo "-----------------------------"
}

main() {
  need_root
  install_system_deps
  clone_or_update
  setup_venv
  install_wrapper
  install_shell_hook

  echo "[*] Running: alex doctor"
  /usr/local/bin/alex doctor || true

  final_message
}

main "$@"
