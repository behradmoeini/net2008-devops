# Week 13 Lecture: CI/CD with GitHub Actions and Jenkins
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Git and a GitHub account with an SSH key (Week 6), Python 3 and Docker (Week 9). GitHub Actions runs on GitHub's computers, so it costs your laptop nothing. Jenkins runs in one Docker container on your laptop (about 1 GB of memory).

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- Do the steps in order. All practice work happens in one folder, `~/ci-practice`.

---
## The big picture: read this first

### The problem

Five developers change the same code every day. Someone breaks the build and nobody notices for a week. Releases are a stressful manual event, done on Friday evening. **CI/CD** removes this by running the same automatic checks on **every change**.

| Term | Meaning |
|---|---|
| **Continuous Integration (CI)** | Every push is built and tested automatically. A broken change is found in minutes, by a machine, not by a customer. |
| **Continuous Delivery** | Every change that passes is **ready** to release. A person presses the button. |
| **Continuous Deployment** | Every change that passes is released **automatically**. |
| **Pipeline** | The ordered stages a change goes through: build, test, package, deploy |
| **Artifact** | A file that a pipeline produces: a Docker image, a package, a report |

### A pipeline in one picture

```text
git push --> checkout --> install --> lint --> test --> build image --> (deploy)
   |                                              |
   +------------- any red stage stops the pipeline and tells you
```

**Fail fast:** cheap checks (lint, unit tests) come first, slow ones (build, deploy) last. **A red pipeline is the team's top priority.**

### Two tools, one idea

| | GitHub Actions | Jenkins |
|---|---|---|
| Where it runs | GitHub's computers (a "runner" per job) | A server you run yourself (here: a container) |
| Pipeline file | `.github/workflows/NAME.yml` | `Jenkinsfile` in the repository |
| Language | YAML | Groovy (declarative form) |
| Setup effort | None: add a file | Install, plug-ins, jobs |
| Typical use | Open source and cloud projects | Company servers, special hardware, private networks |

Both keep the pipeline **as code in the repository**: it is reviewed and versioned like the program.

---
## Part A. GitHub Actions

### Step 1. A small project with tests

```bash
mkdir -p ~/ci-practice && cd ~/ci-practice && git init -b main  # Create the project folder and make it a Git repository.
```

```bash
cat > calc.py <<'EOF'
"""A tiny module to test."""


def average(numbers):
    """Return the average of a list of numbers. An empty list gives 0."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
EOF
```

```bash
cat > test_calc.py <<'EOF'
from calc import average


def test_average_of_three():
    assert average([1, 2, 3]) == 2


def test_average_of_empty_list():
    assert average([]) == 0
EOF
```

A **test** is a function whose name starts with `test_` and that uses `assert`. If an `assert` is false, the test fails. The tool **pytest** finds and runs them.

```bash
python3 -m venv .venv && source .venv/bin/activate  # Create and activate a private Python environment for this project.
```

```bash
pip install -q pytest ruff  # Install pytest (runs tests) and ruff (a fast style and error checker, a "linter").
```

```bash
ruff check .  # Lint: look for mistakes without running the code. You should see "All checks passed!".
```

```bash
pytest -q  # Run the tests. You should see "2 passed".
```

### Step 2. Your first workflow

A **workflow** is a YAML file in `.github/workflows/`. GitHub runs it when its trigger happens.

```bash
mkdir -p .github/workflows  # GitHub looks for workflows in exactly this folder.
```

```bash
cat > .github/workflows/ci.yml <<'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Get the code
        uses: actions/checkout@v4
      - name: Install Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install the tools
        run: pip install pytest ruff
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest -q
EOF
```

Read it:

| Part | Meaning |
|---|---|
| `name` | The name shown in the Actions tab |
| `on` | The **triggers**: every push to `main`, and every pull request |
| `jobs` | The jobs. Each job runs on its own fresh computer. |
| `runs-on` | The type of runner: a new Ubuntu virtual machine |
| `steps` | The commands, in order. A failed step stops the job. |
| `uses` | Reuse a ready-made action (check out the code, install Python). `@v4` is its version. |
| `run` | Run a shell command |

