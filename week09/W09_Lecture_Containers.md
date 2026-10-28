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
## The big picture

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

One image can start many containers. Deleting a container does not delete the image. **Data written inside a container is lost when the container is deleted.** Volumes fix that (Step 9).

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
## Step 2. See the problem first

You will run one small Python script twice: on your laptop and in a container. The script prints a cow that says which Python and which operating system it runs on. It uses a third-party library, `cowsay`.

```bash
mkdir -p ~/container-practice/demo && cd ~/container-practice/demo  # Create the folder for this demo and move into it.
```

```bash
cat > demo.py <<'EOF'
import platform
import cowsay

cowsay.cow(f"I run on Python {platform.python_version()} on {platform.system()}")
EOF
```

Run it on your laptop first:

```bash
python3 demo.py  # Run the script with the Python installed on your laptop.
```

**You should see** `ModuleNotFoundError: No module named 'cowsay'`. This is the "works on my machine" problem: the script needs a library that your laptop does not have, and on a server it would be another missing library or another Python version.

Now run the same file in a container that has Python 3.11:

```bash
docker run --rm -e PIP_ROOT_USER_ACTION=ignore -v "$PWD":/app -w /app python:3.11-slim sh -c "pip install -q cowsay && python demo.py"  # Start a Python 3.11 container, mount this folder as /app, install the library inside the container, and run the script.
```

**You should see** a cow that says `I run on Python 3.11.x on Linux`. Your laptop is untouched: the library exists only inside that container, and the container is deleted when the script ends (`--rm`).

Run it again with a different Python version. Only the image tag changes:

```bash
docker run --rm -e PIP_ROOT_USER_ACTION=ignore -v "$PWD":/app -w /app python:3.12-slim sh -c "pip install -q cowsay && python demo.py"  # Same script, Python 3.12.
```

The cow now reports Python 3.12. One file, two Python versions, no installation on your laptop. The rest of this guide shows how to package, store and connect programs like this one.

---
## Step 3. Run your first container

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

**You should see** HTML that contains `Welcome to nginx!`.

---
## Step 4. Look inside a running container

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
## Step 5. Images and tags

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
## Step 6. Build your own image with a Dockerfile

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
## Step 7. Package a Python web app

Now you package a real program: a small Python web service that reports which container answered and counts the visits.

```bash
mkdir -p ~/container-practice/pyapp && cd ~/container-practice/pyapp  # Create the folder for the app and move into it.
```

```bash
cat > app.py <<'EOF'
import os
import platform
import socket

from flask import Flask, jsonify

app = Flask(__name__)
COUNT_FILE = os.environ.get("COUNT_FILE", "/data/count.txt")
GREETING = os.environ.get("GREETING", "Hello from Bytown NetOps")


def next_count():
    os.makedirs(os.path.dirname(COUNT_FILE), exist_ok=True)
    try:
        with open(COUNT_FILE) as f:
            count = int(f.read())
    except (FileNotFoundError, ValueError):
        count = 0
    count += 1
    with open(COUNT_FILE, "w") as f:
        f.write(str(count))
    return count


@app.get("/")
def index():
    return jsonify(
        message=GREETING,
        container=socket.gethostname(),
        python=platform.python_version(),
        visits=next_count(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
EOF
```

```bash
echo "flask==3.0.3" > requirements.txt  # List the libraries the app needs, with fixed versions.
```

```bash
cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV GREETING="Hello from Bytown NetOps"
EXPOSE 8000
CMD ["python", "app.py"]
EOF
```

Read the Dockerfile from the top: start from Python 3.11, work in `/app`, copy the library list, install the libraries, copy the program, set a default greeting, and start the program when a container starts. The library list is copied **before** the program on purpose: Docker caches each layer, so the slow `pip install` runs again only when `requirements.txt` changes.

```bash
docker build -t bytown-py:1.0 .  # Build the image. The first build downloads Flask and takes a minute.
```

```bash
docker run -d --name py1 -p 8090:8000 bytown-py:1.0  # Start a container from the image on host port 8090.
```

```bash
curl -s http://localhost:8090  # Call the app.
```

**You should see** JSON with `"message": "Hello from Bytown NetOps"`, the Python version, a `container` value (a short hex ID) and `"visits": 1`. Run the `curl` again: the visits go up.

One image starts many containers. Start a second one with a different greeting:

```bash
docker run -d --name py2 -p 8091:8000 -e GREETING="Hello from container two" bytown-py:1.0  # A second container from the same image. -e overrides the greeting.
```

```bash
curl -s http://localhost:8091  # The container ID and the greeting differ from py1, and the visits start at 1.
```

Each container has its own ID, its own environment and its own counter file. Now look at the logs and prove the build cache:

```bash
docker logs py1  # The app prints one line per request it received.
```

