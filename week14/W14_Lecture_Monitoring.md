# Week 14 Lecture: Monitoring and Logging with Nagios and ELK
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Docker with Compose (Week 9). Run **one stack at a time**: the ELK stack alone needs about 2.5 GB of memory, so close Nagios before you start ELK.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it, press Enter, then go to the next box.
- All practice work happens in one folder, `~/monitor-practice`.

---
## The big picture: read this first

You cannot fix what you cannot see. Production systems fail at 3 a.m., and the first question is always "what happened, and since when?". **Monitoring** answers it with data collected all the time.

| Pillar | What it is | Example | Tools in this course |
|---|---|---|---|
| **Metrics** | Numbers over time | CPU 82%, 40 requests per second | Nagios (checks), Zabbix |
| **Logs** | Text events | `GET /login 500` at 10:41:07 | ELK, Splunk |
| **Alerts** | A message when something is wrong | "web-17 is CRITICAL" | All of them |

### What to watch: the four golden signals

| Signal | Question |
|---|---|
| **Latency** | How long does a request take? |
| **Traffic** | How many requests arrive? |
| **Errors** | How many requests fail? |
| **Saturation** | How full is the resource (CPU, memory, disk, connections)? |

An **SLI** is a measured number (99.2% of requests succeeded). An **SLO** is the target (99.5%). An **alert** should fire when the SLO is at risk, and every alert should need a human to act. An alert nobody acts on is noise, and people learn to ignore noise.

### Two ways to collect data

| Style | How | Example |
|---|---|---|
| **Active check** ("pull") | The monitor connects and asks | Nagios opens `http://web/` every minute |
| **Log shipping** ("push") | The system sends its events to a store | Web server logs go to Elasticsearch |

### The tools

| Tool | Kind | Where it fits | In this course |
|---|---|---|---|
| **Nagios** | Active checks, states OK / WARNING / CRITICAL / UNKNOWN | Classic server and service availability | Hands-on lab |
| **ELK** (Elasticsearch, Logstash, Kibana) | Log search and charts | Find and count events | Hands-on lab |
| **Zabbix** | Agents and templates, graphs, auto-discovery | A full monitoring platform for a company | Instructor demo |
| **Splunk** | Commercial log analysis and security | Large organizations, security teams | Instructor demo |

Zabbix and Splunk need more memory, licences or registration, so you see them in class and you do not install them. The ideas are the same: collect, store, query, alert.

---
## Part A. Nagios

Nagios reads **configuration files** that describe *hosts* (machines) and *services* (what to check on them). It runs a **check command** on a schedule and shows the result.

| Term | Meaning |
|---|---|
| **Host** | A machine or container to watch |
| **Service** | One check on a host (web page answers, disk free, ...) |
| **Check command** | The small program that does the check (here `check_http`) |
| **State** | OK (exit code 0), WARNING (1), CRITICAL (2), UNKNOWN (3) |

### Step 1. A target to watch

```bash
mkdir -p ~/monitor-practice/nagios/conf.d ~/monitor-practice/nagios/target && cd ~/monitor-practice/nagios  # Create the folders.
```

```bash
echo "hello from the target" > target/hello.txt  # A file for the web server to serve.
```

```bash
cat > compose.yaml <<'EOF'
services:
  target:
    image: nginx:1.27-alpine
    container_name: practice-target
    volumes:
      - ./target/hello.txt:/usr/share/nginx/html/hello.txt:ro
  nagios:
    image: jasonrivers/nagios:latest
    container_name: practice-nagios
    ports:
      - "8680:80"
    volumes:
      - ./conf.d:/opt/nagios/etc/conf.d:ro
EOF
```

Two containers on one private network. Compose gives each one a name that the others can use as an address: `target` and `nagios`.

### Step 2. Tell Nagios what to watch