Create `.gitignore` so you do not upload your environment, then commit and push to a **new public GitHub repository** named `ci-practice` (create the empty repository on <https://github.com/new> first):

```bash
printf '.venv/\n__pycache__/\n.pytest_cache/\n.ruff_cache/\n' > .gitignore  # Do not commit the environment or caches.
```

```bash
git add -A && git commit -m "Add calc, tests and CI workflow"  # Save everything.
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/ci-practice.git  # Link the GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload. This push triggers the workflow.
```

Open `https://github.com/YOUR-USERNAME/ci-practice/actions`. You see a run named **CI**. Click it, then the job `test`, and open each step. A yellow circle means running, a green check means success, a red cross means failure.

### Step 3. Make it fail, then fix it

A failing test is the pipeline doing its job. Break the code on purpose, **on a branch**:

```bash
git switch -c break-it  # Create a branch for the experiment.
```

```bash
sed -i.bak 's/return sum(numbers) \/ len(numbers)/return sum(numbers)/' calc.py && rm calc.py.bak  # Introduce a bug: forget to divide.
```

```bash
pytest -q  # The test fails on your laptop too. In real life you would notice here. We continue to see the server catch it.
```

```bash
git commit -am "Break average on purpose" && git push -u origin break-it  # Push the broken branch.
```

On GitHub, open a **pull request** from `break-it` into `main` (the yellow banner offers it). Wait one minute: the pull request shows **a red cross and "Some checks were not successful"**. This is the protection: the broken code cannot be merged by accident.

Fix it:

```bash
git revert --no-edit HEAD  # Undo the breaking commit with a new commit (as in Week 6).
```

```bash
git push  # Push the fix. The pull request re-runs the checks and turns green.
```

You could now merge the pull request on GitHub (we do not need to here).

### Step 4. A matrix: many versions at once

Your program must work on several Python versions. A **matrix** runs the same job once per value:

```bash
git switch main  # Back to main.
```

```bash
cat > .github/workflows/ci.yml <<'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - name: Get the code
        uses: actions/checkout@v4
      - name: Install Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install the tools
        run: pip install pytest ruff
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest -q

  package:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Get the code
        uses: actions/checkout@v4
      - name: Build an image
        run: |
          printf 'FROM python:3.12-slim\nCOPY calc.py /app/calc.py\nWORKDIR /app\n' > Dockerfile
          docker build -t ci-practice:${{ github.sha }} .
      - name: Run the image
        run: docker run --rm ci-practice:${{ github.sha }} python -c "import calc; print(calc.average([2, 4]))"
EOF
```

New ideas:

| Syntax | Meaning |
|---|---|
| `strategy.matrix` | Run the job once for each Python version (three jobs, in parallel) |
| `${{ matrix.python-version }}` | The value for the current copy |
| `needs: test` | The job `package` starts only after **all** `test` jobs succeed |
| `run: \|` | A multi-line command. Each line runs in order. |
| `${{ github.sha }}` | The ID of the commit that triggered the run |

```bash
git commit -am "Test on three Python versions and build an image" && git push  # Push to main. Watch the Actions tab: three test jobs, then package.
```

### Secrets (read only)

A pipeline often needs a password or a token. **Never write it in the workflow.** On GitHub: repository Settings > Secrets and variables > Actions. A workflow reads it as `${{ secrets.NAME }}`, and GitHub hides it in the logs.

---
## Part B. Jenkins

Jenkins is a server that runs pipelines. You run it in a container on your laptop.

### Step 5. Start Jenkins

```bash
docker run -d --name jenkins -p 8080:8080 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts-jdk17  # Start Jenkins. The volume keeps its settings. Port 8080 is the web page.
```

```bash
docker exec -u root jenkins sh -c "apt-get update -qq && apt-get install -y -qq python3 python3-pytest"  # Install Python and pytest inside the Jenkins container, so the pipeline can run your tests. This takes a minute.
```

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword  # Print the one-time password. Wait about a minute after the start if the file is not there yet. Copy it.
```

Open <http://localhost:8080>. Paste the password. Click **Install suggested plugins** (takes a few minutes), create an admin user (remember it), keep the default Jenkins URL, and click **Start using Jenkins**.

### Step 6. A Jenkinsfile

A **Jenkinsfile** lives in your repository and describes the pipeline. The **declarative** form has a fixed shape:

```bash
cd ~/ci-practice  # Go back to your project.
```

```bash
cat > Jenkinsfile <<'EOF'
pipeline {
    agent any
    triggers {
        pollSCM('* * * * *')
    }
    stages {
        stage('Show the commit') {
            steps {
                sh 'git log -1 --oneline'
            }
        }
        stage('Test') {
            steps {
                sh 'python3 -m pytest -q'
            }
        }
    }
    post {
        always {
            echo 'Pipeline finished'
        }
    }
}
EOF
```

| Part | Meaning |
|---|---|
| `pipeline { ... }` | The whole pipeline |
| `agent any` | Run on any available Jenkins computer (here: the one container) |
| `triggers { pollSCM(...) }` | Ask Git for changes every minute (a laptop cannot receive webhooks from the internet) |
| `stages` and `stage` | The named steps of the pipeline. They show as boxes in Jenkins. |
| `steps` and `sh` | Run a shell command |
| `post { always { ... } }` | What to do at the end, whatever the result |

```bash
git add Jenkinsfile && git commit -m "Add Jenkinsfile" && git push  # Push the Jenkinsfile to GitHub (to main). Jenkins reads it from there.
```

### Step 7. A Jenkins job

In the Jenkins page: **New Item** > name `ci-practice` > **Pipeline** > OK. Scroll to **Pipeline**:

- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `https://github.com/YOUR-USERNAME/ci-practice.git` (the **https** address; the repository is public)
- Branch Specifier: `*/main`
- Script Path: `Jenkinsfile`

Click **Save**, then **Build Now**. Click the build number (`#1`) and **Console Output**. You see `Finished: SUCCESS` and the stages. Make a small change, push, and wait one minute: Jenkins starts build `#2` by itself (polling).

```bash
docker stop jenkins  # Stop Jenkins when you are done. docker start jenkins brings it back with all its settings.
```

## Cheat sheet

| Task | GitHub Actions | Jenkins |
|---|---|---|
| Pipeline file | `.github/workflows/*.yml` | `Jenkinsfile` |
| Run a command | `run: cmd` | `sh 'cmd'` |
| Build stages | `jobs` and `steps` | `stage` and `steps` |
| Run when | `on: push` | `triggers`, "Build Now" |
| Many versions | `strategy.matrix` | not shown here |
| Order of jobs | `needs:` | order of `stage` |
| Hide a secret | `${{ secrets.NAME }}` | Credentials plug-in |

## If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| The workflow does not appear in the Actions tab | The file is not in `.github/workflows/` (check the spelling), or it is not on `main`, or it is not pushed. |
| `Invalid workflow file` | A YAML error: indentation or a tab. The Actions page shows the line. |
| `ruff: command not found` in the workflow | The "Install the tools" step is missing or failed. |
| Test passes on your laptop, fails on GitHub | Different Python version, or a file you did not commit. Check `git status`. |
| `package` job does not start | The `test` jobs failed, or `needs:` has a typo. |
| Jenkins page does not open | Wait one minute after `docker run`, then check `docker logs jenkins`. |
| Jenkins build: `python3: not found` | You skipped the `apt-get install` command of Step 5. |
| Jenkins build: `Repository not found` | Use the `https://` URL of a **public** repository, with no typo. |
| `docker: Cannot connect to the Docker daemon` | Start Docker Desktop. |

## Summary

- CI runs checks on every push. CD makes every passing change ready (or live). A red pipeline is fixed first.
- GitHub Actions: a YAML workflow in `.github/workflows/`. Jobs run on fresh runners. A matrix repeats a job. `needs` orders jobs. Secrets are never written in the file.
- Jenkins: a server you run, with a `Jenkinsfile` of stages in your repository.
- Both keep the pipeline as code, reviewed with the program.

**Next:** the Week 13 lab (graded) builds a CI pipeline with your own seed, in both tools.
