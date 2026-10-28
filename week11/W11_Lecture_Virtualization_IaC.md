# Week 11 Lecture: Virtualization and Infrastructure as Code
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Docker running and **Terraform** installed (see [W09_Setup_Your_Laptop.md](../week09/lab/W09_Setup_Your_Laptop.md), section 3). **Vagrant and VirtualBox are optional**: the Terraform part of this week runs with Docker only, so every student can finish it.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- Do the steps in order. All practice work happens in one folder, `~/iac-practice`.

---
## The big picture: read this first

### Part A. Virtual machines

A **virtual machine** (VM) is a complete computer made of software. A program called a **hypervisor** shares the real hardware among several VMs. Each VM has its own operating system, its own virtual disk and its own virtual network card.

| Hypervisor type | Runs on | Examples |
|---|---|---|
| **Type 1** ("bare metal") | Directly on the hardware, in data centres | VMware ESXi, Microsoft Hyper-V, KVM |
| **Type 2** ("hosted") | As a program inside your normal operating system | VirtualBox, VMware Workstation, Parallels |

Your laptop uses a type 2 hypervisor. Cloud providers use type 1 hypervisors to rent you VMs.

A VM network card can be attached in three common ways:

| Mode | What the VM can reach |
|---|---|
| **NAT** | The internet through your laptop. Nothing from outside can reach the VM. |
| **Host-only (private network)** | Your laptop and the other VMs on that network only |
| **Bridged** | The real network, as if it were a separate computer |

### The problem with VMs by hand

You click through an installer, install packages, change settings. Three weeks later nobody can say exactly what is on the VM, and nobody can build the same one again. Hand-built servers are called **snowflakes**: every one is unique and fragile.

### Part B. Infrastructure as Code (IaC)

**Infrastructure as Code** means you describe servers, networks and containers in **text files**, keep them in Git, and let a tool create them. You get what you get for source code: history, review, rollback, and the same result every time.

| Tool | What it describes | This week |
|---|---|---|
| **Vagrant** | One or more **VMs** on your own computer (for development) | Read a `Vagrantfile`. Run it if your laptop can. |
| **Terraform** | **Any infrastructure** through "providers": cloud VMs, networks, DNS, Docker | You build real infrastructure (Docker containers) |
| **Ansible** | What is **inside** a server: packages, files, services | Week 12 |

Provisioning (Terraform: "make these things exist") and configuration (Ansible: "set them up") are separate jobs.

### Terraform in one picture

You write the **desired state** in `.tf` files (HCL, a simple language). Terraform compares it with the **state** it remembers and with the real world, and makes the changes needed.

```text
.tf files (what you want) --terraform plan--> list of changes --terraform apply--> real infrastructure
                                                                                          |
terraform.tfstate (what Terraform believes exists) <------------ updated after every apply
```

| Word | Meaning |
|---|---|
| **Provider** | A plug-in that talks to one platform (AWS, Azure, Docker). You declare which. |
| **Resource** | One thing to create: a container, a network, a VM |
| **Variable** | An input. Lets one code base serve many environments. |
| **Output** | A value Terraform prints when it finishes |
| **State** | Terraform's record of what it created. **Never edit it by hand.** |
| **Plan** | The list of changes Terraform would make. Always read it. |

---
## Step 1. Vagrant: a VM as code (read, and run if you can)

A `Vagrantfile` is a small Ruby file. Read this one. It describes one Ubuntu VM:

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "demo-vm"
  config.vm.network "private_network", ip: "192.168.56.20"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  config.vm.provision "shell", inline: "echo hello > /etc/demo-greeting"