```bash
cat > conf.d/practice.cfg <<'EOF'
define host {
    use                   linux-server
    host_name             practice-web
    alias                 Practice web server
    address               practice-target
    check_command         check_http
    max_check_attempts    1
}

define service {
    use                   generic-service
    host_name             practice-web
    service_description   HTTP
    check_command         check_http
    max_check_attempts    1
    normal_check_interval 1
    retry_check_interval  1
}

define service {
    use                   generic-service
    host_name             practice-web
    service_description   Hello file
    check_command         check_http!-u /hello.txt -s hello
    max_check_attempts    1
    normal_check_interval 1
    retry_check_interval  1
}
EOF
```

| Line | Meaning |
|---|---|
| `use linux-server` / `generic-service` | Start from a **template** with sensible defaults |
| `address` | Where to connect (the container name) |
| `check_command check_http!-u /hello.txt -s hello` | Run `check_http`. After `!` come the arguments: fetch `/hello.txt` and require the word `hello` in the answer. |
| `max_check_attempts 1` | Do not retry: go CRITICAL at the first failure (good for a lab, too nervous for production) |
| `normal_check_interval 1` | Check every 1 minute |

```bash
docker compose up -d  # Start both containers.
```

```bash
docker compose ps  # Both must be running.
```

Wait about 90 seconds, then open <http://localhost:8680/nagios> (user `nagiosadmin`, password `nagios`). Click **Services** in the left menu. You see two services with green **OK**.

### Step 3. Read the state from the command line

Nagios has a JSON interface. Scripts use it:

```bash
curl -s -u nagiosadmin:nagios "http://localhost:8680/nagios/cgi-bin/statusjson.cgi?query=servicelist&hostname=practice-web"  # Ask for the state of all services of the host. In the answer, 2 means OK, 4 WARNING, 8 UNKNOWN, 16 CRITICAL.
```

### Step 4. Make it fail

```bash
docker stop practice-target  # Stop the web server. The monitor stays up.
```

Wait 90 seconds and run the `curl` command again, or refresh the page. Both services are **CRITICAL** (16). This is the alert. Bring it back:

```bash
docker start practice-target  # Start the web server. After about a minute the services are OK again.
```

```bash
docker compose down  # Stop and remove the Nagios stack before you start the next one.
```

---
## Part B. ELK

You do not need Logstash for this lab, so you use two parts of ELK:

| Part | Role |
|---|---|
| **Elasticsearch** | Stores documents (here: log events as JSON) and answers searches and counts |
| **Kibana** | The web page to explore and chart what is in Elasticsearch |
| Logstash / Beats (not used here) | Collect, parse and ship logs into Elasticsearch |

An **index** is a collection of documents (like a table). A **document** is one JSON object (one event).

### Step 5. Start Elasticsearch and Kibana

On **Linux and Ubuntu (WSL 2)**, Elasticsearch needs a kernel setting first:

```bash
sudo sysctl -w vm.max_map_count=262144  # Linux only. On macOS, skip this. On Windows with Docker Desktop, see the troubleshooting table.
```

```bash
mkdir -p ~/monitor-practice/elk && cd ~/monitor-practice/elk  # A new folder for the second stack.
```

```bash
cat > compose.yaml <<'EOF'
services:
  es:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.3
    container_name: practice-es
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "8690:9200"
    mem_limit: 1g
  kibana:
    image: docker.elastic.co/kibana/kibana:8.15.3
    container_name: practice-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://es:9200
    ports:
      - "8691:5601"
    depends_on:
      - es
EOF
```

`xpack.security.enabled=false` turns off passwords. That is acceptable on a laptop and **never** acceptable on a real server.

```bash
docker compose up -d  # Start both. The first start downloads about 1.5 GB.
```

```bash
curl -s localhost:8690  # Elasticsearch answers with a JSON "tagline: You Know, for Search" after about a minute. If you get an error, wait and repeat.
```

### Step 6. Add events

```bash
cat > events.ndjson <<'EOF'
{"index":{"_index":"practice-events"}}
{"path":"/login","status":200,"bytes":512}
{"index":{"_index":"practice-events"}}
{"path":"/login","status":500,"bytes":90}
{"index":{"_index":"practice-events"}}
{"path":"/api/devices","status":200,"bytes":2048}
{"index":{"_index":"practice-events"}}
{"path":"/api/devices","status":404,"bytes":120}
EOF
```

