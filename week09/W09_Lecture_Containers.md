# Week 9 Lecture: Containers with Docker
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop**. You need nothing else: no server, no lab machine, no cloud account. Set up your laptop first with [W09_Setup_Your_Laptop.md](W09_Setup_Your_Laptop.md) (about 30 minutes, done once for the rest of the course).

**Windows students:** from this week on, work in the **Ubuntu (WSL 2) terminal**, not in PowerShell or Git Bash. The commands are then identical to Linux and macOS. The setup guide shows how.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- **You should see** shows roughly what the terminal prints. IDs and times will differ.
- Do the steps in order. Each step builds on the one before.
- All practice work happens in one folder, `~/container-practice`.

---
## The big picture: read this first

### The problem

Your Python script runs on your laptop. It fails on the server: wrong Python version, a missing library, a different operating system. "It works on my machine" is the oldest problem in operations. A **container** solves it: you ship the program **together with everything it needs**, and it runs the same everywhere.

### Container or virtual machine?

| | Virtual machine | Container |
|---|---|---|
| Contains | A full operating system, kernel included | Only the program and its libraries |
| Shares | Nothing (hardware is emulated) | The kernel of the host |
| Size | Gigabytes | Megabytes |
| Starts in | Minutes | Seconds or less |
| Isolation | Strong | Good, but weaker than a VM |

A container is not a small VM. It is a normal process that the kernel isolates, so it sees its own files, its own network and its own process list.

### Seven words to know

| Word | Meaning |
|---|---|
| **Image** | A read-only package: files, libraries and the command to start. Like a class. |
| **Container** | A running (or stopped) instance of an image. Like an object. |
| **Registry** | A server that stores images. Docker Hub (`hub.docker.com`) is the public one. |
| **Dockerfile** | A text recipe that builds an image, one instruction per line |
| **Volume** | Storage that lives outside the container, so data survives when the container is deleted |
| **Network** | A virtual network that containers join to talk to each other by name |
| **Compose** | A YAML file that describes several containers and starts them together |

### Image and container

```text
Dockerfile  --docker build-->  image  --docker run-->  container
 (recipe)                      (package)               (running process)
```

One image can start many containers. Deleting a container does not delete the image. **Data written inside a container is lost when the container is deleted.** Volumes fix that (Step 7).

---
## Step 1. Check that Docker works

Docker must be installed and running on your laptop (see the setup guide). On Windows and macOS start **Docker Desktop** and wait until it says it is running. On Linux the Docker service runs in the background. Then:

```bash
docker --version  # Print the Docker version. Any recent version is fine.
```

```bash
docker run --rm hello-world  # Download a tiny test image, run it once, and delete the container afterwards.
```

**You should see** a message that starts with `Hello from Docker!`. If you see `Cannot connect to the Docker daemon`, Docker is not running: start Docker Desktop (or `sudo systemctl start docker` on Linux).

Create the practice folder:

```bash
mkdir -p ~/container-practice && cd ~/container-practice  # Create the practice folder and move into it.
```

---
## Step 2. Run your first container

```bash
docker run -d --name web1 -p 8081:80 nginx:alpine  # Start the nginx web server in the background (-d), name it web1, and map port 8081 of your computer to port 80 inside the container.
```

Read the command in pieces:

| Part | Meaning |
|---|---|
| `docker run` | Create and start a container |
| `-d` | **d**etached: run in the background |
| `--name web1` | Give the container a name you can use later |
| `-p 8081:80` | **p**ublish: `HOST_PORT:CONTAINER_PORT` |
| `nginx:alpine` | The image. `nginx` is the name, `alpine` is the **tag** (a version label, here a small Linux base) |

The first time, Docker downloads the image. Then test it:

```bash
curl http://localhost:8081  # Ask the web server for its page.
```

**You should see** HTML that contains `Welcome to nginx!`. In Codespaces you can also open the **Ports** tab and click the globe next to port 8081.

---
## Step 3. Look inside a running container

```bash
docker ps  # List running containers.
```

```bash
docker logs web1  # Print what the container wrote to its output (the web server's access log).
```

```bash
docker exec web1 cat /etc/os-release  # Run one command inside the container. It is Alpine Linux.
```

```bash
docker exec -it web1 sh  # Open an interactive shell inside the container. Type exit to leave.
```

Inside that shell try `ls /usr/share/nginx/html` and `ps`, then type `exit`. You only see the container's own files and processes.

```bash
docker stop web1  # Stop the container. It still exists.
```

```bash
docker ps -a  # List all containers, including stopped ones. web1 shows "Exited".
```