```bash
echo "# changed" >> app.py  # Change the program but not the library list.
```

```bash
docker build -t bytown-py:1.1 .  # Rebuild. The pip install step says CACHED, so this takes a second.
```

```bash
docker rm -f py1 py2  # Delete both containers. The images stay.
```

The built-in Flask server is fine for learning. A production service would use a server such as gunicorn.

---
## Step 8. Environment variables

```bash
docker run --rm -e SITE=ott-dc1 python:3.11-slim python -c "import os; print('site =', os.environ['SITE'])"  # Pass a variable with -e and read it inside the container.
```

**You should see** `site = ott-dc1`. Environment variables are how you configure a container without rebuilding the image. **Never put passwords in a Dockerfile**: anyone with the image can read them.

---
## Step 9. Volumes: keep data after the container is gone

First prove the problem. Start the app from Step 7 and call it three times:

```bash
docker run -d --name count1 -p 8090:8000 bytown-py:1.0  # Start the app with no volume.
```

```bash
curl -s http://localhost:8090 && curl -s http://localhost:8090 && curl -s http://localhost:8090  # Three visits.
```

**You should see** `"visits": 3` in the last answer. Now delete the container and start a new one:

```bash
docker rm -f count1  # Delete the container. The counter file inside it is gone with it.
```

```bash
docker run -d --name count2 -p 8090:8000 bytown-py:1.0  # Start a fresh container from the same image.
```

```bash
curl -s http://localhost:8090  # The counter starts again at 1.
```

```bash
docker rm -f count2  # Clean up.
```

Now do it with a **named volume**. The app writes its counter to `/data/count.txt`, so you mount the volume at `/data`:

```bash
docker volume create counter  # Create a volume managed by Docker.
```

```bash
docker run -d --name count3 -p 8090:8000 -v counter:/data bytown-py:1.0  # Start the app with the volume mounted at /data. -v NAME:PATH.
```

```bash
curl -s http://localhost:8090 && curl -s http://localhost:8090 && curl -s http://localhost:8090  # Three visits again.
```

```bash
docker rm -f count3  # Delete the container. The volume stays.
```

```bash
docker run -d --name count4 -p 8090:8000 -v counter:/data bytown-py:1.0  # A brand new container, the same volume.
```

```bash
curl -s http://localhost:8090  # The counter continues.
```

**You should see** `"visits": 4`. The container is new, the data is not. You can also read the file from a different container:

```bash
docker run --rm -v counter:/data alpine cat /data/count.txt  # Mount the same volume in a throw-away container and print the file.
```

```bash
docker rm -f count4  # Delete the app container.
```

```bash
docker volume ls  # List volumes.
```

```bash
docker volume rm counter  # Delete the volume (this deletes the data).
```

A **bind mount** (`-v /path/on/your/computer:/path/in/container`) mounts one of your own folders. Use it in development. Use named volumes for data that the container owns.

---
## Step 10. Networks: containers talk by name

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
## Step 11. Docker Compose: many containers, one file

Typing five long `docker run` commands is slow and easy to get wrong. **Compose** describes the whole system in one YAML file.

```bash
mkdir -p ~/container-practice/stack && cd ~/container-practice/stack  # Create a folder for the stack and move into it.
```

```bash
cat > compose.yaml <<'EOF'
services:
  app:
    build: ../pyapp
    image: bytown-py:compose
    ports:
      - "8083:8000"
    environment:
      GREETING: "Hello from Compose"
    volumes:
      - counter:/data
  tools:
    image: alpine:3.20
    command: ["sleep", "3600"]
volumes:
  counter:
EOF
```

YAML uses **spaces** for indentation (never tabs). Compose creates a network for the stack, so `tools` can reach `app` by the name `app`. The `build` line tells Compose to build the image from the Python app folder of Step 7.

```bash
docker compose up -d --build  # Build the app image, create the network and the volume, and start both containers.
```

```bash
docker compose ps  # List the containers of this stack.
```

```bash
curl -s http://localhost:8083  # Call the app from your laptop through the published port.
```

```bash
docker compose exec tools wget -qO- http://app:8000  # From the tools container, call the app by its service name. Visits go up, because both calls reach the same app.
```

```bash
docker compose logs app  # Show the logs of one service: you see both requests.
```

```bash
docker compose down -v  # Stop and delete the containers, the network and (with -v) the volumes.
```

| Command | What it does |
|---|---|
| `docker compose up -d --build` | Build if needed, then create and start everything |
| `docker compose ps` | Show the containers |
| `docker compose logs SERVICE` | Show logs |
| `docker compose exec SERVICE CMD` | Run a command in a service |
| `docker compose down` | Stop and delete (add `-v` to delete volumes) |
| `docker compose config` | Check the file and print it. Run it when Compose complains. |

---
## Step 12. Clean up

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
