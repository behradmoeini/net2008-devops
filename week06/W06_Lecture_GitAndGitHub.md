# Week 6 Lecture: Git and GitHub
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal inside GitHub Codespaces. You install nothing, and it works the same on Windows, macOS and Linux.

## How to follow this guide

- Keep this page in one browser tab and your Codespace in another.
- Every grey box is **one command**. Everything after the `#` at the end of the line is a comment that says what the command does. The terminal ignores it. Copy the whole line, paste it into the terminal with `Ctrl+V` (Windows, Linux) or `Cmd+V` (macOS), press Enter, then go to the next box.
- **You should see** shows roughly what the terminal prints. IDs like `a1b2c3d` will differ.
- Do the steps in order. Each step builds on the one before.
- All practice work happens in one folder, `~/netops-practice`.

---
## The big picture: read this first

You do not need to know anything about Git yet. Read this section once, then start Step 1.

### The problem

Imagine you keep your router configuration in a shared folder:

```text
core-rtr.cfg
core-rtr_old.cfg
core-rtr_final.cfg
core-rtr_final_v2_REAL.cfg
```

Which file is current? What changed between two of them? Who changed it, and why? What if two people edit the same file at the same time? **Version control** solves this. It keeps the full history of your files, lets you go back to any earlier version, and lets many people work on the same project safely.

### Git and GitHub are different things

| | What it is |
|---|---|
| **Git** | A program on your computer that tracks changes to your files. It works offline. |
| **GitHub** | A website that stores a copy of your Git projects online, so you can back them up, share them and work with a team. |

### Five words to know

| Word | Meaning |
|---|---|
| **Repository** (repo) | A project folder that Git tracks, together with its full history |
| **Commit** | A saved snapshot of your files, with a message that says what changed |
| **Branch** | A separate line of work, so you can experiment without breaking the main version (`main`) |
| **Remote** | A copy of the repository somewhere else, usually on GitHub. It is named `origin` |
| **Pull request** | A request on GitHub to merge one branch into another, which teammates can review first |

### The lifecycle of a change

Your work moves through four places. Learn this picture: the rest of the lecture is just walking through it.

![The Git lifecycle: working directory, staging area, local repository and GitHub, with the command that moves a change between them](images/git-lifecycle.svg)

| Place | What it is | Command that moves a change forward |
|---|---|---|
| **Working directory** | The files you edit | `git add` |
| **Staging area** | The changes you picked for the next commit | `git commit` |
| **Local repository** | The saved history, in a hidden `.git` folder | `git push` |
| **GitHub (origin)** | The copy online | |

The orange arrows go the other way: `git restore` throws away an edit, `git restore --staged` takes a file out of staging, and `git pull` brings new work down from GitHub.

The bottom row of the picture is what `git status` tells you about a file: **untracked** (new, Git has never seen it), **modified** (changed since the last commit), **staged** (picked with `git add`), **committed** (saved).

In one sentence: **you edit files, choose which changes to keep with `git add`, save them with `git commit`, and share them with `git push`.**

---
## Step 1. Open a Codespace

A Codespace is a Linux computer that GitHub runs for you. You use it in your browser.

1. Sign in at <https://github.com>.
2. Open the course repository (link in Brightspace).
3. Click the green **<> Code** button, the **Codespaces** tab, then **Create codespace on main**. Wait one to two minutes.
4. Find the **terminal** at the bottom. If it is hidden, press `Ctrl+` and the backtick key.

Your prompt looks like this. The word in brackets is your Git branch:

```text
@your-username ➜ /workspaces/net2008-devops (main) $
```

Run these five commands once, one at a time. They check your tools and keep Git from opening extra windows:

```bash
git --version  # Print the installed Git version, to prove Git works.
```

```bash
export GIT_PAGER=cat  # Stop Git from opening a scrolling viewer for long output.
```

```bash
export GIT_EDITOR=true  # Stop Git from opening a text editor when it wants a message.
```

```bash
git config --global user.name  # Show the name Git will put on your commits.
```

```bash
git config --global user.email  # Show the email Git will put on your commits.
```

You should see a Git version, then your name and email. If the last two print nothing:

```bash
git config --global user.name  "Your Name"  # Set your name for every commit you make.
```

```bash
git config --global user.email "you@example.com"  # Set your email for every commit you make.
```

When you finish for the day: <https://github.com/codespaces>, three dots, **Stop codespace**. Your files are kept.

---
## Step 2. Create a repository

A **repository** (repo) is a folder whose history Git tracks.

```bash
mkdir -p ~/netops-practice  # Create the practice folder (no error if it already exists).
```

```bash
cd ~/netops-practice  # Move the terminal into the practice folder.
```

