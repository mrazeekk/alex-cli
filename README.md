# 🤖 Alex CLI (v0.2.0)
> **Your intelligent Debian assistant that understands your terminal, monitors for errors, and keeps your system safe.**

Alex is a structured CLI assistant built for Debian-based systems. It doesn't just run commands—it understands your environment, captures failed execution details in real-time via shell hooks, and provides AI-powered diagnostics.

## ✨ Key Features

* **🔍 Smart Service Diagnostics:** Unlike basic status checks, Alex performs iterative investigations. It probes logs, ports, and configs until it finds the root cause of a service failure.
* **🧠 Real-time Error Analysis:** With a native shell hook, Alex automatically logs failed commands to `/tmp/alex_last_error.txt`. Run `alex error` to get an instant explanation and fix.
* **🛡️ Built-in Safety Guardrails:** Alex protects you from dangerous operations. It identifies high-risk commands (like destructive `rm`, `mkfs`, or unauthorized redirects) and requires manual confirmation.
* **🏥 Comprehensive System Doctor:** Verify your environment, OpenAI key status, and file permissions at a glance.
* **💸 Token Efficient:** Designed to be lightweight. You can run Alex for weeks on a basic $5 OpenAI credit; the model usage is optimized to save you money.

## 📸 Showcasing Alex

### The "Doctor" Check
Keep your environment healthy. Alex checks everything from Python versions to shell hook status.
![Alex Doctor](docs/screenshots/doctor.png)

### Safety First
Alex identifies high-risk commands and forces a manual confirmation before execution.
![Safety Guardrails](docs/screenshots/safety.png)

### Intelligent Service Diagnosis
Diving deep into systemd units to explain why a service isn't behaving.
![Service Diagnosis](docs/screenshots/service.png)

## 🚀 Installation

```bash
sudo apt update && sudo apt install -y git && \
sudo git clone https://github.com/mrazeekk/alex-cli.git /opt/alex && \
sudo /opt/alex/scripts/install.sh
```
After installation, restart your terminal or run source /etc/profile.d/alex-shell-hook.sh.

## 🔑 Setting up OpenAI API
To use the AI features, you need an OpenAI API key. Even a minimum $5 deposit is more than enough for long-term use.

Get your Key: Go to platform.openai.com and create a new API key.

Authorize Alex: Run:
```bash
alex auth
```
Alex will securely store it in ~/.config/alex/openai.env with restricted (600) permissions.

## 🛠️ Usage Examples
Explain Last Terminal Error
Simply run "alex error" after any command fails. Alex pulls the context and tells you how to fix it.

Ask for Help (No quotes needed!)
```bash
alex run show me the top 5 largest files in /var/log --apply
```
Alex suggests the safest command and helps you execute it after your approval.

Don't be afraid of use "alex --help", "alex run --help"... And so on. It is properly explained.

## ⚙️ Configuration
You can change you settings by calling "alex config". You can change the language (English/Czech), AI model, or response verbosity.
