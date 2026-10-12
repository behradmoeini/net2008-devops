# Week 6 Lab: Bytown NetOps Change Repository
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). It is the hands-on companion to the Week 6 lecture. You build one Git repository for a small router configuration, from the first commit to a merged pull request, then clone it back from GitHub.

**Rules**

- Work in a real terminal: your Codespace from the lecture, or any terminal with Git and Python 3 installed (macOS Terminal, Linux, or Git Bash on Windows).
- Do the parts in order. Each part builds on the one before.
- Use the **exact** file names, branch names and commit messages given here. The self-check and your instructor look for them.
- Every command is one grey box. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Search the error message. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

Your numbers come from your student ID, so your repository is different from everyone else's. **Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`.

Replace `17` with **your** seed (a number from 1 to 36), then run:

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

```bash
echo "My seed is $SEED"  # Print the seed to check it.
```

```bash
export GIT_PAGER=cat GIT_EDITOR=true  # Stop Git from opening a viewer or an editor.
```

```bash
git config --global user.name  # Show the name Git will put on your commits (set it, as in the lecture, if empty).
```

```bash
git config --global user.email  # Show the email Git will put on your commits (set it if empty).
```

**If you close the terminal**, the variables are lost. Open a new terminal and run the two `export` lines again (the seed and `GIT_PAGER`/`GIT_EDITOR`).

---
## Part 1. First commits and `.gitignore` (4 points)

Create the repository. You create `.gitignore` **first**, before the files it must protect.

```bash
mkdir -p ~/bytown-netops  # Create the lab folder.
```

```bash
cd ~/bytown-netops  # Move into the lab folder.
```

```bash
git init -b main  # Turn the folder into a repository with a branch named main.
```

```bash
printf '*.log\nsecrets.env\n' > .gitignore  # Create .gitignore: skip every .log file and secrets.env.
```

```bash
git add .gitignore  # Stage .gitignore.
```

```bash
git commit -m "Add .gitignore"  # Commit number 1.
```

Create the router configuration. The file uses **your** seed:

```bash
printf 'hostname core-rtr-%s\ninterface Loopback0\n ip address 10.%s.0.1 255.255.255.255\n' "$SEED" "$SEED" > core-rtr.cfg  # Create core-rtr.cfg with your hostname and loopback address.
```

```bash
cat core-rtr.cfg  # Print the file and check that your seed is in it.
```

```bash
git add core-rtr.cfg  # Stage core-rtr.cfg.
```

```bash
git commit -m "Add core router config"  # Commit number 2.
```

```bash
echo "snmp-server community netops-ro RO" >> core-rtr.cfg  # Append the SNMP line to core-rtr.cfg.
```

```bash
git diff  # Show the change: the SNMP line starts with a plus sign.
```

```bash
git add core-rtr.cfg  # Stage the change.
```

```bash
git commit -m "Enable SNMP read-only"  # Commit number 3.
```

Now create two files that must **never** be committed:

```bash
echo "noisy log line" > router.log  # Create a log file.
```

```bash
echo "ADMIN_PASSWORD=do-not-commit" > secrets.env  # Create a fake secrets file.
```

```bash
git status  # Both files must be invisible, and the tree must be clean.
```

**You should see** `nothing to commit, working tree clean`. If `router.log` or `secrets.env` appear, your `.gitignore` is wrong. Fix it before you go on.

---
## Part 2. Undo mistakes (3 points)

**2a. Throw away an uncommitted edit.**

```bash
echo "THIS IS A MISTAKE" >> core-rtr.cfg  # Append a bad line.
```

```bash
git restore core-rtr.cfg  # Throw the edit away.
```

```bash
cat core-rtr.cfg  # Check that the bad line is gone.
```

**2b. Undo a commit.** First make a bad commit that shuts down an interface:

```bash
printf 'interface Gi0/1\n shutdown\n' >> core-rtr.cfg  # Append a config that shuts down the uplink.
```

```bash
git add core-rtr.cfg  # Stage it.
```

```bash
git commit -m "Shut down core uplink"  # Commit the mistake.
```

Undo it the safe way, with a new commit that cancels the old one:

```bash
git revert --no-edit HEAD  # Add a new commit that cancels the latest commit.
```

```bash
git log --oneline  # Check the history: the Revert commit sits on top of the bad one.
```

```bash
cat core-rtr.cfg  # Check that the shutdown lines are gone.
```

**2c. Find who changed a line.**

```bash
git blame core-rtr.cfg  # Show the commit that last changed each line.
```

Find the row with `snmp-server community netops-ro RO` and write down the commit ID at the start of that row (without a leading `^`). You need it for Part 6.

---
## Part 3. Branches, merging and a conflict (4 points)

**3a. A branch and a merge.** Add a guest VLAN on a branch. The VLAN number is `100 + your seed`.

```bash
git switch -c add-vlan  # Create the branch add-vlan and switch to it.
```

```bash
printf 'vlan %s\n name guest\n' "$((100 + SEED))" >> core-rtr.cfg  # Append your guest VLAN to core-rtr.cfg (on this branch only).
```

