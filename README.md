# Alex CLI

Structured Linux CLI assistant (Debian-focused) with optional command execution, error log viewer, and basic systemd service diagnostics.

## Install (Debian)

### 1) Get the code
sudo apt update

sudo apt install -y git python3-venv python3-pip

git clone https://github.com/mrazeekk/alex-cli.git

cd alex-cli

python3 -m venv .venv

source .venv/bin/activate

pip install -e .
