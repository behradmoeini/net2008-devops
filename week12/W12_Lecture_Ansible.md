# Week 12 Lecture: Configuration Management with Ansible
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). Ansible does not run in plain Windows PowerShell. You need Docker running and Ansible installed in your Python virtual environment (see [W12_Setup_Ansible.md](W12_Setup_Ansible.md)).

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- **You should see** shows roughly what the terminal prints.
- Do the steps in order. All practice work happens in one folder, `~/ansible-practice`.
- Your "servers" are **Docker containers** on your laptop. Ansible treats them exactly like real servers.

---
## The big picture

### The problem

Terraform (Week 11) makes servers **exist**. Now they are empty. You must install packages, copy files, change settings, start services, and do it the same way on 5 servers or 500. Logging in to each one by hand is slow and error-prone. **Ansible** does it for you from one place.

### How Ansible works

| Idea | Meaning |
|---|---|
| **Agentless** | Nothing to install on the servers except Python. Ansible runs from your laptop (the **control node**) and uses SSH (here: Docker) to reach the **managed nodes**. |
| **Push** | You run Ansible, and it pushes changes to the servers. |
| **Declarative and idempotent** | You describe the **state** you want ("nginx is installed"). If it is already true, Ansible changes nothing. Run a playbook ten times: same result. |
| **YAML** | Everything you write is YAML. |

### Seven words to know

| Word | Meaning |
|---|---|
| **Inventory** | The list of servers, in groups |
| **Module** | A tool that does one job: `apt` installs packages, `copy` copies a file, `template` fills a file, `service` manages services |
| **Task** | One call of a module, with a name |
| **Play** | A list of tasks run on one group of servers |
| **Playbook** | A YAML file with one or more plays |
| **Handler** | A task that runs only when another task reports a change (for example "reload nginx") |
| **Fact** | Information Ansible collects from a server (operating system, memory, address) |

### Ansible or Terraform?

| | Terraform | Ansible |
|---|---|---|
| Job | **Provision**: create servers, networks | **Configure**: what is inside the servers |
| Remembers | A state file | Nothing: it asks the server each time |

You use both: Terraform builds the servers, Ansible sets them up.

---
## Step 1. Check your tools

```bash
source ~/netops-venv/bin/activate  # Activate the virtual environment from the setup guide. The prompt shows (netops-venv). Do this in every new terminal.
```

```bash
ansible --version | head -2  # Ansible must answer with a version number.
```

```bash
ansible-galaxy collection list community.docker  # The community.docker collection must be listed. If not: ansible-galaxy collection install community.docker
```

```bash
mkdir -p ~/ansible-practice && cd ~/ansible-practice  # Create the practice folder and move into it.
```

---
## Step 2. Create three "servers"

```bash
docker run -d --name web1 debian:bookworm-slim sleep infinity  # Start a Debian container that does nothing but stay alive. It is our first server.
```

```bash
docker run -d --name web2 debian:bookworm-slim sleep infinity  # A second web server.
```

```bash
docker run -d --name db1 debian:bookworm-slim sleep infinity  # A database server.
```

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"  # Three containers are running.
```

---
## Step 3. The inventory

The inventory lists the servers and puts them in groups. Square brackets start a group:

```bash
cat > inventory.ini <<'EOF'
[web]
web1
web2

[db]
db1