end
```

| Line | Meaning |
|---|---|
| `config.vm.box` | The base image (a "box") to start from |
| `config.vm.hostname` | The VM's host name |
| `config.vm.network "private_network"` | A host-only network with this address |
| `vb.memory`, `vb.cpus` | The size of the VM |
| `config.vm.provision "shell"` | A command that runs **once** inside the VM when it is created |

**If you installed Vagrant and VirtualBox** (Intel or AMD laptop), try it:

```bash
mkdir -p ~/iac-practice/vm && cd ~/iac-practice/vm  # Create a folder for the VM and move into it.
```

```bash
vagrant init ubuntu/jammy64  # Create a Vagrantfile for that box. Open it and compare with the one above.
```

```bash
vagrant validate  # Check that the Vagrantfile is correct. It does not start anything.
```

```bash
vagrant up  # Download the box, create the VM and start it. The first time takes several minutes.
```

```bash
vagrant ssh -c "hostname && cat /etc/os-release | head -2"  # Run a command inside the VM.
```

```bash
vagrant destroy -f  # Delete the VM. The Vagrantfile stays: you can rebuild it any time.
```

| Command | What it does |
|---|---|
| `vagrant up` | Create and start the VM |
| `vagrant ssh` | Open a shell in the VM |
| `vagrant halt` | Shut it down (keeps the disk) |
| `vagrant destroy` | Delete it |
| `vagrant status` | Show the state |

**If you cannot run Vagrant** (Apple silicon, or VirtualBox conflicts with Docker on your Windows laptop): do not worry. You still write a Vagrantfile in the lab and your work is checked by reading it. You do not lose marks.

---
## Step 2. Terraform: your first infrastructure

You build a web container and a network with Terraform and the Docker provider. Create a folder:

```bash
mkdir -p ~/iac-practice/tf && cd ~/iac-practice/tf  # Create the Terraform folder and move into it.
```

```bash
cat > main.tf <<'EOF'
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "tf-web"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 8095
  }
}
EOF
```

Read it:

- `terraform { ... }` says which provider to download and which versions are acceptable (`~> 3.0` means 3.x).
- `resource "docker_image" "nginx"` declares an image. The two words after `resource` are the **type** and your **name** for it.
- `docker_container.web` uses `docker_image.nginx.image_id`. That reference tells Terraform to create the image **first**. You never write the order yourself: Terraform builds it from the references.

Now the workflow. It has four commands:

```bash
terraform init  # Download the Docker provider into a hidden .terraform folder. Run it once per project, and again after you add a provider.
```

```bash
terraform fmt  # Reformat the .tf files to the standard style. It prints the names of the files it changed.
```

```bash
terraform validate  # Check the syntax and the references. You should see "Success! The configuration is valid."
```

```bash
terraform plan  # Show what Terraform WOULD do. Read it: "+" create, "-" destroy, "~" change. Nothing is created yet.
```

**You should see** `Plan: 2 to add, 0 to change, 0 to destroy.`

```bash
terraform apply  # Show the plan again and ask for confirmation. Type yes to create the resources.
```

```bash
curl -s http://localhost:8095 | head -4  # The container Terraform created answers on port 8095.
```

```bash
docker ps --filter name=tf-web  # Docker shows the container too. Terraform is only a program that called Docker for you.
```

```bash
terraform apply  # Run apply again. It says "No changes". Applying twice is safe: this is called being idempotent.
```

---
## Step 3. State

```bash
terraform state list  # List everything Terraform believes it manages.
```

```bash
terraform show | head -30  # Show the stored details of those resources.
```

```bash
ls -la  # Look at the folder: terraform.tfstate is the state file, .terraform.lock.hcl pins the provider version.
```

| File or folder | Commit to Git? | Why |
|---|---|---|
| `*.tf` | **Yes** | Your code |
| `.terraform.lock.hcl` | **Yes** | Makes everyone use the same provider version |
| `terraform.tfstate`, `terraform.tfstate.backup` | **No** | State can contain secrets and belongs to one real environment. Teams keep it in a shared remote store. |
| `.terraform/` | **No** | Downloaded plug-ins. `terraform init` recreates it. |

---
## Step 4. Variables, outputs and `count`

Replace the file with a version that has inputs and outputs. Create three files:

```bash
cat > variables.tf <<'EOF'
variable "instances" {
  description = "Number of web containers"
  type        = number
  default     = 2
}

