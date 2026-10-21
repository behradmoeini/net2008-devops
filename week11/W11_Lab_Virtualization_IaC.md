# Week 11 Lab: Bytown Infrastructure as Code
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). You describe a virtual machine with Vagrant and build real infrastructure with Terraform: a network and web containers, changed through code, repaired after drift, and destroyed. Everything runs on **your own laptop**.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Docker must be running and Terraform installed (see [W09_Setup_Your_Laptop.md](../week09/W09_Setup_Your_Laptop.md)).
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
terraform version  # Terraform must answer. If not, see the setup guide, section 4.
```

```bash
docker run --rm hello-world  # Check that Docker works.
```

```bash
mkdir -p ~/bytown-iac/vagrant ~/bytown-iac/terraform ~/bytown-iac/evidence && cd ~/bytown-iac && git init -b main  # Create the lab repository with a folder for each tool and a folder for proof.
```

Create `.gitignore` **before** you create any Terraform state, so state is never committed:

```bash
printf '.terraform/\n*.tfstate\n*.tfstate.*\n.vagrant/\n' > .gitignore  # Never commit downloaded plug-ins, state files or Vagrant's hidden folder.
```

```bash
git add .gitignore && git commit -m "Add .gitignore"  # Commit number 1.
```

**If you close the terminal**, the variable is lost. Open a new terminal, run `export SEED=...` again and `cd ~/bytown-iac`.

---
## Part 1. A virtual machine as code (3 points)

Your VM has a host name and an address that use your seed. The address is `192.168.56.(10 + seed)`.

```bash
cat > vagrant/Vagrantfile <<EOF
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
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

```bash
cat vagrant/Vagrantfile  # Check that your seed appears in the host name, the address and the provisioning line.
```

**If Vagrant is installed in this terminal** (macOS with Intel, and Linux), validate the file:

```bash
cd vagrant && vagrant validate | tee ../evidence/part1-validate.txt; cd ..  # Check the Vagrantfile and save the result. You must see "Vagrantfile validated successfully."
```

Starting the VM (`vagrant up`) is **optional** and not graded. If you do it, run `vagrant destroy -f` afterwards.

**If you cannot run Vagrant here** (Windows with Ubuntu, Apple silicon, or no VirtualBox), skip the validate command. Your Vagrantfile is checked by reading it, and you lose no marks.

```bash
git add vagrant && git commit -m "Add Vagrantfile for the Bytown VM"  # Commit number 2.
```

---
## Part 2. Terraform: network and web containers (6 points)

Create three files in the `terraform` folder. First the **variables**:

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

Then the **main** file. It creates a network, an image and `instances` containers:

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

Then the **outputs** and **your values**:

```bash
cat > terraform/outputs.tf <<'EOF'
output "urls" {
  description = "Addresses of the web containers"
  value       = [for c in docker_container.web : "http://localhost:${c.ports[0].external}"]
}
EOF
```

```bash
printf 'seed      = %s\ninstances = 2\n' "$SEED" > terraform/terraform.tfvars  # Write your seed and the number of containers. Terraform reads this file by itself.
```

```bash
cd terraform  # Move into the Terraform folder. Every Terraform command from here on runs in this folder.
```

```bash
terraform init  # Download the Docker provider.
```

```bash
terraform fmt -check && terraform validate  # The formatting must be correct (no output) and the code valid. If fmt -check lists a file, run terraform fmt.
```

```bash
terraform plan -no-color | tail -3  # Read the end of the plan. You must see: Plan: 4 to add, 0 to change, 0 to destroy.
```

```bash
terraform apply -auto-approve  # Create the network, the image and two containers.
```

```bash
terraform output | tee ../evidence/part2-output.txt  # Print and save the two addresses. Your ports are 8500 + seed and 8501 + seed.
```

```bash
curl -s http://localhost:$((8500 + SEED)) | tee ../evidence/part2-curl0.txt  # Container 0 answers with your seed and instance 0.
```

```bash
curl -s http://localhost:$((8501 + SEED)) | tee ../evidence/part2-curl1.txt  # Container 1 answers with your seed and instance 1.
```

```bash
cd .. && git add -A && git commit -m "Add Terraform for network and web containers"  # Commit number 3. Check git status: no .tfstate file may be listed.
```

---
## Part 3. Change and drift (4 points)

**3a. Drift.** Delete one container behind Terraform's back, and watch Terraform notice:

```bash
docker rm -f bytown-tf-$SEED-1  # Delete container 1 by hand.
```

```bash
cd terraform && terraform plan -no-color > ../evidence/part3-plan.txt; grep "Plan:" ../evidence/part3-plan.txt  # Save the plan. You must see: Plan: 1 to add, 0 to change, 0 to destroy.
```

```bash
terraform apply -auto-approve  # Repair the difference. The container comes back.
```

**3b. Change by code.** Raise the number of containers to 3 by editing the **values file**, not the code:

```bash
printf 'seed      = %s\ninstances = 3\n' "$SEED" > terraform.tfvars  # Ask for three containers.
```

```bash
terraform plan -no-color | grep "Plan:"  # Read the plan. Terraform adds exactly one container.
```

```bash
terraform apply -auto-approve  # Create it.
```

```bash
terraform state list | tee ../evidence/part3-state.txt  # Save the list of managed resources. Three containers must be there.
```

```bash
curl -s http://localhost:$((8502 + SEED)) | tee ../evidence/part3-curl2.txt  # The third container answers.
```

```bash
cd .. && git add -A && git commit -m "Scale to three web containers"  # Commit number 4.
```

---
## Part 4. Lock file, state and destroy (4 points)

```bash
git ls-files terraform  # The files Git tracks. You must see .terraform.lock.hcl and the .tf files, and no state file.
```

If `.terraform.lock.hcl` is **not** listed, add and commit it:

```bash
git add terraform/.terraform.lock.hcl && git commit -m "Pin the provider version" || true  # Commit the lock file if it is not tracked yet.
```

Destroy everything:

```bash
cd terraform && terraform destroy -auto-approve  # Delete the containers, the image reference and the network.
```

```bash
docker ps -a --filter name=bytown-tf-$SEED | tee ../evidence/part4-after-destroy.txt  # Save the proof: only the header line remains.
```

```bash
cd .. && git add -A && git commit -m "Record the destroyed state"  # Commit number 5.
```

---
## Part 5. Answers (3 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. In Part 3a you deleted a container by hand. What did Terraform do, and why must you change infrastructure through the code?
2. Why is `terraform.tfstate` not committed to Git?
3. What is the difference between what Terraform does and what Ansible (Week 12) will do?

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

The self-check reads your repository and your proof files. It runs `terraform fmt -check` and `validate` on your code. It changes nothing. Run it from your lab folder, **after** Part 4 (the destroy):

```bash
python3 ~/net2008-devops/week11/W11_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again.

## Submit

1. Commit everything and push to a **public** GitHub repository named `bytown-iac` (the same steps as Week 6, Part 4). Create the empty repository on GitHub first, then:

```bash
git add -A && git commit -m "Week 11 lab: infrastructure as code" ; git remote add origin git@github.com:YOUR-USERNAME/bytown-iac.git  # Save and link your empty GitHub repository. Use your own user name. (If git says nothing to commit, that is fine.)
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 11 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | `vagrant/Vagrantfile` with your host name, address and provisioning line | 3 |
| 2 | Terraform code formatted and valid, network and two containers created, both pages show your seed | 6 |
| 3 | Drift shown in a plan and repaired, scaled to three by the values file | 4 |
| 4 | State never committed, lock file committed, everything destroyed | 4 |
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
