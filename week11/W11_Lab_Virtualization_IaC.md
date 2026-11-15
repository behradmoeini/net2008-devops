# Week 11 Lab: Bytown Infrastructure as Code

This lab is graded (2% of final grade). You describe a virtual machine with Vagrant and build real infrastructure with Terraform: a network and web containers, changed through code, repaired after drift, and destroyed. Everything runs on **your own laptop**.

**Rules**

- Work in a real terminal: **PowerShell** on Windows, or **Terminal** on macOS or Linux. Docker must be running and Terraform installed (see [Setup](W11_Lecture_Virtualization_IaC.md#setup) in the lecture).
- Do the parts in order. Each part builds on the one before.
- Use the **exact** names and file names given here. The self-check and your instructor look for them.
- Every command is one grey box. Some boxes come in two versions, **Windows (PowerShell)** and **macOS / Linux (Terminal)**. Open the one for your system. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Search the error message. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

Your numbers come from your student ID. **Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`. Replace `17` with **your** seed:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
$SEED = 17  # Remember your seed in a variable. Replace 17 with your own number.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

</details>

```bash
echo "My seed is $SEED"  # Print the seed to check it.
```

```bash
terraform version  # Terraform must answer. If not, see [Setup](W11_Lecture_Virtualization_IaC.md#setup) in the lecture.
```

```bash
docker run --rm hello-world  # Check that Docker works.
```

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\bytown-iac\vagrant", "$HOME\bytown-iac\terraform", "$HOME\bytown-iac\evidence" | Out-Null; cd "$HOME\bytown-iac"; git init -b main  # Create the lab repository with a folder for each tool and a folder for proof.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
mkdir -p ~/bytown-iac/vagrant ~/bytown-iac/terraform ~/bytown-iac/evidence && cd ~/bytown-iac && git init -b main  # Create the lab repository with a folder for each tool and a folder for proof.
```

</details>

Create `.gitignore` **before** you create any Terraform state, so state is never committed:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
Set-Content -Encoding ascii .gitignore -Value '.terraform/', '*.tfstate', '*.tfstate.*', '.vagrant/'  # Never commit downloaded plug-ins, state files or Vagrant's hidden folder.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
printf '.terraform/\n*.tfstate\n*.tfstate.*\n.vagrant/\n' > .gitignore  # Never commit downloaded plug-ins, state files or Vagrant's hidden folder.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
git add .gitignore; git commit -m "Add .gitignore"  # Commit number 1.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
git add .gitignore && git commit -m "Add .gitignore"  # Commit number 1.
```

</details>

**If you close the terminal**, the variable is lost. Open a new terminal, set the seed again (`$SEED = ...` in PowerShell, `export SEED=...` on macOS or Linux), and go back to the lab folder (`cd $HOME\bytown-iac` in PowerShell, `cd ~/bytown-iac` on macOS or Linux).

---
## Part 1. A virtual machine as code (3 points)

Your VM has a host name and an address that use your seed. The address is `192.168.56.(10 + seed)`.

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@"
Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.box_version = "202510.26.0"
  config.vm.hostname = "bytown-vm-$SEED"
  config.vm.network "private_network", ip: "192.168.56.$(10 + $SEED)"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  config.vm.provision "shell", inline: "echo seed=$SEED > /etc/bytown-seed"
end
"@ | Set-Content -Encoding ascii vagrant\Vagrantfile
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > vagrant/Vagrantfile <<EOF
Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.box_version = "202510.26.0"
  config.vm.hostname = "bytown-vm-$SEED"
  config.vm.network "private_network", ip: "192.168.56.$((10 + SEED))"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  config.vm.provision "shell", inline: "echo seed=$SEED > /etc/bytown-seed"
end
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
Get-Content vagrant\Vagrantfile  # Check that your seed appears in the host name, the address and the provisioning line.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat vagrant/Vagrantfile  # Check that your seed appears in the host name, the address and the provisioning line.
```

</details>

**If Vagrant is installed** (see the lecture), validate the file. The result is saved in the `evidence` folder. You must see "Vagrantfile validated successfully."

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd vagrant; vagrant validate | Out-File -Encoding ascii ..\evidence\part1-validate.txt; Get-Content ..\evidence\part1-validate.txt; cd ..  # Check the Vagrantfile and save the result.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd vagrant && vagrant validate | tee ../evidence/part1-validate.txt; cd ..  # Check the Vagrantfile and save the result. You must see "Vagrantfile validated successfully."
```

</details>

Starting the VM (`vagrant up`) is **optional** and not graded. It works with VirtualBox on Windows, Mac (Intel and Apple silicon) and Linux. It may not work on a Windows laptop with an ARM chip. If you do it, run `vagrant destroy -f` afterwards.

**If you did not install Vagrant**, skip the validate command. Your Vagrantfile is checked by reading it, and you lose no marks.

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
git add vagrant; git commit -m "Add Vagrantfile for the Bytown VM"  # Commit number 2.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
git add vagrant && git commit -m "Add Vagrantfile for the Bytown VM"  # Commit number 2.
```

</details>

---
## Part 2. Terraform: network and web containers (5 points)

Create three files in the `terraform` folder. First the **variables**:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
variable "seed" {
  description = "Sum of the last four digits of your student ID"
  type        = number
}

variable "instances" {
  description = "Number of web containers"
  type        = number
  default     = 2
}

variable "base_port" {
  description = "Host ports start here, plus your seed"
  type        = number
  default     = 8500
}
'@ | Set-Content -Encoding ascii terraform\variables.tf
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > terraform/variables.tf <<'EOF'
variable "seed" {
  description = "Sum of the last four digits of your student ID"
  type        = number
}

variable "instances" {
  description = "Number of web containers"
  type        = number
  default     = 2
}

variable "base_port" {
  description = "Host ports start here, plus your seed"
  type        = number
  default     = 8500
}
EOF
```

</details>

Then the **main** file. It creates a network, an image and `instances` containers:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "lab" {
  name = "bytown-net-${var.seed}"
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  count = var.instances
  name  = "bytown-tf-${var.seed}-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.base_port + var.seed + count.index
  }

  networks_advanced {
    name = docker_network.lab.name
  }

  upload {
    file    = "/usr/share/nginx/html/index.html"
    content = "<h1>Bytown NetOps</h1><p>Seed: ${var.seed}, instance: ${count.index}</p>\n"
  }
}
'@ | Set-Content -Encoding ascii terraform\main.tf
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > terraform/main.tf <<'EOF'
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "lab" {
  name = "bytown-net-${var.seed}"
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  count = var.instances
  name  = "bytown-tf-${var.seed}-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.base_port + var.seed + count.index
  }

  networks_advanced {
    name = docker_network.lab.name
  }

  upload {
    file    = "/usr/share/nginx/html/index.html"
    content = "<h1>Bytown NetOps</h1><p>Seed: ${var.seed}, instance: ${count.index}</p>\n"
  }
}
EOF
```

</details>

Then the **outputs** and **your values**:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
output "urls" {
  description = "Addresses of the web containers"
  value       = [for c in docker_container.web : "http://localhost:${c.ports[0].external}"]
}
'@ | Set-Content -Encoding ascii terraform\outputs.tf
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > terraform/outputs.tf <<'EOF'
output "urls" {
  description = "Addresses of the web containers"
  value       = [for c in docker_container.web : "http://localhost:${c.ports[0].external}"]
}
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
Set-Content -Encoding ascii terraform\terraform.tfvars -Value "seed      = $SEED", "instances = 2"  # Write your seed and the number of containers. Terraform reads this file by itself.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
printf 'seed      = %s\ninstances = 2\n' "$SEED" > terraform/terraform.tfvars  # Write your seed and the number of containers. Terraform reads this file by itself.
```

</details>

```bash
cd terraform  # Move into the Terraform folder. Every Terraform command from here on runs in this folder.
```

```bash
terraform init  # Download the Docker provider.
```

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
terraform fmt -check; terraform validate  # The formatting must be correct (no output) and the code valid. If fmt -check lists a file, run terraform fmt.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
terraform fmt -check && terraform validate  # The formatting must be correct (no output) and the code valid. If fmt -check lists a file, run terraform fmt.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
terraform plan -no-color | Select-Object -Last 3  # Read the end of the plan. You must see: Plan: 4 to add, 0 to change, 0 to destroy.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
terraform plan -no-color | tail -3  # Read the end of the plan. You must see: Plan: 4 to add, 0 to change, 0 to destroy.
```

</details>

```bash
terraform apply -auto-approve  # Create the network, the image and two containers.
```

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
terraform output | Out-File -Encoding ascii ..\evidence\part2-output.txt; Get-Content ..\evidence\part2-output.txt  # Print and save the two addresses. Your ports are 8500 + seed and 8501 + seed.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
terraform output | tee ../evidence/part2-output.txt  # Print and save the two addresses. Your ports are 8500 + seed and 8501 + seed.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s "http://localhost:$(8500 + $SEED)" | Out-File -Encoding ascii ..\evidence\part2-curl0.txt; Get-Content ..\evidence\part2-curl0.txt  # Container 0 answers with your seed and instance 0.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$((8500 + SEED)) | tee ../evidence/part2-curl0.txt  # Container 0 answers with your seed and instance 0.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s "http://localhost:$(8501 + $SEED)" | Out-File -Encoding ascii ..\evidence\part2-curl1.txt; Get-Content ..\evidence\part2-curl1.txt  # Container 1 answers with your seed and instance 1.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$((8501 + SEED)) | tee ../evidence/part2-curl1.txt  # Container 1 answers with your seed and instance 1.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd ..; git add -A; git commit -m "Add Terraform for network and web containers"  # Commit number 3. Check git status: no .tfstate file may be listed.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd .. && git add -A && git commit -m "Add Terraform for network and web containers"  # Commit number 3. Check git status: no .tfstate file may be listed.
```

</details>

---
## Part 3. Change and drift (3 points)

**3a. Drift.** Delete one container behind Terraform's back, and watch Terraform notice:

```bash
docker rm -f "bytown-tf-$SEED-1"  # Delete container 1 by hand.
```

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd terraform; terraform plan -no-color | Out-File -Encoding ascii ..\evidence\part3-plan.txt; Select-String "Plan:" ..\evidence\part3-plan.txt  # Save the plan. You must see: Plan: 1 to add, 0 to change, 0 to destroy.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd terraform && terraform plan -no-color > ../evidence/part3-plan.txt; grep "Plan:" ../evidence/part3-plan.txt  # Save the plan. You must see: Plan: 1 to add, 0 to change, 0 to destroy.
```

</details>

```bash
terraform apply -auto-approve  # Repair the difference. The container comes back.
```

**3b. Change by code.** Raise the number of containers to 3 by editing the **values file**, not the code:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
Set-Content -Encoding ascii terraform.tfvars -Value "seed      = $SEED", "instances = 3"  # Ask for three containers.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
printf 'seed      = %s\ninstances = 3\n' "$SEED" > terraform.tfvars  # Ask for three containers.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
terraform plan -no-color | Select-String "Plan:"  # Read the plan. Terraform adds exactly one container.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
terraform plan -no-color | grep "Plan:"  # Read the plan. Terraform adds exactly one container.
```

</details>

```bash
terraform apply -auto-approve  # Create it.
```

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
terraform state list | Out-File -Encoding ascii ..\evidence\part3-state.txt; Get-Content ..\evidence\part3-state.txt  # Save the list of managed resources. Three containers must be there.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
terraform state list | tee ../evidence/part3-state.txt  # Save the list of managed resources. Three containers must be there.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s "http://localhost:$(8502 + $SEED)" | Out-File -Encoding ascii ..\evidence\part3-curl2.txt; Get-Content ..\evidence\part3-curl2.txt  # The third container answers.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$((8502 + SEED)) | tee ../evidence/part3-curl2.txt  # The third container answers.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd ..; git add -A; git commit -m "Scale to three web containers"  # Commit number 4.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd .. && git add -A && git commit -m "Scale to three web containers"  # Commit number 4.
```

</details>

---
## Part 4. Lock file, state and destroy (3 points)

```bash
git ls-files terraform  # The files Git tracks. You must see .terraform.lock.hcl and the .tf files, and no state file.
```

If `.terraform.lock.hcl` is **not** listed, add and commit it:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
git add terraform/.terraform.lock.hcl; git commit -m "Pin the provider version"  # Commit the lock file if it is not tracked yet.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
git add terraform/.terraform.lock.hcl && git commit -m "Pin the provider version" || true  # Commit the lock file if it is not tracked yet.
```

</details>

Destroy everything:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd terraform; terraform destroy -auto-approve  # Delete the containers, the image reference and the network.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd terraform && terraform destroy -auto-approve  # Delete the containers, the image reference and the network.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
docker ps -a --filter "name=bytown-tf-$SEED" | Out-File -Encoding ascii ..\evidence\part4-after-destroy.txt; Get-Content ..\evidence\part4-after-destroy.txt  # Save the proof: only the header line remains.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
docker ps -a --filter name=bytown-tf-$SEED | tee ../evidence/part4-after-destroy.txt  # Save the proof: only the header line remains.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
cd ..; git add -A; git commit -m "Record the destroyed state"  # Commit number 5.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cd .. && git add -A && git commit -m "Record the destroyed state"  # Commit number 5.
```

</details>

---
## Practice questions (not graded)

Use these to check yourself before the graded answers. Do not hand them in.

Answer these in your head or on paper. Open the answers only after you tried.

1. You need a Windows system for one hour, and you only have a Mac. Would you use a VM or a container? Why?
2. What does Vagrant give you that clicking in VirtualBox does not?
3. A colleague logs in to a server and edits a config file by hand. Which two IaC problems does that cause?
4. What is the difference between `plan` and `apply`?
5. Your plan shows `-/+` on a database. What do you do?
6. A teammate says "the cloud is just someone else's computer, so security is their job". Which idea says this is wrong?

<details>
<summary>Show the answers (try the questions first)</summary>

(1) A VM: a container shares the host's kernel, so it cannot run a different operating system. (2) The VM is described in a file: it is repeatable, shareable through Git, and can be deleted and rebuilt with one command. (3) Drift (the real server no longer matches the code) and a snowflake that nobody can rebuild. (4) `plan` only shows a preview; `apply` really makes the changes. (5) Stop and read why it is replaced; it means the data is destroyed. Change the code so the resource is updated in place, or back up first. (6) The shared responsibility model: the provider secures the data centre, you secure what you put in it.

</details>

---
## Part 5. Answers (3 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. In Part 3a you deleted a container by hand. What did Terraform do, and why must you change infrastructure through the code?
2. Why is `terraform.tfstate` not committed to Git?
3. What is the difference between what Terraform does and what Ansible (Week 12) will do?
4. In the shared responsibility model, name one thing the cloud provider secures and one thing you secure on a cloud VM.

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
Q4: replace this with your answer
'@ | Set-Content -Encoding ascii answers.txt
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > answers.txt <<'EOF'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
Q4: replace this with your answer
EOF
```

</details>

Open `answers.txt` in an editor and replace each placeholder.

---
## Check your work

The self-check reads your repository and your proof files. It runs `terraform fmt -check` and `validate` on your code. It changes nothing. Run it from your lab folder, **after** Part 5:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
python "$HOME\net2008-devops\week11\W11_Lab_selfcheck.py" --seed $SEED  # Check your work against the lab.
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
python3 ~/net2008-devops/week11/W11_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

</details>

Fix every `FAIL` line, then run it again.

## Submit

1. Commit everything and push to a **public** GitHub repository named `bytown-iac` (the same steps as Week 6, Part 4). Create the empty repository on GitHub first, then:

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
git add -A; git commit -m "Week 11 lab: infrastructure as code"; git remote add origin git@github.com:YOUR-USERNAME/bytown-iac.git  # Save and link your empty GitHub repository. Use your own user name. (If git says nothing to commit, that is fine.)
```

</details>

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
git add -A && git commit -m "Week 11 lab: infrastructure as code" ; git remote add origin git@github.com:YOUR-USERNAME/bytown-iac.git  # Save and link your empty GitHub repository. Use your own user name. (If git says nothing to commit, that is fine.)
```

</details>

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 11 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline.

## Marking (17 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | `vagrant/Vagrantfile` with your host name, address and provisioning line | 3 |
| 2 | Terraform code formatted and valid, network and two containers created, both pages show your seed | 5 |
| 3 | Drift shown in a plan and repaired, scaled to three by the values file | 3 |
| 4 | State never committed, lock file committed, everything destroyed | 3 |
| 5 | `answers.txt` (read by your instructor) | 3 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `Error: No value for required variable` | `terraform/terraform.tfvars` is missing or has no `seed`. Recreate it. |
| `port is already allocated` | Another program uses that port. Find it with `docker ps`. Remove old containers: `docker rm -f NAME`. |
| `Error: Conflict. The container name ... is already in use` | An old container exists with that name. `docker rm -f NAME`, then apply again. |
| `terraform fmt -check` lists a file | Run `terraform fmt` and commit the change. |
| `git status` shows `terraform.tfstate` | `.gitignore` is wrong or was created too late. Run `git rm --cached terraform/terraform.tfstate*` and fix `.gitignore`. |
| `vagrant validate` says the box or provider is wrong | Check the line you copied. If Vagrant cannot run on your laptop, skip it (see Part 1). |
| `Cannot connect to the Docker daemon` | Start Docker Desktop. |
| Everything is a mess | In `terraform`: `terraform destroy -auto-approve`, then `docker rm -f $(docker ps -aq --filter name=bytown-tf)`, and restart at Part 2. |
