# Week 13 Lab: A CI Pipeline for Bytown Fleet Tools
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). You write a small Python module with tests on **your own laptop**, then build a pipeline for it in **GitHub Actions** and in **Jenkins** (a container on your laptop). You break the build on purpose and fix it.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Docker must be running. You need Python 3, Git, and a GitHub account with an SSH key (see [W09_Setup_Your_Laptop.md](../week09/lab/W09_Setup_Your_Laptop.md)).
- Do the parts in order. Use the **exact** names and file names given here. The self-check and your instructor look for them.
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
mkdir -p ~/bytown-ci/evidence && cd ~/bytown-ci && git init -b main  # Create the lab repository, with a folder for proof.
```

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -q pytest ruff  # Private Python environment with the test and lint tools.
```

```bash
printf '.venv/\n__pycache__/\n.pytest_cache/\n.ruff_cache/\n' > .gitignore  # Do not commit the environment or caches.
```

**If you close the terminal**, open a new one, run `export SEED=...`, `cd ~/bytown-ci` and `source .venv/bin/activate`.

---
## Part 1. The module and its tests (5 points)

The module has your seed written in it. The shell inserts it:

```bash
cat > fleet.py <<EOF
"""Small helpers for the Bytown fleet tools."""

SEED = $SEED


def uptime_percent(up, total):
    """Return the percentage of devices that are up, rounded to 1 decimal. 0 devices gives 0.0."""
    if total <= 0:
        return 0.0
    return round(100 * up / total, 1)


def mgmt_port(index):
    """Return the management port of device number index: 9000 + SEED * 10 + index."""
    return 9000 + SEED * 10 + index
EOF
```

Write the tests. You must have **at least five** test functions, and at least one must check the port of device 3 with your own seed, written as a number:

```bash
cat > test_fleet.py <<EOF
from fleet import SEED, mgmt_port, uptime_percent


def test_seed_is_yours():
    assert SEED == $SEED


def test_port_of_device_3():
    assert mgmt_port(3) == $((9000 + SEED * 10 + 3))


def test_uptime_all_up():
    assert uptime_percent(10, 10) == 100.0


def test_uptime_rounding():
    assert uptime_percent(1, 3) == 33.3


def test_uptime_no_devices():
    assert uptime_percent(0, 0) == 0.0
EOF
```

```bash
ruff check .  # Lint. You must see "All checks passed!".
```

```bash
pytest -q 2>&1 | tee evidence/part1-pytest.txt  # Run the tests and save the output. You must see "5 passed".
```

---
## Part 2. GitHub Actions (6 points)

Create the workflow. Your seed goes in an environment variable, and the image tag uses it:

```bash
mkdir -p .github/workflows  # GitHub reads workflows from this folder.
```

```bash
cat > .github/workflows/ci.yml <<EOF
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  SEED: "$SEED"

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - name: Get the code
        uses: actions/checkout@v4
      - name: Install Python \${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: \${{ matrix.python-version }}
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
      - name: Build the image
        run: |
          printf 'FROM python:3.12-slim\nCOPY fleet.py /app/fleet.py\nWORKDIR /app\n' > Dockerfile
          docker build -t bytown-ci:seed-\$SEED .
      - name: Run the image
        run: docker run --rm bytown-ci:seed-\$SEED python -c "import fleet; print(fleet.mgmt_port(3))"
EOF
```

```bash
grep -n "SEED\|matrix" .github/workflows/ci.yml  # Check: your seed appears in env, and the matrix lines are there.
```

Create an **empty public** repository named `bytown-ci` at <https://github.com/new> (no README). Then:

```bash
git add -A && git commit -m "Add fleet module, tests and CI workflow"  # Save everything.
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-ci.git  # Link the GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload. The push starts the workflow.
```

Open `https://github.com/YOUR-USERNAME/bytown-ci/actions`. Wait until the run **CI** is green (three check marks in the graph: two `test` jobs and `package`). Click the run and copy its address from the browser. It looks like `https://github.com/YOUR-USERNAME/bytown-ci/actions/runs/1234567890`. Save it:

```bash
echo "https://github.com/YOUR-USERNAME/bytown-ci/actions/runs/PASTE-THE-NUMBER" > evidence/actions-green.txt  # Save the address of the green run. Replace the parts in capitals.
```

---
## Part 3. Break it and fix it (2 points)

On a branch, break the code, push, and watch the pull request go red:

```bash
git switch -c break-it  # Create a branch for the experiment.
```

```bash
sed -i.bak 's/return round(100 \* up \/ total, 1)/return round(up \/ total, 1)/' fleet.py && rm fleet.py.bak  # Introduce a bug: forget the 100.
```

```bash
git commit -am "Break uptime_percent on purpose" && git push -u origin break-it  # Push the broken branch.
```

On GitHub, open a pull request from `break-it` into `main`. Wait for the check to turn **red**. Open the failed run and copy its address:

