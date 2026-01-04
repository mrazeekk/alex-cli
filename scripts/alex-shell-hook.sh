# scripts/alex-shell-hook.sh
# Log last failed command into /tmp/alex_last_error.txt in a simple format.

__alex_log_error() {
  local exit_code=$?
  # log only if non-zero and interactive
  [[ $exit_code -eq 0 ]] && return
  [[ -z "$PS1" ]] && return

  local ts
  ts=$(date "+%Y-%m-%d %H:%M:%S")

  # BASH_COMMAND is the currently executing command (works well for this use-case)
  echo "---- $ts ----" >> /tmp/alex_last_error.txt
  echo "Exit code: $exit_code | Command: $BASH_COMMAND" >> /tmp/alex_last_error.txt
  echo >> /tmp/alex_last_error.txt
}

# append to existing trap if any
trap '__alex_log_error' ERR
set -o errtrace
