# NET2008 DevOps: Practical Assessment 3

**Containerized Infrastructure Pipeline** | Docker, Terraform and Ansible | 5% of final grade | 50 marks repository + 50 marks live demo

## The situation

A web server writes an access log. Nobody reads it. You build a pipeline that turns a log file into a summary and publishes it on a small web page, from nothing, with one command. A ready-made Python program summarises the log inside a **Docker** container. **Terraform** creates the network, the storage and two containers. **Ansible** configures the second container as a web server that publishes the summary. A script, `run.sh`, runs all of it and checks that it works. Everything runs on your own laptop (macOS, Linux, or Windows with the Ubuntu WSL 2 terminal).

The summary program is given to you. The assessment is about Docker, Terraform and Ansible (Weeks 9, 11 and 12), with Git (Week 6) throughout. You decide how to write the Dockerfile, the Terraform code and the playbook.

## What you submit

A **public GitHub repository** named `net2008-pa3`. You submit only the repository URL, as text, in *Practical Assessment 3 Submission* on Brightspace before the deadline.

Your work is marked in two steps:

1. **Repository (50 marks).** Your instructor reads the repository as it was at the deadline: the files, the commit history and the evidence folder.
2. **Live demo (50 marks).** In your lab, **the week after the deadline**, you clone your repository on your own laptop and run the pipeline in front of your instructor. See [The live demo](#the-live-demo).

When you are ready to submit, create the tag `v1.0` on your final commit and push it (`git tag v1.0` and `git push origin v1.0`). The commit with that tag is the one that is marked. Commits made after the deadline are not marked.

The repository root contains exactly this layout:

```
net2008-pa3/
  README.md   .gitignore   run.sh
  app/        logsum.py (provided)  Dockerfile  .dockerignore
  tools/      check_report.py (provided)
  data/       access.log                 (a copy of PA3_sample.log)
  infra/      main.tf  variables.tf  outputs.tf  terraform.tfvars
  ansible/    inventory.ini  site.yml  group_vars/all.yml  templates/
  evidence/   (files created by run.sh, committed)
```

## The programs you receive

You do **not** write the Python code. Two programs are posted with this brief. Copy `logsum.py` to `app/logsum.py` and `check_report.py` to `tools/check_report.py`, and use them as they are.

| Program | What it does |
|---|---|
| `logsum.py` | Started as `python logsum.py INPUT_LOG OUTPUT_FOLDER`. Reads an access log and writes `summary.json` and `summary.xml` in the output folder. It also prints the JSON on one line. Exit code 0 on success, 1 for an unreadable input, 2 for wrong arguments. It needs only Python. |
| `check_report.py` | Started as `python check_report.py BASE_URL`. Calls `BASE_URL/summary.json` and `BASE_URL/summary.xml`, checks that both answer with status 200 and give the same `total_requests`, and prints `OK total_requests=N`. On any problem it prints `FAIL` and a message, and exits with code 1. |

The whole `PA3_sample.log` gives exactly `PA3_expected_summary.json` and `PA3_expected_summary.xml`. Use them to check your pipeline.

## Stage A. Docker

`app/Dockerfile` builds the image `net2008-pa3:1.0`. It must:

- start from a base image with a fixed tag (not `latest`);
- set a `WORKDIR`;
- copy only what the program needs;
- run as a **non-root user**;
- use the **exec form** of `ENTRYPOINT`, so that the two arguments can be passed;
- prepare an `/out` folder that the non-root user can write to.

Add an `.dockerignore`. Hint: a new named volume copies the owner of the folder in the image.

`run.sh` builds this image with `docker build` before it runs Terraform.

## Stage B. Terraform (folder `infra`)

One `terraform apply` creates the stack, and `terraform destroy` removes it. Use these names:

| Resource | Name and rules |
|---|---|
| Network | `pa3-net` |
| Volume | `pa3-out`, mounted at `/out` in both containers |
| App container | `pa3-app`: image `net2008-pa3:1.0` (built by `run.sh`), runs once with `data/` mounted read-only at `/data`, arguments `/data/access.log /out`. It exits when it is done. Hint: look for `must_run` in the Docker provider documentation. |
| Report container | `pa3-report`: image `debian:bookworm-slim`, command `sleep infinity`, port 80 published on `report_port` |
| Variables | `report_port` (number, default 8800) and `student_id_last4` (string, no default; the last four digits of your student ID, set in `terraform.tfvars`) |
| Labels | Every container has the label `owner` with the value of `student_id_last4` |
| Outputs | `report_url` (for example `http://localhost:8800`) and `student_id_last4` |

The code must pass `terraform fmt -check` and `terraform validate`. Do not commit state files or the `.terraform` folder. Do commit `.terraform.lock.hcl`.

## Stage C. Ansible (folder `ansible`)

- **Inventory:** group `report` with the host `pa3-report`, connected through `community.docker.docker`.
- **Bootstrap play:** installs Python in the container (it has none at the start) without failing on a second run.
- **Main play:** installs nginx, writes the nginx site file from the template below, writes the home page from your own template, and makes sure nginx is running. A **handler** reloads nginx when the site file or the page changes.
- **The page** is a Jinja2 template. It shows the text `Student` followed by `student_id_last4`, and the number `total_requests` that Ansible reads from the summary file inside the container (look at the `slurp` module and the `from_json` filter).
- Every task has a `name`. Variables live in `group_vars/all.yml`. The **second run** of the playbook reports `changed=0` for the host.

Use this nginx site file as a template (`templates/site.conf.j2`) and copy it to `/etc/nginx/sites-enabled/default`. With it, `/summary.json` returns the JSON file, `/summary.xml` returns the XML file and `/` returns your page:

```
server {
    listen 80 default_server;
    root /var/www/html;
    index index.html;
    location = /summary.json { alias /out/summary.json; default_type application/json; }
    location = /summary.xml  { alias /out/summary.xml;  default_type application/xml; }
}
```

## Stage D. The pipeline and the evidence

`run.sh` (bash, `set -euo pipefail`, exit code 0 only if everything worked) does these steps, in this order:

1. `docker build` of the image `net2008-pa3:1.0` from `app/`.
2. `terraform init` and `terraform apply -auto-approve` in `infra/`.
3. `ansible-playbook`, run **twice**, with `student_id_last4` read from the Terraform output (one place for the value).
4. `tools/check_report.py` against `report_url`.

`./run.sh destroy` runs `terraform destroy` so the next run starts from a clean state.

While it runs, `run.sh` saves its results in the `evidence/` folder. You **commit these files**. They show your instructor what happened on your laptop:

| File | Content |
|---|---|
| `evidence/terraform_apply.txt` | The output of `terraform apply` |
| `evidence/ansible_run2.txt` | The second Ansible run (must show `changed=0`) |
| `evidence/check_report.txt` | The output of `check_report.py` |
| `evidence/summary.json` | The summary file that the web server published |

## Stage E. Git and the repository

- `README.md`: **15 lines or fewer**: what it does, what to install, how to run it.
- `.gitignore`: Terraform state files, `.terraform/`, Python caches.
- At least **6 meaningful commits**, with messages that say what changed.
- At least **one feature branch** merged into `main`.
- The tag `v1.0` on the final commit.
- No secrets, no state, no generated files other than `evidence/`.

## How the repository is marked (50 marks)

The repository is checked by reading it and by running parts of it with a different log in `data/access.log`, so your pipeline must not depend on the sample. Finish the stages in order: a pipeline that works up to Stage B still earns most of its marks.

| Stage | What is checked | Marks |
|---|---|---|
| A. Docker | Dockerfile rules (6), the image runs and writes to the volume (2), `.dockerignore` and build in `run.sh` (2) | 10 |
| B. Terraform | `fmt` and `validate` (2), the resources with the right names (6), variables, labels and outputs (4), `apply` and `destroy` work (4) | 16 |
| C. Ansible | Inventory and bootstrap (3), nginx, template and handler (6), second run `changed=0` (3), page and variables (4) | 16 |
| D. Pipeline and evidence | `run.sh` steps and exit code (2), evidence files present and consistent (2) | 4 |
| E. Git and repository | Commits, branch, tag, README and `.gitignore` | 4 |
| **Total** | | **50** |

## Suggested plan for the week

| Work | About |
|---|---|
| Stage A: Dockerfile, test it with `docker run` | 1 hour |
| Stage B: Terraform | 2 hours |
| Week 12 lecture and lab (needed for Stage C) | in class and at home |
| Stage C: Ansible | 2 hours |
| Stage D and E: `run.sh`, evidence, README, tag | 1.5 hours |

Do Stages A and B first. They only need what you already know. Commit after every working step.

## The live demo

The demo is in your lab, **the week after the deadline**. It is worth 50 marks and it is done on your own laptop, one student at a time (about 10 minutes). Bring a laptop with Docker, Terraform and Ansible installed and working.

1. **Clean run (20 marks).** You clone your repository from GitHub into an empty folder and run `./run.sh destroy`. Your instructor gives you a **different log file**. You put it in `data/access.log`, run `./run.sh`, and open the page in the browser. The pipeline must finish with exit code 0, and the page and both summary files must show the new numbers.
2. **Explain (15 marks).** Your instructor points at parts of your code and asks questions from Weeks 9 to 12: for example what a line of the Dockerfile does, what `terraform apply` changes, why the second Ansible run shows `changed=0`, or why the Terraform output feeds the Ansible variable.
3. **A small change (15 marks).** Your instructor asks for one change, for example a new label, a different port, or a different line on the page. You make it, run the pipeline again, and commit it with a clear message.

You must understand every part of the code you submit. You may use the course notes and the official documentation during the demo. A pipeline that fails in the demo can still earn the explanation and change marks for the parts that work.

## Rules

- This is **individual work**. You may use the course material, documentation and tools of your choice, but you must be able to explain every line you submit.
- Do not put passwords, tokens or keys in the repository.
- Keep the repository **public** until the grades are released.
- If you cannot attend the demo, contact your instructor **before** the deadline.

## Files posted with this brief

| File | Use |
|---|---|
| `logsum.py` and `check_report.py` | The two programs you use (do not change them) |
| `PA3_sample.log` | The example log (40 valid lines and 3 malformed lines) |
| `PA3_expected_summary.json` | The JSON that `logsum.py` produces for the sample |
| `PA3_expected_summary.xml` | The XML that `logsum.py` produces for the sample |
