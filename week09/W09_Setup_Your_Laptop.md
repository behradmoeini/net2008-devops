# Week 9 Setup: Your Laptop Toolchain
**NET2008 DevOps · Algonquin College**

From Week 9 to Week 15 you do everything on **your own laptop**. You do not need a server, a lab machine, a cloud account or a Codespace. Do this setup **once**, before the Week 9 lecture. Install only what each week needs, in the order below. Weeks 10, 11 and 12 each have their own setup guide in their week folder. If you already have a tool, skip its step.

## How to install?

You can choose whether to install only on your terminal or use Docker desktop. In the following, and in the lecture, we will work with docker on terminal.

**Note:** You can install **Docker Desktop**(a gui version of Docker) from <https://www.docker.com/products/docker-desktop/>. During setup keep on. Start Docker Desktop. 

### Envronment

**Windows:** Open **PowerShell as administrator** (right-click Start, "Terminal (Admin)") and run:

```powershell
wsl --install -d Ubuntu
```

Restart the laptop when it asks. Ubuntu opens and asks you to create a Linux user name and password (the password does not show as you type). From now on, **use the Ubuntu app for every command in Weeks 9 to 14**, not PowerShell and not Git Bash. Keep your work in the Linux home folder (`~`), not under `/mnt/c`: it is much faster.

**macOS:** Use **Terminal**. Install Homebrew, the package manager used below:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Linux:** Use your terminal. The commands below assume Ubuntu or Debian. On another distribution use its package manager.

### Docker Engine

**macOS:**

```bash
brew install --cask docker
```

Open **Docker** from Applications once and accept the prompts.

**Linux (Ubuntu or Debian):**

```bash
curl -fsSL https://get.docker.com | sudo sh
```

```bash
sudo usermod -aG docker $USER
```

Close and reopen the terminal so the group change applies.

**Check (all systems):**

```bash
docker run --rm hello-world
```

You must see `Hello from Docker!`.

### Check everything with one command

Download [check_tools.py](check_tools.py) from the course repository (it is next to this file) and run it from the terminal you use for the course:

```bash
python3 check_tools.py  # Print OK or MISSING for each tool and the week that needs it.
```

You should have `OK` for the terminal and Docker now. Run it again before each week. Tools for later weeks show `MISSING` until you install them.

## If something goes wrong

| Message | Cause and fix |
|---|---|
| `WSL 2 requires an update to its kernel component` | Run `wsl --update` in PowerShell, then retry. |
| `Please enable the Virtual Machine Platform` or `virtualization is disabled` | Restart, open the BIOS or UEFI settings, and switch on **Virtualization** (Intel VT-x or AMD-V, often called SVM). |
| `docker: command not found` in Ubuntu on Windows | Docker Desktop is not running, or WSL integration is off for Ubuntu (Settings > Resources > WSL integration). |
| `permission denied` on `/var/run/docker.sock` | Run `sudo usermod -aG docker $USER`, then close and reopen the terminal. |
| `brew: command not found` after installing Homebrew | Run the two lines Homebrew printed at the end of its install ("Next steps"), then reopen the terminal. |
| Nothing works and you are stuck for more than 30 minutes | Stop. Write down the command and the full error message and bring them to class. |
