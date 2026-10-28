# Week 12 Lab: Configure the Bytown Servers with Ansible
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). You create three servers (Docker containers) on **your own laptop**, and configure them with an inventory, ad hoc commands and a playbook with variables, a template and a handler. You prove the playbook is idempotent and preview a change.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Ansible does not run in plain PowerShell. Docker must be running and Ansible installed (see [W12_Setup_Ansible.md](W12_Setup_Ansible.md)).
- Do the parts in order. Each part builds on the one before.
- Use the **exact** names and file names given here. The self-check and your instructor look for them.
- Every command is one grey box. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Search the error message. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

Your numbers come from your student ID. **Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`. Replace `17` with **your** seed:

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

```bash
echo "My seed is $SEED"  # Print the seed to check it.
```

```bash
source ~/netops-venv/bin/activate  # Activate the Python virtual environment with Ansible. The prompt shows (netops-venv).
```

```bash
ansible --version | head -1  # Ansible must answer.
```

```bash
mkdir -p ~/bytown-ansible/evidence && cd ~/bytown-ansible && git init -b main  # Create the lab repository, with a folder for proof.
```

**If you close the terminal**, the variable and the virtual environment are lost. Open a new terminal, run `export SEED=...`, `source ~/netops-venv/bin/activate` and `cd ~/bytown-ansible`.

---
## Part 1. Servers and inventory (4 points)

Your three servers carry your seed in their names:

```bash
for n in web1 web2 db1; do docker run -d --name bytown-$n-$SEED debian:bookworm-slim sleep infinity; done  # Start three Debian containers: bytown-web1-<seed>, bytown-web2-<seed> and bytown-db1-<seed>.
```

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"  # Check that all three are Up.
```

Create the inventory. The shell inserts your seed:

```bash
cat > inventory.ini <<EOF
[web]
bytown-web1-$SEED
bytown-web2-$SEED

[db]
bytown-db1-$SEED

[all:vars]
ansible_connection=community.docker.docker
ansible_python_interpreter=/usr/bin/python3
EOF
```

```bash
cat > ansible.cfg <<'EOF'
[defaults]
inventory = inventory.ini
retry_files_enabled = False
EOF
```

```bash
ansible-inventory --graph  # You must see @web with two servers and @db with one.
```

The servers have no Python yet. Bootstrap them with the `raw` module, as in the lecture:

```bash
ansible all -m raw -a "apt-get update -qq && apt-get install -y -qq python3 python3-apt" > /dev/null  # Install Python on every server. This takes a minute.
```

```bash
ansible all -m ping | tee evidence/part1-ping.txt  # Every server must answer SUCCESS with "pong". The output is saved.
```

---
## Part 2. Ad hoc commands (4 points)

```bash
ansible web -m command -a "hostname" | tee evidence/part2-hostname.txt  # Ask the web servers for their host name. The output is saved.
```

```bash
ansible all -m setup -a "filter=ansible_distribution_release" | tee evidence/part2-facts.txt  # Read one fact from every server and save it. You must see bookworm.
```

```bash
ansible db -m apt -a "name=tree state=present update_cache=yes" > /dev/null  # Install the package tree on the database server.
```

```bash
ansible db -m apt -a "name=tree state=present" | tee evidence/part2-idempotent.txt  # Run the same command again. It must say "changed": false. The output is saved.
```

---
## Part 3. The playbook (6 points)

**3a. Variables.** They hold your seed and your site name:

```bash
mkdir -p group_vars templates  # Create the folders Ansible reads by name.
```

```bash
printf 'site: ott-dc1\nseed: %s\n' "$SEED" > group_vars/all.yml  # Variables for every server, including your seed.
```

```bash
printf 'page_title: Bytown NetOps Web\n' > group_vars/web.yml  # A variable for the web group only.
```

**3b. The template** for the home page:

```bash
cat > templates/index.html.j2 <<'EOF'
<h1>{{ page_title }}</h1>
<p>Site: {{ site }}</p>
<p>Seed: {{ seed }}</p>
<p>Served by: {{ inventory_hostname }} ({{ ansible_distribution }} {{ ansible_distribution_version }})</p>
EOF
```

**3c. The playbook.** Three plays, one for every server, one for the web group and one for the database group. Every task has a name:

