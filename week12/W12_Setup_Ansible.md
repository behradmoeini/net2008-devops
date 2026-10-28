# Week 12 Setup: Ansible
**NET2008 DevOps · Algonquin College**

You do this setup **once**, before the Week 12 lecture. It assumes you finished the [Week 9 setup](../week09/W09_Setup_Your_Laptop.md): a working terminal (Ubuntu on WSL 2 for Windows) and Docker running.

## Ansible in a Python virtual environment

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
