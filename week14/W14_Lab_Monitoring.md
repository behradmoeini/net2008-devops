# Week 14 Lab: Monitor the Bytown Web Server
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). On **your own laptop** you monitor a web server with **Nagios** (active checks), then store and query log events with **Elasticsearch** (the core of ELK). Your seed changes the names, ports and data, so each student's results are different.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Docker with Compose must be running.
- Run **one stack at a time**. Part 1 and Part 2 each end with `docker compose down`. Do not skip it: two stacks together need more memory than many laptops have.
- Use the **exact** names and file names given here. The self-check and your instructor look for them.
- Every command is one grey box. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

**Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`. Replace `17` with **your** seed:

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

```bash
echo "Nagios port $((8600 + SEED)), Elasticsearch port $((8650 + SEED)), Kibana port $((8700 + SEED))"  # Your three ports. Write them down.
```

```bash
mkdir -p ~/bytown-monitor/evidence ~/bytown-monitor/nagios/conf.d ~/bytown-monitor/nagios/target ~/bytown-monitor/elk && cd ~/bytown-monitor && git init -b main  # Create the lab repository with its folders.
```

**If you close the terminal**, open a new one, run `export SEED=...` and `cd ~/bytown-monitor`.

---
## Part 1. Nagios (8 points)

**1a. The target** serves a file that contains your seed:

```bash
cd ~/bytown-monitor/nagios && echo "seed=$SEED" > target/seed.txt  # The file the monitor will look for.
```

```bash
printf 'SEED=%s\nNAGIOS_PORT=%s\n' "$SEED" "$((8600 + SEED))" > .env  # Compose reads .env automatically and fills in ${SEED} and ${NAGIOS_PORT}.
```

```bash
cat > compose.yaml <<'EOF'
services:
  target:
    image: nginx:1.27-alpine
    container_name: bytown-target-${SEED}
    volumes:
      - ./target/seed.txt:/usr/share/nginx/html/seed.txt:ro
  nagios:
    image: jasonrivers/nagios:latest
    container_name: bytown-nagios-${SEED}
    ports:
      - "${NAGIOS_PORT}:80"
    volumes:
      - ./conf.d:/opt/nagios/etc/conf.d:ro
EOF
```

**1b. The Nagios configuration.** One host and two services. The shell inserts your seed:

```bash
cat > conf.d/bytown.cfg <<EOF
define host {
    use                   linux-server
    host_name             bytown-web-$SEED
    alias                 Bytown web $SEED
    address               bytown-target-$SEED
    check_command         check_http
    max_check_attempts    1
}

define service {
    use                   generic-service
    host_name             bytown-web-$SEED
    service_description   HTTP
    check_command         check_http
    max_check_attempts    1
    normal_check_interval 1
    retry_check_interval  1
}

define service {
    use                   generic-service
    host_name             bytown-web-$SEED
    service_description   Seed file
    check_command         check_http!-u /seed.txt -s seed=$SEED
    max_check_attempts    1
    normal_check_interval 1
    retry_check_interval  1
}
EOF
```

```bash
docker compose up -d && docker compose ps  # Start both containers and check that both are running.
```

Wait **two minutes** for the first checks. Then read the state of your services and save it:

```bash
curl -s -u nagiosadmin:nagios "http://localhost:$((8600 + SEED))/nagios/cgi-bin/statusjson.cgi?query=servicelist&hostname=bytown-web-$SEED" | tee ../evidence/nagios-ok.json  # Ask Nagios for the state of your services. Both must be 2 (OK). The output is saved.
```

If a value is `1` (pending) or the answer is an error, wait another minute and run it again. Use the same command, but write to the file again (the `tee` replaces it).

**1c. Make it fail.** Stop the target, wait two minutes, and save the state again:

```bash
docker stop bytown-target-$SEED  # Stop the web server. Nagios is still running.
```

```bash
sleep 120 && curl -s -u nagiosadmin:nagios "http://localhost:$((8600 + SEED))/nagios/cgi-bin/statusjson.cgi?query=servicelist&hostname=bytown-web-$SEED" | tee ../evidence/nagios-critical.json  # Wait two minutes, then read the state. Both services must be 16 (CRITICAL). The output is saved.
```

Open `http://localhost:<your Nagios port>/nagios` in the browser (user `nagiosadmin`, password `nagios`) and look at **Services**. This is the alert page.

```bash
docker compose down && cd ~/bytown-monitor  # Remove the Nagios stack before Part 2, and go back to the lab folder.
```

---
## Part 2. Elasticsearch (8 points)

On **Linux and Ubuntu (WSL 2)** run the kernel setting first (macOS: skip; Windows with Docker Desktop: see the table at the end):

```bash
sudo sysctl -w vm.max_map_count=262144  # Linux and WSL only. Elasticsearch needs this.
```

**2a. The stack.**

```bash
cd ~/bytown-monitor/elk && printf 'SEED=%s\nES_PORT=%s\nKIBANA_PORT=%s\n' "$SEED" "$((8650 + SEED))" "$((8700 + SEED))" > .env  # Your ports and seed for Compose.
```

```bash
cat > compose.yaml <<'EOF'
services:
  es:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.3
    container_name: bytown-es-${SEED}
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "${ES_PORT}:9200"
    mem_limit: 1g
  kibana:
    image: docker.elastic.co/kibana/kibana:8.15.3
    container_name: bytown-kibana-${SEED}
    environment:
      - ELASTICSEARCH_HOSTS=http://es:9200
    ports:
      - "${KIBANA_PORT}:5601"
    depends_on:
      - es
EOF
```