[all:vars]
ansible_connection=community.docker.docker
ansible_python_interpreter=/usr/bin/python3
EOF
```

- Each name is a **container name**.
- `[all:vars]` sets variables for every server: connect through Docker (instead of SSH), and use Python at this path.

```bash
ansible-inventory -i inventory.ini --graph  # Show the groups as a tree: @all contains @web (web1, web2) and @db (db1).
```

```bash
ansible -i inventory.ini all -m ping  # Try the ping module on all servers. It FAILS: the containers have no Python yet.
```

**You should see** an error that mentions Python. Ansible modules are small Python programs that Ansible copies to the server, so the server needs Python. The `raw` module needs no Python: use it to bootstrap.

```bash
ansible -i inventory.ini all -m raw -a "apt-get update -qq && apt-get install -y -qq python3 python3-apt"  # Install Python on every server with the raw module.
```

```bash
ansible -i inventory.ini all -m ping  # Now it works. Every server answers SUCCESS with "ping": "pong".
```

To avoid typing `-i inventory.ini` every time, create a config file in this folder:

```bash
cat > ansible.cfg <<'EOF'
[defaults]
inventory = inventory.ini
retry_files_enabled = False
EOF
```

---
## Step 4. Ad hoc commands

An **ad hoc command** runs one module once. Form: `ansible GROUP -m MODULE -a "ARGUMENTS"`.

```bash
ansible web -m command -a "hostname"  # Run a command on the web group only.
```

```bash
ansible all -m setup -a "filter=ansible_distribution*"  # Print facts about the operating system of every server.
```

```bash
ansible db -m apt -a "name=tree state=present update_cache=yes"  # Install the package tree on the db group. The first time it says CHANGED.
```

```bash
ansible db -m apt -a "name=tree state=present"  # Run the same command again. It says SUCCESS with "changed": false. Nothing to do: idempotent.
```

Colour code: **green** = already correct, **yellow** = changed something, **red** = failed.

---
## Step 5. Your first playbook

Ad hoc commands are good for one-off checks. For real work you write a **playbook**:

```bash
cat > site.yml <<'EOF'
---
- name: Baseline for every server
  hosts: all
  tasks:
    - name: Install curl
      ansible.builtin.apt:
        name: curl
        state: present

- name: Web servers
  hosts: web
  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: Publish a home page
      ansible.builtin.copy:
        content: "<h1>Hello from {{ inventory_hostname }}</h1>\n"
        dest: /var/www/html/index.html
        mode: "0644"
      notify: Reload nginx

    - name: Make sure nginx is running
      ansible.builtin.command:
        cmd: nginx
        creates: /run/nginx.pid

  handlers:
    - name: Reload nginx
      ansible.builtin.command:
        cmd: nginx -s reload
EOF
```

Read it:

- A playbook is a YAML **list** of plays (each starts with `- name:`).
- `hosts:` picks the group. `tasks:` is a list of tasks.
- A task has a `name` (read by humans) and one module with its arguments.
- `{{ inventory_hostname }}` is a **variable**: Ansible replaces it with the server name.
- `notify` calls a handler, but only if this task **changed** something.
- `creates: /run/nginx.pid` makes the `command` module skip the task when that file exists. It is a simple way to make a command idempotent.

```bash
ansible-playbook --syntax-check site.yml  # Check the YAML and the structure without running anything.
```

```bash
ansible-playbook site.yml  # Run the playbook. Read the output: each task shows ok or changed for each server. The last block is the PLAY RECAP.
```

**You should see** `changed` for the installs on the first run. Now run it again:

```bash
ansible-playbook site.yml  # The second run shows changed=0 for every server. Idempotent.
```

```bash
ansible web -m uri -a "url=http://localhost return_content=yes"  # Ask nginx on each web server for its page, from inside the server.
```

**You should see** `Hello from web1` and `Hello from web2`.

---
## Step 6. Check mode: look before you change

```bash
ansible-playbook site.yml --check --diff  # Show what WOULD change, with a before/after diff, without changing anything.
```

This is the Ansible equivalent of `terraform plan`. Use it before every run on real servers.

---
## Step 7. Variables and templates

Put values in a **variable file**, and fill them into a **template**. A template is a file with `{{ ... }}` holes, written in a language called **Jinja2**.

```bash
mkdir -p group_vars templates  # Folders Ansible reads by name: group_vars holds variables, templates holds templates.
```

```bash
cat > group_vars/web.yml <<'EOF'
page_title: Demo Web Server
EOF
```

```bash
cat > group_vars/all.yml <<'EOF'
site: ott-dc1
EOF
```

`group_vars/all.yml` applies to every server. `group_vars/web.yml` applies to the `web` group. The file name must match the group name.

```bash
cat > templates/index.html.j2 <<'EOF'
<h1>{{ page_title }}</h1>
<p>Site: {{ site }}</p>
<p>Served by: {{ inventory_hostname }} ({{ ansible_distribution }} {{ ansible_distribution_version }})</p>
EOF
```

`ansible_distribution` is a **fact**: Ansible reads it from the server. Now use the template instead of `copy`. Change the task in `site.yml`:

```bash
python3 - <<'EOF'
import re
p = open("site.yml").read()
old = '''      ansible.builtin.copy:
        content: "<h1>Hello from {{ inventory_hostname }}</h1>\\n"
        dest: /var/www/html/index.html'''
