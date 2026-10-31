# Week 9 Setup: Your Laptop Toolchain
**NET2008 DevOps · Algonquin College**

From Week 9 to Week 15 you do everything on **your own laptop**. You do not need a server, a lab machine, a cloud account or a Codespace. Do this setup **once**, before the Week 9 lecture. Install only what each week needs, in the order below. Weeks 10, 11 and 12 each have their own setup guide in their week folder. If you already have a tool, skip its step.

## How to install

Download and install **Docker Desktop** from <https://www.docker.com/products/docker-desktop/>. It includes Docker Engine, the `docker` command and Docker Compose.

- **Windows:** run the installer and keep **Use WSL 2** switched on. Restart if it asks.
- **macOS:** choose **Apple chip** or **Intel chip** to match your Mac (Apple menu > About This Mac). Drag Docker to Applications.

Open Docker Desktop, accept the prompts, and wait until it says it is running. Keep it running whenever you use Docker.

**Linux users:** do not use Docker Desktop. Install Docker Engine by following <https://docs.docker.com/engine/install>, then run `sudo usermod -aG docker $USER` and reopen the terminal.

### Check

In a terminal run:

```bash
docker run --rm hello-world
```

You must see `Hello from Docker!`.

## If something goes wrong

| Message | Cause and fix |
|---|---|
| `WSL 2 requires an update to its kernel component` | Run `wsl --update` in PowerShell, then retry. |
| `Please enable the Virtual Machine Platform` or `virtualization is disabled` | Restart, open the BIOS or UEFI settings, and switch on **Virtualization** (Intel VT-x or AMD-V, often called SVM). |
| `docker: command not found` in Ubuntu on Windows | Docker Desktop is not running, or WSL integration is off for Ubuntu (Settings > Resources > WSL integration). |
| `permission denied` on `/var/run/docker.sock` | Run `sudo usermod -aG docker $USER`, then close and reopen the terminal. |
| Nothing works and you are stuck for more than 30 minutes | Stop. Write down the command and the full error message and bring them to class. |