```bash
git init -b main  # Turn this folder into a Git repository with a branch named main.
```

```bash
git status  # Show the state of your repository: new, changed and staged files.
```

You should see `Initialized empty Git repository` and `No commits yet`. `git status` is the command you will use most. Run it often.

**Remember:** Git keeps the whole history in a hidden folder named `.git` inside your project folder. Never edit it by hand. Delete it and the repository is gone.

---
## Step 3. Make commits

A **commit** is a saved snapshot of your files. Every change goes through three steps, matching the lifecycle picture you saw in "The big picture": **edit, `git add`, `git commit`**.

Create a file and check what Git sees:

```bash
printf 'hostname core-rtr-01\nntp server 10.0.0.10\n' > core-rtr.cfg  # Create core-rtr.cfg containing two lines of router config.
```

```bash
git status  # Show the state again: core-rtr.cfg should now be listed as modified.
```

You should see `core-rtr.cfg` under **Untracked files**. Stage it, then commit it:

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg so it goes into the next commit.
```

```bash
git commit -m "Add core router config"  # Save the staged file as a commit with this message.
```

```bash
git log --oneline  # Show the history, one short line per commit.
```

You should see one line with an ID and your message. Write messages that start with a verb and say what changed.

Change the file and look at the difference. Lines starting with `+` were added:

```bash
echo "snmp-server community netops-ro RO" >> core-rtr.cfg  # Append one line to the end of core-rtr.cfg.
```

```bash
git status  # Show the state: both new files are listed as untracked.
```

```bash
git diff  # Show what changed in your files since the last commit (+ is added).
```

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg so it goes into the next commit.
```

```bash
git commit -m "Enable SNMP read-only"  # Save the staged change as a commit with this message.
```

```bash
git log --oneline  # Show the history, one short line per commit.
```

The `git status` above shows `core-rtr.cfg` as **modified, not staged for commit**. The three states you will see:

| `git status` says | Meaning |
|---|---|
| Untracked | Git has never seen the file |
| Modified, not staged | A tracked file changed, but you have not run `git add` |
| Changes to be committed | Staged, ready for `git commit` |

`git log --oneline` prints the history, one short line per commit.

---
## Step 4. Ignore files

Logs and passwords must never be committed. A `.gitignore` file tells Git to skip them:

```bash
echo "noisy log line" > router.log  # Create a log file that should never be committed.
```

```bash
echo "ADMIN_PASSWORD=do-not-commit" > secrets.env  # Create a fake secrets file that should never be committed.
```

```bash
git status  # Show the state: only .gitignore is listed now, the ignored files are hidden.
```

```bash
printf '*.log\nsecrets.env\n' > .gitignore  # Write the .gitignore file: skip every .log file and secrets.env.
```

```bash
git status  # Show the state: it should say the working tree is clean.
```

The first `git status` lists both files. The second lists only `.gitignore`. Commit it:

```bash
git add .gitignore  # Stage .gitignore so it goes into the next commit.
```

```bash
git commit -m "Add .gitignore"  # Save .gitignore as a commit.
```

**Important:** `.gitignore` only affects files Git is **not yet tracking**. If `secrets.env` had already been committed, adding it to `.gitignore` would not help: Git would keep tracking it, and it stays in the history. Ignore a file **before** you first commit it.

---
## Step 5. Undo mistakes

| Situation | Command |
|---|---|
| Edited a file (not committed), want the last saved version back | `git restore FILE` |
| A commit was wrong | `git revert COMMIT` |

Throw away an edit:

```bash
echo "THIS IS A MISTAKE" >> core-rtr.cfg  # Append a bad line to the file, as a pretend mistake.
```

```bash
git restore core-rtr.cfg  # Throw away your uncommitted edits and bring back the last saved version.
```

```bash
cat core-rtr.cfg  # Print the file to check its contents.
```

The bad line is gone for good. `git restore` cannot be undone.

Undo a commit. First make a bad one:

```bash
printf 'interface Gi0/1\n shutdown\n' >> core-rtr.cfg  # Append a bad config (shuts down an interface) to the file.
```

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg so it goes into the next commit.
```

```bash
git commit -m "Shut down core uplink"  # Save the bad change as a commit, so we can practice undoing it.
```

`git revert` adds a **new commit** that cancels it. Nothing is erased, so it is safe:

```bash
git revert --no-edit HEAD  # Add a new commit that cancels the latest commit, keeping the default message.
```

```bash
git log --oneline  # Show the history, one short line per commit.
```

You should see a new commit that starts with `Revert`. The wrong commit stays in the history, and the new one undoes it.

---
## Step 6. Branches and merging

A **branch** is a separate line of work. You can experiment without touching `main`, then merge it back.

```bash
git switch -c guest-vlan  # Create a new branch called guest-vlan and switch to it.
```

```bash
printf 'vlan 200\n name guest\n' >> core-rtr.cfg  # Append a guest VLAN config to the file (on this branch only).
```

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg so it goes into the next commit.
```