new = '''      ansible.builtin.template:
        src: index.html.j2
        dest: /var/www/html/index.html'''
assert old in p
open("site.yml", "w").write(p.replace(old, new))
EOF
```

```bash
ansible-playbook site.yml  # Run again. Only the template task changes. The handler reloads nginx.
```

```bash
ansible web -m uri -a "url=http://localhost return_content=yes" | grep -E "Site|Served|Demo"  # The new page shows the variables.
```

Override a variable from the command line (highest priority):

```bash
ansible-playbook site.yml -e site=ott-dc2 --check --diff | grep "Site:"  # Preview a change of the site name. Nothing is changed.
```

**Variable priority** (low to high), simplified: `group_vars/all` < `group_vars/GROUP` < variables in the playbook < `-e` on the command line.

---
## Step 8. Loops and conditions

```bash
cat > extras.yml <<'EOF'
---
- name: Loops and conditions
  hosts: all
  tasks:
    - name: Install several small tools
      ansible.builtin.apt:
        name: "{{ item }}"
        state: present
      loop:
        - tree
        - less

    - name: Only on web servers, say so
      ansible.builtin.debug:
        msg: "{{ inventory_hostname }} is a web server"
      when: "'web' in group_names"
EOF
```

```bash
ansible-playbook extras.yml  # The loop runs once per item. The debug message prints only for web1 and web2: the others show "skipping".
```

---
## Step 9. Clean up

```bash
docker rm -f web1 web2 db1  # Delete the three containers (the servers).
```

## Cheat sheet

| Command | What it does |
|---|---|
| `ansible GROUP -m MODULE -a "ARGS"` | One module, once (ad hoc) |
| `ansible-playbook FILE` | Run a playbook |
| `ansible-playbook FILE --check --diff` | Preview without changing |
| `ansible-playbook FILE -e name=value` | Override a variable |
| `ansible-playbook FILE --syntax-check` | Check the YAML |
| `ansible-inventory --graph` | Show the groups |
| `ansible-doc MODULE` | Read the manual of a module |

## If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| `ansible: command not found` | The virtual environment is not active: `source ~/netops-venv/bin/activate`. |
| `couldn't resolve module/action 'community.docker...'` or `connection plugin ... not found` | Install the collection: `ansible-galaxy collection install community.docker`. |
| `Failed to connect ... No such container` | The container name in the inventory is wrong or the container is stopped. `docker ps`. |
| `/bin/sh: 1: /usr/bin/python3: not found` or `module ... requires python` | Bootstrap with the `raw` command from Step 3. |
| `Could not import python modules: apt, apt_pkg` | `python3-apt` is missing. Run the `raw` bootstrap line again. |
| `[WARNING]: Ansible is being run in a world writable directory ... ignoring ansible.cfg` | You are in a folder under `/mnt/c` (Windows). Work in your Linux home folder `~`. |
| YAML error: `mapping values are not allowed here` or `could not find expected ':'` | Indentation or a missing space after a colon. The message gives the line number. |
| A task shows `changed` on every run | The task is not idempotent (for example `command` with no `creates`). |
| Apple silicon: package or image problems | The Debian image has an ARM build. Make sure you did not add `--platform linux/amd64`. |

## Summary

- Ansible configures servers from one place, with no agent, using modules written as YAML tasks.
- Inventory = servers and groups. Playbook = plays = tasks. Handlers run only on change.
- Idempotent: the second run changes nothing. `--check --diff` previews a run.
- Variables live in `group_vars`. Templates (Jinja2) turn variables and facts into files.

**Next:** the Week 12 lab (graded) configures three servers with your own seed. Then Practical Assessment 3 combines Docker, Terraform and Ansible.
