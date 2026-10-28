# Week 9 Lab: Bytown Web Service in Containers
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). It is the hands-on companion to the Week 9 lecture. You package a small web page as an image, run it, give it storage, and run it behind a proxy with Docker Compose. Everything runs on **your own laptop**.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Docker must be running (see [W09_Setup_Your_Laptop.md](../W09_Setup_Your_Laptop.md)).
- Do the parts in order. Each part builds on the one before.
- Use the **exact** names, tags and file names given here. The self-check and your instructor look for them.
- Every command is one grey box. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Search the error message. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

Your numbers come from your student ID, so your ports and names are different from everyone else's. **Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`.

Replace `17` with **your** seed (a number from 1 to 36), then run:

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

```bash
echo "My seed is $SEED"  # Print the seed to check it.
```

```bash
docker run --rm hello-world  # Check that Docker works. You must see "Hello from Docker!".
```

```bash
mkdir -p ~/bytown-containers/evidence && cd ~/bytown-containers  # Create the lab folder, and a folder for the proof of your work, and move into it.
```

```bash
git init -b main  # Make the lab folder a Git repository, as in Week 6.
```

**If you close the terminal**, the variable is lost. Open a new terminal, run `export SEED=...` again and `cd ~/bytown-containers`.

---
## Part 1. Run and inspect a container (3 points)

Your web server listens on host port `8000 + seed`.

```bash
docker run -d --name web-$SEED -p $((8000 + SEED)):80 nginx:alpine  # Start nginx. The container is named web-<seed>.
```

```bash
curl -s http://localhost:$((8000 + SEED)) | head -5  # Ask for the page. You should see the start of the nginx welcome page.
```

```bash
docker logs web-$SEED > evidence/part1-logs.txt  # Save the container's log as proof that your request reached it.
```

```bash
cat evidence/part1-logs.txt | tail -3  # Read the last lines. One of them must contain GET / HTTP/1.1.
```

Delete the container:

```bash
docker rm -f web-$SEED  # Stop and delete the container.
```

---
## Part 2. Build your own image (6 points)

Create the page. It shows your seed:

```bash
mkdir -p web && printf '<h1>Bytown NetOps</h1>\n<p>Seed: %s</p>\n' "$SEED" > web/index.html  # Create the web folder and a page with your seed in it.
```

```bash
cat web/index.html  # Check the file.
```

Create the Dockerfile. It must use the build argument `SEED` and store it as a label:

```bash
cat > web/Dockerfile <<'EOF'
FROM nginx:alpine
ARG SEED
LABEL org.bytown.seed=$SEED
LABEL org.bytown.course=NET2008
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
EOF
```

```bash
docker build --build-arg SEED=$SEED -t bytown-web:1.0 ./web  # Build the image bytown-web:1.0 and pass your seed to the build.
```

```bash
docker run -d --name bytown-web-$SEED -p $((8100 + SEED)):80 bytown-web:1.0  # Start a container from your image on host port 8100 + seed.
```

```bash
curl -s http://localhost:$((8100 + SEED)) | tee evidence/part2-curl.txt  # Fetch the page, show it, and save it. You must see your seed.
```

```bash
docker image inspect bytown-web:1.0 > evidence/part2-inspect.json  # Save the image details. They contain your label.
```

Now build **version 1.1** with one more line on the page. You need this image again in Week 10:

```bash
echo "<p>Version 1.1</p>" >> web/index.html  # Add a line to the page.
```

```bash
docker build --build-arg SEED=$SEED -t bytown-web:1.1 ./web  # Build the second version. Unchanged steps say CACHED.
```

```bash
docker images bytown-web  # You must see two rows: 1.0 and 1.1.
```

```bash
docker rm -f bytown-web-$SEED  # Delete the running container. Keep both images.
```

---
## Part 3. A volume keeps your data (4 points)

The volume is named `bytown-data-<seed>`.

```bash
docker volume create bytown-data-$SEED  # Create the volume.
```

```bash
docker run -d --name vol-a-$SEED -v bytown-data-$SEED:/usr/share/nginx/html nginx:alpine  # Start a container that serves the volume's content.
```

```bash
docker exec vol-a-$SEED sh -c "echo seed=$SEED > /usr/share/nginx/html/status.txt"  # Write a file into the volume.
```

Delete the container. The data must survive:

```bash
docker rm -f vol-a-$SEED  # Delete the container.
```

```bash
docker run -d --name vol-b-$SEED -p $((8200 + SEED)):80 -v bytown-data-$SEED:/usr/share/nginx/html nginx:alpine  # Start a NEW container on the same volume, on host port 8200 + seed.
```

```bash
curl -s http://localhost:$((8200 + SEED))/status.txt | tee evidence/part3-curl.txt  # The new container serves the file the old one wrote. You must see seed=<your seed>.
```

```bash
docker rm -f vol-b-$SEED  # Delete the container. Keep the volume.
```