```bash
git commit -m "Add guest VLAN"  # Save the VLAN change as a commit on the guest-vlan branch.
```

```bash
git switch main  # Switch back to the main branch.
```

```bash
cat core-rtr.cfg  # Print the file: the VLAN lines should not be there yet, because they are on another branch.
```

The VLAN is not on `main` yet. Merge the branch in:

```bash
git merge guest-vlan  # Bring the commits from guest-vlan into the branch you are on (main).
```

```bash
cat core-rtr.cfg  # Print the file: the VLAN lines are now on main.
```

```bash
git log --oneline --graph --all  # Show every branch in the history as a graph.
```

```bash
git branch -d guest-vlan  # Delete the guest-vlan branch. Its work is already merged into main.
```

You should see `Fast-forward`, and the VLAN is now on `main`.

A **fast-forward** is possible when `main` has no new commits since the branch was created. Git just moves the `main` pointer forward. If `main` has moved on, Git makes a **merge commit** instead (you will see this in Step 7).

---
## Step 7. Fix a merge conflict

A **conflict** happens when two branches change the **same line**. Git cannot choose, so you do. Conflicts are normal.

Set it up: the same line is changed two different ways.

```bash
echo "ntp server 10.0.0.10" > ntp.cfg  # Create ntp.cfg with one line.
```

```bash
git add ntp.cfg  # Stage ntp.cfg so it goes into the next commit.
```

```bash
git commit -m "Add NTP config"  # Save ntp.cfg as a commit.
```

```bash
git switch -c ntp-primary  # Create a new branch called ntp-primary and switch to it.
```

```bash
echo "ntp server 10.0.0.11" > ntp.cfg  # Overwrite ntp.cfg with a different server (this branch).
```

```bash
git commit -a -m "Use primary NTP server"  # Stage all changes to tracked files and commit them in one step.
```

```bash
git switch main  # Switch back to the main branch.
```

```bash
echo "ntp server 10.0.0.12" > ntp.cfg  # Overwrite the same line with another server (on main).
```

```bash
git commit -a -m "Use backup NTP server"  # Stage all changes to tracked files and commit them in one step.
```

```bash
git merge ntp-primary  # Merge ntp-primary into main. Both changed the same line, so this conflicts.
```

```bash
cat ntp.cfg  # Print ntp.cfg to see the conflict markers Git inserted.
```

You should see `CONFLICT` and a file that looks like this:

```text
<<<<<<< HEAD
ntp server 10.0.0.12
=======
ntp server 10.0.0.11
>>>>>>> ntp-primary
```

The top half is your side, the bottom half is the other side. You decide what the file should say and delete the three marker lines. We keep both servers:

```bash
printf 'ntp server 10.0.0.11 prefer\nntp server 10.0.0.12\n' > ntp.cfg  # Replace the conflicted file with the final text we chose (markers removed).
```

```bash
git add ntp.cfg  # Mark the conflict as resolved by staging the fixed ntp.cfg.
```

```bash
git commit --no-edit  # Finish the merge with Git's default merge message.
```

```bash
git branch -d ntp-primary  # Delete the ntp-primary branch. Its work is already merged.
```

```bash
git log --oneline --graph --all  # Show every branch in the history as a graph.
```

The markers are `<<<<<<<`, `=======` and `>>>>>>>`. The three steps for any conflict: **edit the file, `git add` it, `git commit`**.

---
## Step 8. Put your repository on GitHub

**GitHub** stores a copy of your repository online. That copy is called a **remote**, named `origin`. In a Codespace you are already signed in. Create the GitHub repo from your folder and push:

```bash
gh repo create netops-practice --public --source=. --remote=origin --push  # Create a public GitHub repo from this folder, link it as origin, and upload your commits.
```

```bash
git remote -v  # List the remotes (online copies) this repository knows about.
```

```bash
gh repo view --web  # Open this repository on github.com in your browser.
```

Your repository opens in the browser, with your files and commits.

**Without `gh`:** create an empty repository on github.com (no README), then run:

```bash
git remote add origin https://github.com/YOUR-USERNAME/netops-practice.git  # Link your empty GitHub repo to this folder under the name origin.
```

```bash
git push -u origin main  # Upload main to origin and remember it as the default for git push and git pull.
```

`git push -u origin main` uploads `main` to the remote named `origin` and sets it as the **upstream** of your local `main`. After that you can type just `git push` and `git pull`.

**Never use `git push --force` on a shared branch.** It can overwrite commits on GitHub and destroy your teammates' work.