```bash
docker start web1  # Start the same container again.
```

```bash
docker rm -f web1  # Delete the container (-f stops it first). The image stays on disk.
```

| Command | What it does |
|---|---|
| `docker ps` / `docker ps -a` | Running / all containers |
| `docker logs NAME` | Show the output of a container |
| `docker exec NAME CMD` | Run a command inside a running container |
| `docker stop NAME` / `docker start NAME` | Stop / start |
| `docker rm NAME` | Delete a stopped container (`-f` forces) |

---
## Step 4. Images and tags

```bash
docker images  # List the images on your computer.
```

```bash
docker pull python:3.11-slim  # Download an image without running it. 3.11-slim is Python 3.11 on a small Debian.
```

```bash
docker run --rm python:3.11-slim python --version  # Run one command in a new container. --rm deletes the container when it ends.
```

```bash
docker history nginx:alpine  # Show the layers that make up the image. Each Dockerfile line becomes a layer.
```

An image name has the form `NAME:TAG`. **Always use a tag.** If you leave it out, Docker uses `latest`, which changes over time and makes your builds unpredictable.

---
## Step 5. Build your own image with a Dockerfile

Create a small website and a Dockerfile in a new folder:

```bash
mkdir -p ~/container-practice/site && cd ~/container-practice/site  # Create the folder for this image and move into it.
```

```bash
cat > index.html <<'EOF'
<h1>Bytown NetOps</h1>
<p>Built by me, served from a container.</p>
EOF
```

```bash
cat > Dockerfile <<'EOF'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
EOF
```

The three lines of the Dockerfile:

| Instruction | Meaning |
|---|---|
| `FROM nginx:alpine` | Start from this existing image |
| `COPY index.html ...` | Copy a file from your folder into the image |
| `EXPOSE 80` | Document that the program listens on port 80 (it does not publish it) |

Build and run it:

```bash
docker build -t site:1.0 .  # Build an image from the Dockerfile in this folder (.) and name it site:1.0.
```

```bash
docker run -d --name site1 -p 8082:80 site:1.0  # Start a container from your image on port 8082.
```

```bash
curl http://localhost:8082  # You should see your own HTML.
```

Change the page and build version 1.1. Docker reuses unchanged layers, so this is fast:

```bash
echo "<p>Version 1.1</p>" >> index.html  # Add a line to the page.
```

```bash
docker build -t site:1.1 .  # Build again. Lines that did not change say CACHED.
```

```bash
docker rm -f site1  # Delete the old container.
```

Other Dockerfile instructions you will use in the lab:

| Instruction | Meaning |
|---|---|
| `ARG NAME` | A value you pass at build time with `--build-arg NAME=value` |
| `ENV NAME=value` | An environment variable inside the container |
| `LABEL key=value` | Metadata stored on the image |
| `WORKDIR /app` | Set the working folder for the next instructions |
| `RUN command` | Run a command **while building** (install packages) |
| `CMD ["cmd", "arg"]` | The command that runs **when the container starts** |

---
## Step 6. Environment variables

```bash
docker run --rm -e SITE=ott-dc1 python:3.11-slim python -c "import os; print('site =', os.environ['SITE'])"  # Pass a variable with -e and read it inside the container.
```

**You should see** `site = ott-dc1`. Environment variables are how you configure a container without rebuilding the image. **Never put passwords in a Dockerfile**: anyone with the image can read them.

---
## Step 7. Volumes: keep data after the container is gone

First prove the problem:

```bash
docker run -d --name tmp1 nginx:alpine  # Start a throw-away container with no volume.
```

```bash
docker exec tmp1 sh -c "echo hello > /usr/share/nginx/html/note.txt"  # Write a file inside the container.
```

```bash
docker rm -f tmp1  # Delete the container. The file is gone with it.
```

Now do it with a **named volume**:

```bash
docker volume create webdata  # Create a volume managed by Docker.
```

```bash
docker run -d --name vol1 -v webdata:/usr/share/nginx/html nginx:alpine  # Mount the volume at the folder nginx serves. -v NAME:PATH.
```

```bash
docker exec vol1 sh -c "echo saved > /usr/share/nginx/html/note.txt"  # Write a file into the volume.
```

```bash
docker rm -f vol1  # Delete the container. The volume stays.
```

```bash
docker run --rm -v webdata:/data alpine cat /data/note.txt  # Mount the same volume in a new container and read the file. It is still there.
```

**You should see** `saved`.

```bash
docker volume ls  # List volumes.
```