This is the **bulk format**: one action line, one document line, repeated.

```bash
curl -s -X POST "localhost:8690/_bulk?refresh=true" -H 'Content-Type: application/x-ndjson' --data-binary @events.ndjson  # Send the four events. The answer contains "errors":false.
```

### Step 7. Search and count

```bash
curl -s "localhost:8690/practice-events/_count"  # How many events are stored? 4.
```

```bash
curl -s -H 'Content-Type: application/json' "localhost:8690/practice-events/_search?size=0" -d '{"aggs":{"by_status":{"terms":{"field":"status"}}}}'  # An aggregation: count the events for each status code.
```

```bash
curl -s -H 'Content-Type: application/json' "localhost:8690/practice-events/_count" -d '{"query":{"range":{"status":{"gte":500}}}}'  # A query: how many server errors (status 500 or more)? 1.
```

### Step 8. Look at it in Kibana

Open <http://localhost:8691>. Open the menu, then **Stack Management > Data Views > Create data view**. Name `practice-events`, index pattern `practice-events`, **Save**. Open **Discover**: set the time filter to **Last 15 years** if the page looks empty (these events have no timestamp, so choose "No time field" when you create the data view). You see your four events and can click a field to see its values.

```bash
docker compose down  # Stop and remove the stack. The data disappears with it.
```

## Zabbix and Splunk (instructor demo)

Your instructor shows both in class. Compare them with what you did:

| Question | Nagios | ELK | Zabbix | Splunk |
|---|---|---|---|---|
| Main data | Check results | Log events | Metrics from agents | Log events |
| Configuration | Text files | Mostly API and web page | Web page and templates | Web page |
| Graphs | Weak | Strong (Kibana) | Strong | Strong |
| Alerts | Core feature | Needs extra setup | Core feature | Core feature |
| Cost | Free core | Free basic | Free | Commercial licence |

## Cheat sheet

| Task | Command |
|---|---|
| Start a stack | `docker compose up -d` |
| Stop and remove a stack | `docker compose down` |
| See the logs of a container | `docker logs NAME` |
| Nagios service states | `curl -s -u nagiosadmin:nagios "http://localhost:PORT/nagios/cgi-bin/statusjson.cgi?query=servicelist&hostname=HOST"` |
| Count documents | `curl -s localhost:PORT/INDEX/_count` |
| Count by field | `_search?size=0` with an `aggs` / `terms` body |

## If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| Nagios page shows "Pending" or no services | Wait another minute. The first checks need time. |
| Nagios asks for a password again and again | User `nagiosadmin`, password `nagios`. |
| Nagios services are CRITICAL, target is running | `docker exec practice-nagios /opt/nagios/libexec/check_http -I practice-target -u /hello.txt -s hello` shows the real reason. |
| `no such file` for `conf.d/practice.cfg` | You are not in the `nagios` folder. `cd ~/monitor-practice/nagios`. |
| Elasticsearch container exits at once | Linux or WSL: run the `sysctl` command of Step 5. Windows with Docker Desktop: in PowerShell run `wsl -d docker-desktop sysctl -w vm.max_map_count=262144`. |
| `curl: (52) Empty reply` or `(56)` | Elasticsearch is still starting. Wait a minute. |
| Kibana says "server is not ready" | Wait two minutes. Check `docker logs practice-kibana`. |
| `port is already allocated` | Another stack is still running. `docker compose down` in the other folder. |
| Everything is slow or Docker crashes | You have two stacks running or too little memory. Run one stack at a time. |

## Summary

- Monitoring has three parts: metrics, logs, alerts. Watch latency, traffic, errors and saturation.
- Nagios makes **active checks** from text configuration: hosts, services, check commands, states.
- ELK stores and searches **log events**: Elasticsearch holds JSON documents, Kibana shows them.
- Run one heavy stack at a time on a laptop, and `docker compose down` between them.
- Good alerts need a human to act. Everything else is noise.

**Next:** the Week 14 lab (graded) uses your own seed for both stacks. PA4 is in Week 15.