---
## Part 4. A stack with Compose (5 points)

You build a stack of two containers: your web image and a proxy in front of it. Only the **proxy** is reachable from your laptop. The web container has no published port.

```bash
mkdir -p stack/proxy && cd stack  # Create the stack folder and move into it.
```

The proxy configuration forwards every request to the service named `web`:

```bash
cat > proxy/default.conf <<'EOF'
server {
    listen 80;
    location / {
        proxy_pass http://web:80;
    }
}
EOF
```

The values that change per student live in a `.env` file that Compose reads by itself:

```bash
printf 'SEED=%s\nPROXY_PORT=%s\n' "$SEED" "$((8300 + SEED))" > .env  # Write your seed and your proxy port (8300 + seed).
```

```bash
cat .env  # Check it.
```

```bash
cat > compose.yaml <<'EOF'
services:
  web:
    build:
      context: ../web
      args:
        SEED: ${SEED}
    image: bytown-web:stack
  proxy:
    image: nginx:alpine
    ports:
      - "${PROXY_PORT}:80"
    volumes:
      - ./proxy/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - web
EOF
```

```bash
docker compose config > /dev/null && echo "compose.yaml is valid"  # Check the file. Fix any error before you go on.
```

```bash
docker compose up -d --build  # Build the web image, create the network and start both containers.
```

```bash
docker compose ps | tee ../evidence/part4-ps.txt  # Show the two containers and save the list. Only the proxy shows a port mapping.
```

```bash
curl -s http://localhost:$((8300 + SEED)) | tee ../evidence/part4-curl.txt  # Request the page through the proxy. You must see your seed.
```

Prove that the web container is **not** reachable directly. This command must fail:

```bash
curl -s --max-time 3 http://localhost:$((8100 + SEED)) || echo "not reachable, as intended"  # Nothing listens on this port now.
```

**Run the self-check now** (see "Check your work" below), while the stack is still running. Then stop it:

```bash
docker compose down  # Stop and delete the stack. The images stay.
```

```bash
cd ~/bytown-containers  # Go back to the lab folder.
```

---
## Part 5. Answers and clean-up (2 points)

Answer these three questions in your own words in a file named `answers.txt`, one answer per line, in the form `Q1: your answer`:

1. What happened to a file written inside a container that has no volume, when the container was deleted?
2. Why does the web service in your stack have no published port?
3. What is the difference between an image and a container, in one sentence?

Create the file with placeholders:

```bash
cat > answers.txt <<'EOF'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
EOF
```

Open `answers.txt` in any editor and replace each `replace this with your answer`. Each answer needs at least 20 characters.

Clean up the containers and the network (keep the images and the volume):

```bash
docker ps -a  # Check that no lab container is left.
```

---
## Check your work

The self-check reads your lab folder and asks Docker for the images and the volume. It changes nothing. Run it from your lab folder, with the stack from Part 4 still running for the best result. Use the path of your copy of the course repository:

```bash
python3 ~/net2008-devops/week09/lab/W09_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again. It checks that things exist and have the right shape. Your instructor also reads the files in your repository and `answers.txt`.

## Submit

1. Keep `.env` in the repository: your instructor needs your seed. Commit everything and push to a **public** GitHub repository named `bytown-containers` (the same steps as Week 6, Part 4). First create the empty repository on GitHub, then:

```bash
git add -A && git commit -m "Week 9 lab: containers"  # Save everything in one commit (add more commits if you prefer).
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-containers.git  # Link your empty GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 9 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline. Your instructor looks at the history.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Container run on your port, log saved | 3 |
| 2 | Image `bytown-web:1.0` with your seed label and page, image `bytown-web:1.1` | 6 |
| 3 | Volume `bytown-data-<seed>` with your file, served by a second container | 4 |
| 4 | Valid `compose.yaml`, proxy published, web not published, stack ran | 5 |
| 5 | `answers.txt` (read by your instructor) | 2 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$SEED` prints nothing, or names look like `web-` | The variable is lost. Run `export SEED=...` again and repeat the failing command. |
| `port is already allocated` | An old container uses the port. `docker ps -a`, then `docker rm -f NAME`. |
| `The container name ... is already in use` | `docker rm -f NAME`, then run the command again. |
| `docker compose config` shows `variable is not set` | You are not in the `stack` folder, or `.env` is missing. |
| The proxy answers `502 Bad Gateway` | The web container is not up yet or failed. `docker compose logs web`. Wait 3 seconds and try again. |
| `curl` says `Connection refused` | The container is not running or you used the wrong port. `docker ps`. |
| YAML error | A tab or a wrong indent in `compose.yaml`. Use spaces. Compare with the lab. |
| Everything is a mess | `docker compose down` in `stack`, `docker rm -f $(docker ps -aq)`, `docker volume rm bytown-data-$SEED`, then restart at Part 1. |
