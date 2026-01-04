import os
import platform

def get_system_info() -> str:
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    distro = " ".join(platform.freedesktop_os_release().get("PRETTY_NAME", "").split()) \
        if hasattr(platform, "freedesktop_os_release") else ""
    arch = platform.machine()
    user = os.getenv("USER") or os.getenv("LOGNAME") or "unknown"
    hostname = platform.node()

    lines = []
    lines.append(f"OS: {os_name} {os_release}")
    if distro:
        lines.append(f"Distro: {distro}")
    lines.append(f"Kernel: {os_version}")
    lines.append(f"Arch: {arch}")
    lines.append(f"Hostname: {hostname}")
    lines.append(f"User: {user}")
    return "\n".join(lines)
