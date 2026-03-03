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

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# Nová kontrola, jestli python skutečně umí vytvořit venv
can_venv() {
  "$PYTHON_BIN" -m venv --help >/dev/null 2>&1
}

apt_install_deps() {
  echo "[*] Updating apt and installing dependencies..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  # Instalujeme python3-venv explicitně, protože bez něj to na Debianu/Ubuntu nejde
  apt-get install -y git sudo "$PYTHON_BIN" "${PYTHON_BIN}-venv" "${PYTHON_BIN}-pip" ca-certificates curl
}

clone_or_update() {
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[*] Updating repo in $INSTALL_DIR"
    git -C "$INSTALL_DIR" fetch --all --prune
    git -C "$INSTALL_DIR" checkout main >/dev/null 2>&1 || true
    git -C "$INSTALL_DIR" pull --ff-only
  else
    echo "[*] Cloning repo to $INSTALL_DIR"
    # Pokud adresář existuje ale není to git (např. prázdný po selhání), smažeme ho
    [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
}

setup_venv() {
  echo "[*] Creating venv in $INSTALL_DIR/.venv"
  # Odstraníme starý pokus o venv, pokud existuje a je rozbitý
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
  fi
}

final_message() {
  echo
  echo "[*] Done."
  echo "Next:"
  echo "  1) Open a NEW shell (or: source /etc/profile.d/alex-shell-hook.sh)"
  echo "  2) Run: alex doctor"
  echo "  3) Run: alex auth    (to store OPENAI_API_KEY securely)"
  echo
}

main() {
  need_root

  # Změna logiky: instaluj dependencies, pokud chybí git NEBO pokud python neumí venv
  if ! have_cmd git || ! have_cmd "$PYTHON_BIN" || ! can_venv; then
    apt_install_deps
  fi

  clone_or_update
  setup_venv
  install_wrapper
  install_shell_hook

  echo
  echo "[*] Running: alex doctor"
  # Spouštíme přes wrapper, který jsme právě vytvořili
  /usr/local/bin/alex doctor || true

  final_message
}

main "$@"