variable "base_port" {
  description = "Host port of the first container"
  type        = number
  default     = 8095
}
EOF
```

```bash
cat > main.tf <<'EOF'
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  count = var.instances
  name  = "tf-web-${count.index}"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.base_port + count.index
  }

  upload {
    file    = "/usr/share/nginx/html/index.html"
    content = "<h1>Container ${count.index}</h1>\n"
  }
}
EOF
```

```bash
cat > outputs.tf <<'EOF'
output "urls" {
  description = "Addresses of the web containers"
  value       = [for c in docker_container.web : "http://localhost:${c.ports[0].external}"]
}
EOF
```

What is new:

| Syntax | Meaning |
|---|---|
| `var.instances` | The value of the variable `instances` |
| `count = var.instances` | Create that many copies of the resource |
| `count.index` | 0 for the first copy, 1 for the second, and so on |
| `"text ${expression}"` | Put the value of an expression inside a string |
| `upload { ... }` | Put a file into the container when it is created |
| `output` | A value printed at the end of `apply` |

```bash
terraform plan  # Read the plan. The old tf-web is destroyed (its name changed) and two new containers are created.
```

```bash
terraform apply -auto-approve  # Apply without asking (-auto-approve). Only use this when you already read the plan.
```

```bash
terraform output  # Print the outputs: the two addresses.
```

```bash
curl -s http://localhost:8095 && curl -s http://localhost:8096  # Each container serves its own page.
```

Change a variable **without editing the code**:

```bash
terraform apply -auto-approve -var="instances=3"  # Ask for 3 containers. Terraform adds exactly one.
```

```bash
terraform apply -auto-approve  # Back to the default of 2. Terraform removes exactly one.
```

You can also put values in a file named `terraform.tfvars` (a line like `instances = 3`), which Terraform reads by itself.

---
## Step 5. Drift: when the real world changes

Someone deletes a container by hand. Terraform notices.

```bash
docker rm -f tf-web-1  # Delete a container behind Terraform's back.
```

```bash
terraform plan  # Terraform compares the state with the real world and plans to create tf-web-1 again.
```

```bash
terraform apply -auto-approve  # Repair the difference.
```

This is why you change infrastructure **only through the code**. A hand change is called **drift**, and the next `apply` undoes it.

---
## Step 6. Destroy

```bash
terraform destroy  # Show what would be deleted and ask. Type yes. Everything Terraform created is removed, in the right order.
```

```bash
docker ps -a --filter name=tf-web  # Nothing is left.
```

The `.tf` files are all you need to build it again. That is the point of IaC.

## Cheat sheet

| Command | What it does |
|---|---|
| `terraform init` | Download providers (first, and after adding one) |
| `terraform fmt` | Format the code |
| `terraform validate` | Check the code |
| `terraform plan` | Preview changes |
| `terraform apply` | Make the changes (asks first) |
| `terraform destroy` | Delete everything it manages |
| `terraform output` | Show the outputs |
| `terraform state list` | List managed resources |

## If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running. Start Docker Desktop. |
| `Error: Failed to query available provider packages` | No internet during `init`, or a typo in `source`. Check `kreuzwerker/docker`. |
| `port is already allocated` | Something uses the host port. `docker ps`, remove the old container, or change `base_port`. |
| `Error: Reference to undeclared input variable` | A variable is used but not declared in a `variable` block. |
| `Error: Unsupported argument` | A typo in an attribute name, or the wrong block type. Read the line and column in the message. |
| `Error: container exited immediately` | The image or command is wrong. `docker logs NAME`. |
| `Error acquiring the state lock` | A previous run was killed. Wait a minute, or `terraform force-unlock ID` (the ID is in the message). |
| `terraform: command not found` | Terraform is not installed in this terminal. See the setup guide, section 4. |
| macOS: `unix:///var/run/docker.sock` not found | Docker Desktop > Settings > Advanced: enable **Allow the default Docker socket to be used**, or set `provider "docker" { host = "unix:///Users/YOU/.docker/run/docker.sock" }`. |
| Windows: Docker works in Ubuntu but Terraform does not | Run Terraform in the **Ubuntu** terminal, with Docker Desktop's WSL integration on. |

## Summary

- A VM is a whole computer in software, run by a hypervisor. Vagrant describes VMs as code for development.
- Infrastructure as Code keeps infrastructure in text files in Git, so it is reviewable and repeatable.
- Terraform workflow: `init`, `plan`, `apply`, `destroy`. Always read the plan. State is Terraform's memory: never edit it, never commit it.
- Variables make code reusable. `count` makes copies. A hand change causes drift, and `apply` repairs it.

**Next:** the Week 11 lab (graded) builds a Vagrantfile and a Terraform project with your own seed.
