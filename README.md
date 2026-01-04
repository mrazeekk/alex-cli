# Alex CLI

Structured Linux CLI assistant (Debian-focused) with optional command execution, error log viewer, and basic systemd service diagnostics.

## Install (Debian)

### 1) Get the code
sudo apt update && sudo apt install -y git

sudo git clone https://github.com/mrazeekk/alex-cli.git /opt/alex

sudo /opt/alex/scripts/install.sh

alex doctor

alex auth