```bash
docker volume rm webdata  # Delete the volume (this deletes the data).
```

A **bind mount** (`-v /path/on/your/computer:/path/in/container`) mounts one of your own folders. Use it in development. Use named volumes for data that the container owns.

---
## Step 8. Networks: containers talk by name

By default a container can reach the internet but not find other containers by name. A **user-defined network** adds name lookup (DNS).

```bash
docker network create labnet  # Create a user-defined network.
```

```bash
docker run -d --name backend --network labnet nginx:alpine  # Start a web server on that network. It has no published port.
```

```bash
docker run --rm --network labnet curlimages/curl curl -s http://backend  # A second container on the same network reaches the first one by its NAME.
```

**You should see** the nginx welcome page. Container names are host names inside a user-defined network. Nothing outside can reach `backend`, because you did not publish a port. This is how you keep a database private and expose only the web server.

```bash
docker rm -f backend  # Clean up the container.
```

```bash
docker network rm labnet  # Clean up the network.
```

---
## Step 9. Docker Compose: many containers, one file

Typing five long `docker run` commands is slow and easy to get wrong. **Compose** describes the whole system in one YAML file.

```bash
mkdir -p ~/container-practice/stack && cd ~/container-practice/stack  # Create a folder for the stack and move into it.
```

```bash
cat > compose.yaml <<'EOF'
services:
  web:
    image: nginx:alpine
    ports:
      - "8083:80"
    volumes:
      - pages:/usr/share/nginx/html
  tools:
    image: alpine:3.20
    command: ["sleep", "3600"]
volumes:
  pages:
EOF
```

YAML uses **spaces** for indentation (never tabs). Compose creates a network for the stack, so `tools` can reach `web` by the name `web`.

```bash
docker compose up -d  # Create the network, the volume and both containers, and start them.
```

```bash
docker compose ps  # List the containers of this stack.
```

```bash
docker compose exec tools wget -qO- http://web  # From the tools container, fetch the web container's page by name.
```

```bash
docker compose logs web  # Show the logs of one service.
```

```bash
docker compose down -v  # Stop and delete the containers, the network and (with -v) the volumes.
```

| Command | What it does |
|---|---|
| `docker compose up -d` | Create and start everything |
| `docker compose ps` | Show the containers |
| `docker compose logs SERVICE` | Show logs |
| `docker compose exec SERVICE CMD` | Run a command in a service |
| `docker compose down` | Stop and delete (add `-v` to delete volumes) |
| `docker compose config` | Check the file and print it. Run it when Compose complains. |

---
## Step 10. Clean up

```bash
docker ps -a  # Check what is still around.
```

```bash
docker system df  # Show how much disk space images, containers and volumes use.
```

```bash
docker image prune -f  # Delete unused dangling images (-f skips the confirmation).
```

---
## If something goes wrong

| Message | Cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running. Start Docker Desktop, or `sudo systemctl start docker`. |
| `port is already allocated` | Another container or program uses that host port. Run `docker ps`, remove the old container, or choose another port. |
| `The container name "/web1" is already in use` | An old container has that name. `docker rm -f web1`. |
| `pull access denied` or `not found` | Typo in the image name or tag. Check it on <https://hub.docker.com>. |
| `permission denied ... docker.sock` (Linux, WSL) | Add yourself to the group: `sudo usermod -aG docker $USER`, then close and reopen the terminal. |
| `yaml: line N: found character that cannot start any token` | A tab in a YAML file. Use spaces. |
| Windows: `docker: command not found` in Ubuntu | Docker Desktop > Settings > Resources > WSL integration: switch on your Ubuntu distribution. |
| `no matching manifest for linux/arm64` (Apple silicon) | The image has no ARM build. Add `--platform linux/amd64` to `docker run` or `docker pull`. |
| Everything is very slow or containers get killed | Docker Desktop has too little memory. Settings > Resources: give it 4 GB. |
| Nothing at `http://localhost:PORT` | Check `docker ps` shows the port mapping and that you used the **host** port (left side). |

## Summary

- A container is a normal process with its own files and network. An image is the package it starts from.
- `docker run -d --name N -p HOST:CONTAINER IMAGE:TAG` starts a service. `docker ps`, `logs`, `exec`, `stop`, `rm` manage it.
- A Dockerfile builds an image. Use tags, put changing lines last, never store secrets in it.
- Volumes keep data. User-defined networks give containers name lookup. Compose describes a whole stack in one YAML file.

**Next:** the Week 9 lab (graded) builds, runs, stores and composes a small web service with your own seed.