```bash
docker compose up -d  # Start Elasticsearch and Kibana. The first start downloads about 1.5 GB.
```

```bash
until curl -s "localhost:$((8650 + SEED))" | grep -q tagline; do sleep 5; done; echo "Elasticsearch is up"  # Wait until Elasticsearch answers. This can take one to two minutes.
```

**2b. Your events.** This script makes `60 + SEED` events that are different for every seed:

```bash
cat > gen_events.py <<'EOF'
import json
import random
import sys

seed = int(sys.argv[1])
rng = random.Random(seed)
paths = ["/login", "/index.html", "/api/devices", "/api/alerts", "/logout"]
statuses = [200, 200, 200, 200, 301, 404, 500]
with open("events.ndjson", "w", encoding="utf-8") as f:
    for i in range(60 + seed):
        f.write(json.dumps({"index": {"_index": "bytown-events"}}) + "\n")
        f.write(json.dumps({"id": i, "path": rng.choice(paths), "status": rng.choice(statuses), "bytes": rng.randint(100, 5000)}) + "\n")
EOF
```

```bash
python3 gen_events.py "$SEED" && wc -l events.ndjson  # Create events.ndjson. The line count is 2 x (60 + your seed).
```

**2c. Load and query.** Each answer is saved as proof:

```bash
curl -s -X POST "localhost:$((8650 + SEED))/_bulk?refresh=true" -H 'Content-Type: application/x-ndjson' --data-binary @events.ndjson > ../evidence/es-bulk.json  # Send all events to Elasticsearch. The answer is saved.
```

```bash
curl -s "localhost:$((8650 + SEED))/bytown-events/_count" | tee ../evidence/es-count.json  # How many events are stored? It must be 60 + your seed.
```

```bash
curl -s -H 'Content-Type: application/json' "localhost:$((8650 + SEED))/bytown-events/_search?size=0" -d '{"aggs":{"by_status":{"terms":{"field":"status"}}}}' > ../evidence/es-status.json  # Count the events for each status code. The answer is saved.
```

```bash
curl -s -H 'Content-Type: application/json' "localhost:$((8650 + SEED))/bytown-events/_count" -d '{"query":{"range":{"status":{"gte":500}}}}' | tee ../evidence/es-errors.json  # Count the server errors (status 500 or more).
```

Open Kibana at `http://localhost:<your Kibana port>`. Create a data view named `bytown-events` with index pattern `bytown-events` and **no time field**, then open **Discover**. Click the field `status` and note which value is most common.

```bash
docker compose down && cd ~/bytown-monitor  # Remove the ELK stack and go back to the lab folder.
```

---
## Part 3. Answers (4 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. Nagios used `max_check_attempts 1`. Why is this fine for this lab and a bad idea in production?
2. In `nagios-critical.json` both services were CRITICAL, but only one thing was broken. What was it, and what does this tell you about alerts that depend on each other?
3. What is the difference between an active check (Nagios) and log shipping (Elasticsearch)? Give one problem each is good at finding.
4. Name one real-life situation where you would choose Zabbix or Splunk over what you used in this lab, and say why.

```bash
cat > answers.txt <<'EOF'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
Q4: replace this with your answer
EOF
```

Open `answers.txt` in an editor and replace each placeholder.

---
## Check your work

The self-check reads your files and your proof and changes nothing. Run it from your lab folder:

```bash
python3 ~/net2008-devops/week14/W14_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again.

## Submit

1. Create an **empty public** repository named `bytown-monitor` on GitHub (no README). Add a `.gitignore` so Docker caches are not uploaded:

```bash
printf '__pycache__/\n' > .gitignore  # Nothing else needs to be ignored in this lab.
```

```bash
git add -A && git commit -m "Week 14 lab: monitoring"  # Save everything.
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-monitor.git  # Link your empty GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 14 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Compose file and configuration with your seed (4), a saved OK state (2), a saved CRITICAL state (2) | 8 |
| 2 | Compose file with your ports (2), all events loaded (2), correct status counts (2), correct error count (2) | 8 |
| 3 | `answers.txt` (read by your instructor) | 4 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$SEED` is empty and names look like `bytown-target-` | The variable is lost. Run `export SEED=...`. Delete `.env` and `conf.d/bytown.cfg` and repeat the steps that created them. |
| `variable is not set` warning from Compose | The `.env` file is missing or you are not in the stack's folder. |
| Nagios answers `{"result": ... "failed"` or a 401 error | Wait a minute; user is `nagiosadmin`, password `nagios`. |
| Services stay `1` (pending) | Wait two more minutes. The first checks are spread out. |
| Services are `16` while the target runs | `docker exec bytown-nagios-$SEED /opt/nagios/libexec/check_http -I bytown-target-$SEED -u /seed.txt -s seed=$SEED` shows the real reason. |
| Elasticsearch container exits at once | Linux or WSL: run the `sysctl` command. Windows with Docker Desktop: in PowerShell run `wsl -d docker-desktop sysctl -w vm.max_map_count=262144`. |
| The `until` loop never ends | `docker logs bytown-es-$SEED` shows the error. Low memory is the usual cause: close other programs and apps. |
| `"errors":true` in `es-bulk.json` | Delete the index (`curl -X DELETE localhost:<port>/bytown-events`), then load again. |
| `es-count.json` shows more than 60 + seed | You loaded twice. Delete the index as above and load once. |
| `port is already allocated` | The other stack is still running. `docker compose down` in its folder. |
| Everything is a mess | `docker compose down` in both folders, delete `evidence/*`, and restart at the failing part. |