---
## Step 9. Pull changes from GitHub

Other people change the repository too. You play the teammate by editing on GitHub.

1. In the browser, open `core-rtr.cfg` in your repository and click the **pencil** icon.
2. Add the line `logging host 10.0.0.50` at the bottom.
3. Click **Commit changes**, type the message `Send syslog to collector`, and commit.

Your Codespace does not have it yet. Download it:

```bash
git pull  # Download new commits from GitHub and merge them into your branch.
```

```bash
cat core-rtr.cfg  # Print the file: the new syslog line from GitHub should be there.
```

You should see the new line in your file.

| Command | What it does |
|---|---|
| `git fetch` | Downloads new commits but does **not** change your branch |
| `git pull` | `git fetch` and then a merge into your branch |
| `git push` | Uploads your commits to GitHub |

Habit: `git pull` before you start, `git push` when you finish.

---
## Step 10. Tag a release

A **tag** names one commit as a release, with a version like `v1.0.0` (MAJOR.MINOR.PATCH).

```bash
git tag -a v1.0.0 -m "First release"  # Label the current commit v1.0.0, with a message.
```

```bash
git push origin v1.0.0  # Upload the v1.0.0 tag to GitHub (tags are not pushed automatically).
```

```bash
git tag  # List all tags in this repository.
```

Version numbers follow **semantic versioning**, MAJOR.MINOR.PATCH:

| Change | Number that goes up | Example |
|---|---|---|
| Breaking change | MAJOR | v1.4.2 to v2.0.0 |
| New feature, backward compatible | MINOR | v1.4.2 to v1.5.0 |
| Bug fix, backward compatible | PATCH | v1.4.2 to v1.4.3 |

---
## Step 11. A pull request

On a team, nobody edits `main` directly. You work on a branch, push it, and open a **pull request** (PR): a request to merge changes from one branch into another, which teammates can review first.

```bash
git switch -c add-banner  # Create a new branch called add-banner and switch to it.
```

```bash
echo "banner motd Authorized access only" >> core-rtr.cfg  # Append a login banner line to the file.
```

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg so it goes into the next commit.
```

```bash
git commit -m "Add login banner"  # Save the banner change as a commit.
```

```bash
git push -u origin add-banner  # Upload the add-banner branch to GitHub and set it as its upstream.
```

```bash
gh pr create --base main --head add-banner --title "Add login banner" --body "Adds a login banner."  # Open a pull request on GitHub that asks to merge add-banner into main.
```

`gh` prints a link. Open it. Click **Merge pull request**, then **Confirm merge**. Then bring `main` up to date:

```bash
git switch main  # Switch back to the main branch.
```

```bash
git pull  # Bring your local main up to date with GitHub, including the merged pull request.
```

```bash
git log --oneline --graph -5  # Show the last 5 commits as a short list with a branch graph.
```

You should see your banner commit on `main`.

---
## Finish

```bash
git status  # Show the state of your repository. It should be clean.
```

You should see `nothing to commit, working tree clean`. Stop your Codespace (Step 1). To start over, delete the practice folder:

```bash
cd ~  # Go back to your home folder.
```

```bash
rm -rf ~/netops-practice  # Delete the practice folder and everything in it. This cannot be undone.
```

---
## Command cheat sheet

| I want to... | Command |
|---|---|
| Start a repository | `git init -b main` |
| See what is going on | `git status` |
| Stage / commit | `git add FILE` / `git commit -m "message"` |
| See changes | `git diff` |
| See history | `git log --oneline --graph --all` |
| Discard an edit | `git restore FILE` |
| Undo a commit safely | `git revert COMMIT` |
| New branch / switch branch | `git switch -c NAME` / `git switch NAME` |
| Merge a branch | `git merge NAME` |
| Finish a conflict | edit, `git add FILE`, `git commit` |
| Publish a repo | `gh repo create NAME --public --source=. --push` |
| Download only / download and merge | `git fetch` / `git pull` |
| Upload | `git push` |
| Tag a release | `git tag -a v1.0.0 -m "msg"` |

## If something goes wrong

| Problem | What to do |
|---|---|
| `fatal: not a git repository` | Wrong folder. Run `cd ~/netops-practice`. |
| `Author identity unknown` | Run the two `git config --global` lines in Step 1. |
| Terminal shows `>` and waits | Press `Ctrl+C` and retype the command. |
| A strange editor opens (vim) | Press `Esc`, type `:q!`, Enter. Run `export GIT_EDITOR=true`. |
| `Updates were rejected` on push | Run `git pull`, then `git push`. |
| `CONFLICT` | Follow Step 7. |
| Everything is a mess | `cd ~`, `rm -rf ~/netops-practice`, start again at Step 2. |