```bash
cat > site.yml <<'EOF'
---
- name: Baseline for every server
  hosts: all
  tasks:
    - name: Record the seed in a file
      ansible.builtin.copy:
        content: "seed={{ seed }}\n"
        dest: /etc/bytown-seed
        mode: "0644"

    - name: Install curl
      ansible.builtin.apt:
        name: curl
        state: present
        update_cache: true
        cache_valid_time: 3600

- name: Web servers
  hosts: web
  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: Publish the home page from a template
      ansible.builtin.template:
        src: index.html.j2
        dest: /var/www/html/index.html
        mode: "0644"
      notify: Reload nginx

    - name: Make sure nginx is running
      ansible.builtin.command:
        cmd: nginx
        creates: /run/nginx.pid

    - name: Check that the page answers and shows the seed
      ansible.builtin.uri:
        url: http://localhost
        return_content: true
      register: page
      failed_when: (seed | string) not in page.content

  handlers:
    - name: Reload nginx
      ansible.builtin.command:
        cmd: nginx -s reload

- name: Database servers
  hosts: db
  tasks:
    - name: Install sqlite3
      ansible.builtin.apt:
        name: sqlite3
        state: present

    - name: Label the role of this server
      ansible.builtin.lineinfile:
        path: /etc/bytown-role
        line: "role=database site={{ site }}"
        create: true
        mode: "0644"
EOF
```

```bash
ansible-playbook --syntax-check site.yml  # Check the file. You must see "playbook: site.yml". Fix any error before you go on.
```

```bash
ansible-playbook site.yml | tee evidence/part3-run1.txt  # First run. Read it: yellow "changed" tasks. At the end the PLAY RECAP shows failed=0 for every server.
```

```bash
ansible-playbook site.yml | tee evidence/part3-run2.txt  # Second run. The PLAY RECAP must show changed=0 for every server: the playbook is idempotent.
```

```bash
ansible web -m uri -a "url=http://localhost return_content=yes" | tee evidence/part3-page.txt  # Fetch the page from inside each web server and save it. It must show your seed.
```

---
## Part 4. Preview a change (3 points)

Preview a change of the site name. **Nothing is applied.**

```bash
ansible-playbook site.yml -e site=ott-dc2 --check --diff | tee evidence/part4-check.txt  # Check mode with a diff: the output shows Site: ott-dc1 replaced by Site: ott-dc2 in the page, and the database label.
```

```bash
grep -E "ott-dc1|ott-dc2" evidence/part4-check.txt | head  # Look at the lines that would change.
```

Prove that nothing was applied:

```bash
ansible web -m uri -a "url=http://localhost return_content=yes" | grep "Site:"  # Still ott-dc1.
```

---
## Part 5. Answers (3 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. What does "idempotent" mean, and which output in this lab proved that your playbook is idempotent?
2. Why did `ping` fail before the `raw` bootstrap command?
3. A handler (`Reload nginx`) did not run in the second run. Why?

```bash
cat > answers.txt <<'EOF'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
EOF
```

Open `answers.txt` in an editor and replace each placeholder.

---
## Check your work

The self-check reads your files and your proof. It runs `ansible-playbook --syntax-check` on your playbook. It changes nothing. Run it from your lab folder:

```bash
python3 ~/net2008-devops/week12/W12_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again.

## Clean up

```bash
docker rm -f bytown-web1-$SEED bytown-web2-$SEED bytown-db1-$SEED  # Delete the three servers. Your files stay.
```

## Submit

1. Commit everything and push to a **public** GitHub repository named `bytown-ansible` (the same steps as Week 6, Part 4). Create the empty repository on GitHub first, then:

```bash
git add -A && git commit -m "Week 12 lab: ansible"  # Save everything.
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-ansible.git  # Link your empty GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 12 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Three servers, inventory with groups web and db, all answer `ping` | 4 |
| 2 | Ad hoc commands, an idempotent second run | 4 |
| 3 | Variables, template, three plays with a handler, first run without failures, second run with `changed=0`, page shows your seed | 6 |
| 4 | Check mode with a diff, nothing applied | 3 |
| 5 | `answers.txt` (read by your instructor) | 3 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$SEED` is empty and names look like `bytown-web1-` | The variable is lost. Run `export SEED=...` and repeat the command. |
| `ansible: command not found` | `source ~/netops-venv/bin/activate`. |
| `connection plugin ... community.docker.docker not found` | `ansible-galaxy collection install community.docker`. |
| `ping` fails with a Python error | Run the `raw` bootstrap line again. |
| `No such container` | The container name in `inventory.ini` does not match `docker ps`. Check your seed. |
| `failed_when` error: `seed is undefined` | `group_vars/all.yml` is missing or not in the same folder as `inventory.ini`. |
| `Could not import python modules: apt` | The bootstrap did not finish. Run it again and wait for it. |
| Second run is not `changed=0` | A task is not idempotent. Read which task shows `changed` in `evidence/part3-run2.txt`. |
| YAML error | Indentation or a missing space after a colon. The message gives the line number. |
| Everything is a mess | `docker rm -f` the three containers, delete `~/bytown-ansible/evidence/*` and restart at Part 1. |
