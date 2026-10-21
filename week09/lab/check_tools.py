#!/usr/bin/env python3
"""NET2008 laptop toolchain check.

Run it in the terminal you use for the course (Terminal on macOS, your Linux
terminal, or the Ubuntu app on Windows):

    python3 check_tools.py

It only reads version numbers. It installs and changes nothing.
"""
import platform
import shutil
import subprocess
import sys

# (tool name, command to run, needed in week, required for that week's lab)
TOOLS = [
    ("Python 3.10 or newer", [sys.executable, "--version"], 9, True),
    ("Git", ["git", "--version"], 9, True),
    ("Docker client", ["docker", "--version"], 9, True),
    ("Docker engine running", ["docker", "info", "--format", "{{.ServerVersion}}"], 9, True),
    ("Docker Compose", ["docker", "compose", "version", "--short"], 9, True),
    ("kubectl", ["kubectl", "version", "--client"], 10, True),
    ("minikube", ["minikube", "version", "--short"], 10, True),
    ("Terraform", ["terraform", "version"], 11, True),
    ("Vagrant (optional)", ["vagrant", "--version"], 11, False),
    ("VirtualBox (optional)", ["VBoxManage", "--version"], 11, False),
    ("Ansible", ["ansible", "--version"], 12, True),
    ("GitHub CLI (optional)", ["gh", "--version"], 13, False),
]


def first_line(text):
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:70]
    return ""


def main():
    print("System: %s %s (%s)" % (platform.system(), platform.release(), platform.machine()))
    if sys.version_info < (3, 10):
        print("Your Python is older than 3.10. Install a newer one.")
    print()
    print("%-26s %-6s %-5s %s" % ("Tool", "Week", "State", "Detail"))
    missing = 0
    for name, cmd, week, required in TOOLS:
        if shutil.which(cmd[0]) is None:
            state, detail = "MISSING", "not installed or not on PATH"
        else:
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                out = first_line(p.stdout) or first_line(p.stderr)
                if p.returncode == 0:
                    state, detail = "OK", out
                else:
                    state, detail = "FAIL", out or "the command returned an error"
            except (OSError, subprocess.SubprocessError) as exc:
                state, detail = "FAIL", str(exc)[:70]
        if state != "OK" and required:
            missing += 1
        print("%-26s %-6s %-7s %s" % (name, week, state, detail))
    print()
    if missing == 0:
        print("Everything required is ready.")
    else:
        print("%d required item(s) not ready. Install them before the week shown in the Week column." % missing)
    if platform.system() == "Windows":
        print("Note: you are in native Windows. Use the Ubuntu (WSL 2) terminal for Weeks 9 to 14.")


if __name__ == "__main__":
    main()
