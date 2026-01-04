__alex_log_error() {
  local exit_code=$?
  [[ $exit_code -eq 0 ]] && return
  [[ -z "$PS1" ]] && return

  local ts
  ts=$(date "+%Y-%m-%d %H:%M:%S")

  echo "---- $ts ----" >> /tmp/alex_last_error.txt
  echo "Exit code: $exit_code | Command: $BASH_COMMAND" >> /tmp/alex_last_error.txt
  echo >> /tmp/alex_last_error.txt
}

trap '__alex_log_error' ERR
set -o errtrace
