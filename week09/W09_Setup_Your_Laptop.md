# Week 9 Setup: Your Laptop Toolchain
**NET2008 DevOps · Algonquin College**

From Week 9 to Week 15 you do everything on **your own laptop**. You do not need a server, a lab machine, a cloud account or a Codespace. Do this setup **once**, before the Week 9 lecture. Install only what each week needs, in the order below. Weeks 10, 11 and 12 each have their own setup guide in their week folder. If you already have a tool, skip its step.

## How to install

Download and install **Docker Desktop** from <https://www.docker.com/products/docker-desktop/>. It includes Docker Engine, the `docker` command and Docker Compose.

Open Docker Desktop, accept the prompts, and wait until it says it is running. Keep it running whenever you use Docker.

**Linux users:** For linux users, you can choose to install Docker Engine by following <https://docs.docker.com/engine/install>, then run `sudo usermod -aG docker $USER` and reopen the terminal.

### How to Check

In a terminal run:

```bash
docker run --rm hello-world
```

You must see `Hello from Docker!`.
