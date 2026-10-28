# Week 9 Setup: Your Laptop Toolchain
**NET2008 DevOps · Algonquin College**

From Week 9 to Week 15 you do everything on **your own laptop**. You do not need a server, a lab machine, a cloud account or a Codespace. Do this setup **once**, before the Week 9 lecture. Install only what each week needs, in the order below. Week 10 has its own setup guide in the Week 10 folder. If you already have a tool, skip its step.

## What you install and when

| Tool | Needed in | What it is for |
|---|---|---|
| Terminal (Ubuntu on WSL 2 for Windows) | Week 9 | Where you type every command |
| Docker | Weeks 9 to 14 | Containers |
| Terraform | Week 11 | Infrastructure as code |
| Python virtual environment with Ansible | Week 12 | Configuration management |
| VirtualBox and Vagrant (optional) | Week 11 | Virtual machines (see the note in the Week 11 lab) |

## 1. Terminal

**Windows.** Open **PowerShell as administrator** (right-click Start, "Terminal (Admin)") and run:

```powershell
wsl --install -d Ubuntu
```

Restart the laptop when it asks. Ubuntu opens and asks you to create a Linux user name and password (the password does not show as you type). From now on, **use the Ubuntu app for every command in Weeks 9 to 14**, not PowerShell and not Git Bash. Keep your work in the Linux home folder (`~`), not under `/mnt/c`: it is much faster.

**macOS.** Use **Terminal**. Install Homebrew, the package manager used below:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Linux.** Use your terminal. The commands below assume Ubuntu or Debian. On another distribution use its package manager.

## 2. Docker (needed in Week 9)

**Windows.** Install **Docker Desktop** from <https://www.docker.com/products/docker-desktop/>. During setup keep **Use WSL 2** on. Start Docker Desktop. Then open Settings > Resources > WSL integration and switch on **Ubuntu**. Close and reopen the Ubuntu terminal.

**macOS.**

```bash
brew install --cask docker
```

Open **Docker** from Applications once and accept the prompts.

**Linux (Ubuntu or Debian).**

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

**Docker Desktop memory.** In Docker Desktop open Settings > Resources and give Docker **4 GB** of memory (6 GB on a 16 GB laptop). Kubernetes and the monitoring stack in later weeks need it.

## 3. Terraform (needed in Week 11)

**macOS.**

```bash
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
```

**Windows (Ubuntu terminal) and Ubuntu or Debian Linux.**

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
```

```bash
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

```bash
sudo apt update && sudo apt install -y terraform
```

**Check:**

```bash
terraform version
```

## 4. Ansible in a Python virtual environment (needed in Week 12)

Ansible runs on macOS, Linux and in the Ubuntu (WSL) terminal. It does **not** run in plain Windows PowerShell, which is why Windows students use Ubuntu.

On Ubuntu, Debian or WSL, install the tools first:

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
```

On macOS Python 3 comes with the developer tools (`xcode-select --install` if `python3` is missing).

Create the virtual environment (a private folder of Python packages) and install Ansible:

```bash
python3 -m venv ~/netops-venv  # Create the virtual environment in your home folder.
```

```bash
source ~/netops-venv/bin/activate  # Activate it. Your prompt shows (netops-venv). Do this in every new terminal before Week 12 work.
```

```bash
pip install ansible-core docker pyyaml  # Install Ansible, the Docker library it uses, and PyYAML.
```

```bash
ansible-galaxy collection install community.docker  # Install the Ansible collection that talks to Docker.
```

**Check:**

```bash
ansible --version
```

## 5. VirtualBox and Vagrant (optional, Week 11)

Virtual machines on a laptop depend on the processor. The Week 11 lab is written so that you finish **without** a virtual machine. Install these only if your laptop can run them, and only if you want to try `vagrant up`.

- **Windows 10 or 11 and Intel or AMD Linux:** VirtualBox (<https://www.virtualbox.org>) and Vagrant (<https://developer.hashicorp.com/vagrant/install>). VirtualBox can conflict with WSL 2 and Docker Desktop on some Windows laptops. If Docker stops working after you install it, uninstall VirtualBox. **Vagrant must be installed in Windows, not in Ubuntu.**
- **macOS with Intel:** the same two tools with Homebrew: `brew install --cask virtualbox vagrant`.
- **macOS with Apple silicon (M1 to M4):** VirtualBox does not run Intel boxes. Skip this section. The lab has a path for you.

## 6. Check everything with one command

Download [check_tools.py](check_tools.py) from the course repository (it is next to this file) and run it from the terminal you use for the course:

```bash
python3 check_tools.py  # Print OK or MISSING for each tool and the week that needs it.
```

You should have `OK` for every tool needed in Week 9 now. Run it again before each week. Tools needed later may show `MISSING` until you install them.

## If something goes wrong

| Message | Cause and fix |
|---|---|
| `WSL 2 requires an update to its kernel component` | Run `wsl --update` in PowerShell, then retry. |
| `Please enable the Virtual Machine Platform` or `virtualization is disabled` | Restart, open the BIOS or UEFI settings, and switch on **Virtualization** (Intel VT-x or AMD-V, often called SVM). |
| `docker: command not found` in Ubuntu on Windows | Docker Desktop is not running, or WSL integration is off for Ubuntu (Settings > Resources > WSL integration). |
| `permission denied` on `/var/run/docker.sock` | Run `sudo usermod -aG docker $USER`, then close and reopen the terminal. |
| `brew: command not found` after installing Homebrew | Run the two lines Homebrew printed at the end of its install ("Next steps"), then reopen the terminal. |
| `externally-managed-environment` when you run `pip` | You are not inside the virtual environment. Run `source ~/netops-venv/bin/activate` first. |
| Nothing works and you are stuck for more than 30 minutes | Stop. Write down the command and the full error message and bring them to class. |