```bash
git add core-rtr.cfg  # Stage it.
```

```bash
git commit -m "Add guest VLAN"  # Commit it on add-vlan.
```

While the branch waits, `main` moves on. Switch back and add an NTP file:

```bash
git switch main  # Switch back to main.
```

```bash
echo "ntp server 10.0.0.10" > ntp.cfg  # Create ntp.cfg with one line.
```

```bash
git add ntp.cfg  # Stage it.
```

```bash
git commit -m "Add NTP config"  # Commit it on main.
```

```bash
git merge add-vlan  # Merge add-vlan into main. Both branches have new commits, so Git makes a merge commit.
```

```bash
git log --oneline --graph --all  # Show the graph: two lines join in the merge commit.
```

Delete the branch (**local** only, it was never on GitHub):

```bash
git branch -d add-vlan  # Delete the local branch add-vlan. Its work is merged.
```

**3b. A conflict.** Two branches change the same line of `ntp.cfg`.

```bash
git switch -c ntp-primary  # Create the branch ntp-primary and switch to it.
```

```bash
echo "ntp server 10.0.0.11" > ntp.cfg  # Replace the line with the primary server (this branch).
```

```bash
git commit -a -m "Use primary NTP server"  # Stage and commit the change to the tracked file.
```

```bash
git switch main  # Switch back to main.
```

```bash
echo "ntp server 10.0.0.12" > ntp.cfg  # Replace the same line with the backup server (on main).
```

```bash
git commit -a -m "Use backup NTP server"  # Stage and commit the change to the tracked file.
```

```bash
git merge ntp-primary  # Merge. Both changed the same line, so Git reports a CONFLICT.
```

```bash
cat ntp.cfg  # Print the file and read the conflict markers.
```

Resolve it. Your final `ntp.cfg` must have exactly these two lines and no marker lines:

```text
ntp server 10.0.0.11 prefer
ntp server 10.0.0.12
```

```bash
printf 'ntp server 10.0.0.11 prefer\nntp server 10.0.0.12\n' > ntp.cfg  # Write the final text and remove the markers.
```

```bash
git add ntp.cfg  # Mark the conflict as resolved.
```

```bash
git commit -m "Merge ntp-primary, keep both NTP servers"  # Finish the merge.
```

```bash
git branch -d ntp-primary  # Delete the local branch ntp-primary.
```

```bash
git branch  # List local branches. Only main must be left.
```

---
## Part 4. GitHub: push and pull (3 points)

**4a. Create an empty repository on GitHub.** Open <https://github.com/new>. **Repository name:** `bytown-netops`. Select **Public**. Leave README, `.gitignore` and license **off**. Click **Create repository**.

**4b. SSH key.** If you made an SSH key in the lecture (Step 8b and 8c) and it still works, skip this. Test it:

```bash
ssh -T git@github.com  # Test the SSH login. It must say "successfully authenticated". If not, redo Step 8b and 8c of the lecture.
```