```bash
echo "https://github.com/YOUR-USERNAME/bytown-ci/actions/runs/PASTE-THE-NUMBER" > evidence/actions-red.txt  # Save the address of the red run. Replace the parts in capitals.
```

Fix it with a revert and push:

```bash
git revert --no-edit HEAD && git push  # Undo the bug with a new commit. The pull request turns green again.
```

```bash
git switch main && git merge break-it && git push  # Bring the branch (bug and revert) into main. The history keeps the story.
```

---
## Part 4. Jenkins (5 points)

```bash
docker run -d --name jenkins -p 8080:8080 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts-jdk17  # Start Jenkins (as in the lecture). If the name exists, run docker start jenkins instead.
```

```bash
docker exec -u root jenkins sh -c "apt-get update -qq && apt-get install -y -qq python3 python3-pytest"  # Install Python and pytest in the container. One minute.
```

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword  # The one-time password. Open http://localhost:8080 and finish the setup (suggested plug-ins, admin user).
```

Create the Jenkinsfile. The stage names include your seed:

```bash
cat > Jenkinsfile <<EOF
pipeline {
    agent any
    environment {
        SEED = '$SEED'
    }
    stages {
        stage('Show the commit') {
            steps {
                sh 'git log -1 --oneline'
            }
        }
        stage('Test seed $SEED') {
            steps {
                sh 'python3 -m pytest -q'
            }
        }
        stage('Check the port') {
            steps {
                sh 'python3 -c "import fleet; print(fleet.mgmt_port(3))"'
            }
        }
    }
    post {
        always {
            echo "Pipeline finished for seed \$SEED"
        }
    }
}
EOF
```

```bash
git add Jenkinsfile && git commit -m "Add Jenkinsfile" && git push  # Push the Jenkinsfile to main.
```

In Jenkins: **New Item**, name **`bytown-ci`**, type **Pipeline**. Pipeline definition: **Pipeline script from SCM**, SCM **Git**, Repository URL `https://github.com/YOUR-USERNAME/bytown-ci.git`, Branch `*/main`, Script Path `Jenkinsfile`. Save and click **Build Now**. When build `#1` is green, save its log:

```bash
docker exec jenkins cat /var/jenkins_home/jobs/bytown-ci/builds/1/log > evidence/jenkins-console.txt  # Copy the console log of build 1 into your evidence folder.
```

```bash
tail -3 evidence/jenkins-console.txt  # The last line must be "Finished: SUCCESS".
```

---
## Part 5. Answers (2 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. Why does the job `package` have `needs: test`? What happens to `package` when one `test` job fails?
2. What is the difference between Continuous Delivery and Continuous Deployment?
3. Why does the Jenkinsfile use polling or a manual build instead of a webhook on your laptop?

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

The self-check reads your files, runs `ruff` and `pytest` on your code, and changes nothing. Run it from your lab folder:

```bash
python3 ~/net2008-devops/week13/W13_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again. The self-check cannot see GitHub: your instructor opens your two Actions runs.

## Clean up

```bash
docker stop jenkins  # Stop Jenkins. Your files stay. (docker rm -f jenkins and docker volume rm jenkins_home delete everything.)
```

## Submit

```bash
git add -A && git commit -m "Week 13 lab: ci" && git push  # Save the last changes (answers and evidence) and upload.
```

1. Open the repository in a private (incognito) window. If you can see it, your instructor can.
2. Open **Week 13 Lab Submission** on Brightspace and submit **only the URL** of the repository.
3. Do not push after the deadline.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Module with your seed, five or more tests that pass, lint clean | 5 |
| 2 | Workflow with triggers, matrix, lint, test, `needs`, image build; a green run on GitHub | 6 |
| 3 | A red run, then a revert commit and a green run | 2 |
| 4 | Jenkinsfile with stages, a successful build log | 5 |
| 5 | `answers.txt` (read by your instructor) | 2 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$SEED` is empty and `SEED = ` is blank in `fleet.py` | The variable was lost. Run `export SEED=...`, delete `fleet.py`, `test_fleet.py`, and repeat Part 1. |
| `ruff: command not found` | `source .venv/bin/activate`. |
| The workflow does not appear on GitHub | The file is not at `.github/workflows/ci.yml`, or it is not pushed. |
| `Invalid workflow file` | YAML indentation. The Actions page shows the line. |
| `${{ matrix... }}` shows as `{{ matrix... }}` in `ci.yml` | In the heredoc each `$` must be written `\$`. Copy the box again exactly. |
| The `package` job is skipped | A `test` job failed. Open it and read the red step. |
| Pull request stays yellow | Wait a minute. Checks need time to start. |
| Jenkins: `python3: not found` | You skipped the `apt-get install` command. |
| Jenkins: `Repository not found` | Use the `https://` address of your **public** repository. |
| `builds/1/log: No such file` | The job is not named `bytown-ci`, or build 1 did not run. Check the name. |
| `docker: Cannot connect to the Docker daemon` | Start Docker Desktop. |