**4c. Connect and push.** Use **your** GitHub username in the URL:

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-netops.git  # Link the empty GitHub repository to your folder.
```

```bash
git push -u origin main  # Upload main to GitHub and remember it as the upstream.
```

Reload the repository page. Your files and commits are there. `router.log` and `secrets.env` are **not**.

**4d. Pull a teammate's change.** You play the teammate. On GitHub, open `core-rtr.cfg`, click the pencil icon, add the line `logging host 10.0.0.50` at the bottom, and commit with the message `Send syslog to collector`. Then:

```bash
git pull  # Download the new commit from GitHub and merge it into main.
```

```bash
cat core-rtr.cfg  # Check that the logging line is in your file.
```

---
## Part 5. A pull request (3 points)

```bash
git switch -c add-banner  # Create the branch add-banner and switch to it.
```

```bash
echo "banner motd Authorized access only" >> core-rtr.cfg  # Append a login banner line.
```

```bash
git add core-rtr.cfg  # Stage it.
```

```bash
git commit -m "Add login banner"  # Commit it.
```

```bash
git push -u origin add-banner  # Upload the branch add-banner to GitHub.
```

On GitHub: click **Compare & pull request**. Check **base: main** and **compare: add-banner**. **Title:** `Add login banner`. In the **Description** write `Seed: ` and your seed. Click **Create pull request**. Open **Files changed** and check that it shows only your one line. Go back to **Conversation**, click **Merge pull request**, then **Confirm merge**. **Do not click "Delete branch".** You delete it yourself with a command, so you learn the command.

```bash
git switch main  # Switch back to main.
```

```bash
git pull  # Bring main up to date with GitHub, including the merged pull request.
```

```bash
git branch -d add-banner  # Delete the LOCAL branch add-banner.
```

```bash
git push origin --delete add-banner  # Delete the branch add-banner on GitHub (the REMOTE one).
```

```bash
git branch -a  # List local and remote branches. add-banner must be gone from both.
```

---
## Part 6. Clone it back and answer five questions (3 points)

**6a. Clone.** Clone your own repository into a different folder and look at it. This proves your work is on GitHub:

```bash
cd ~  # Leave the lab folder.
```

```bash
git clone git@github.com:YOUR-USERNAME/bytown-netops.git bytown-copy  # Download a full copy of your GitHub repository into a folder named bytown-copy.
```

```bash
cd bytown-copy  # Move into the clone.
```

```bash
git log --oneline --graph  # Every commit came with the clone.
```

```bash
cd ~  # Leave the clone.
```

```bash
rm -rf ~/bytown-copy  # Delete the copy. Your lab folder and GitHub are not affected.
```

**6b. Answer five questions.** Go back to your lab folder and create `answers.txt`:

```bash
cd ~/bytown-netops  # Go back into the lab folder.
```

```bash
printf 'Q1: \nQ2: \nQ3: \nQ4: \nQ5: \n' > answers.txt  # Create answers.txt with five empty answers.
```

Open `answers.txt` in an editor (Codespace: `code answers.txt`; or `nano answers.txt`) and write each answer **on the same line** as its `Q` number:

1. The commit ID you wrote down in Part 2c: the commit that last changed the `snmp-server community` line.
2. How many merge commits does your history have? Run `git rev-list --merges --count HEAD` and write the number.
3. You commit on your computer and run `git push`. GitHub rejects it with `! [rejected] main -> main (fetch first)` because a teammate pushed first. Write the **command** you run next, and one sentence on why.
4. You committed `secrets.env` with a real password and pushed it. Today you add `secrets.env` to `.gitignore`. Is the password protected now? Write yes or no and one sentence on why.
5. A pull request for the branch `old-fix` was merged on GitHub. Write the two commands that delete `old-fix`: first the local one, then the one on GitHub.

Save, then commit and push:

```bash
git add answers.txt  # Stage your answers.
```

```bash
git commit -m "Add lab answers"  # Commit them.
```

```bash
git push  # Upload them to GitHub.
```

---
## Check your work

The self-check reads your repository and tells you which parts pass. It changes nothing. Run it from your lab folder. In a Codespace the script is in the course repository:

```bash
python3 /workspaces/net2008-devops/week06/W06_Lab_selfcheck.py --seed "$SEED"  # Check your repository against the lab. (Local computer: use the path of your copy of the course repository. On Windows Git Bash, type `python` if `python3` is not found.)
```

Fix every `FAIL` line, then run it again. It checks that things exist and have the right shape. It does **not** replace reading your own history with `git log --oneline --graph`: your instructor reads your repository and answers on GitHub too.

## Submit

1. Run the self-check and fix every `FAIL`.
2. Open your repository on GitHub in a private (incognito) window. If you can see it, your instructor can. If not, it is not public: fix that.
3. Open **Week 6 Lab Submission** on Brightspace and submit **only the URL** of your repository, for example `https://github.com/your-username/bytown-netops`. Write it in the submission comments or upload a text file `W06_Lab_<your-last-name>.txt` that contains only the URL.
4. Do not push to the repository after the deadline. Your instructor looks at the history.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Three starting commits, `.gitignore` before the files, nothing secret ever committed | 4 |
| 2 | Revert (not delete) of the bad commit, no leftover mistakes | 3 |
| 3 | Guest VLAN merged, conflict resolved, local branches deleted | 4 |
| 4 | Pushed to GitHub, SSH remote, upstream set, GitHub edit pulled | 3 |
| 5 | Pull request merged on GitHub, branch deleted locally and on GitHub | 3 |
| 6 | `answers.txt` correct and pushed (Q3, Q4, Q5 read by your instructor) | 3 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `fatal: not a git repository` | Wrong folder. Run `cd ~/bytown-netops`. |
| `$SEED` prints nothing, or files contain `10..0.1` | The variable is lost. Run the `export SEED=...` line again, then fix the file by hand. |
| A file you must not commit shows up in `git status` | `.gitignore` is wrong, or you committed the file already. Ask yourself why the second case is worse (Question 4). |
| `Updates were rejected` on push | `git pull`, resolve any conflict, then `git push`. |
| `Permission denied (publickey)` | GitHub does not have your public key. Redo Step 8b and 8c of the lecture. |
| `403` on push | You used an `https://` URL. Use `git remote set-url origin git@github.com:YOUR-USERNAME/bytown-netops.git`. |
| `git push origin --delete add-banner` says `remote ref does not exist` | You (or GitHub) already deleted it. Run `git fetch --prune` and check with `git branch -a`. |
| `git branch -d add-banner` says `not fully merged` | You did not `git pull` after merging the pull request. Run `git pull` first. |
| A strange editor opens (vim) | Press `Esc`, type `:q!`, Enter. Run `export GIT_EDITOR=true`. |
| Everything is a mess | You may start over: `cd ~`, `rm -rf ~/bytown-netops`, delete the GitHub repository (Settings, bottom of the page), and begin again at Part 1. |
