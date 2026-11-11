# Week 11 Lecture: Virtualization and Infrastructure as Code
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Docker running and **Terraform** installed (see [W11_Setup_Terraform.md](W11_Setup_Terraform.md)). **Vagrant and VirtualBox are optional**: the Terraform part of this week runs with Docker only, so every student can finish it.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- Do the steps in order. All practice work happens in one folder, `~/iac-practice`.

---
## The big picture

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

### Part A2. The cloud

A **cloud provider** (AWS, Microsoft Azure, Google Cloud) owns huge data centres full of type 1 hypervisors and rents you pieces of them by the second. You do not buy hardware: you ask for a VM, a network or a database through a web page or an **API**, and you pay for what you use.

| Service model | You manage | The provider manages | Example |
|---|---|---|---|
| **IaaS** (Infrastructure as a Service) | The operating system and everything above it | Hardware, network, hypervisor | AWS EC2, Azure Virtual Machines |
| **PaaS** (Platform as a Service) | Your code and its settings | Also the OS and runtime | AWS Elastic Beanstalk, Azure App Service |
| **SaaS** (Software as a Service) | Only your data and users | Everything | Microsoft 365, Gmail |

Words you will meet in every cloud:

| Word | Meaning |
|---|---|
| **Region** | A geographic area with several data centres (for example `ca-central-1` in Montréal) |
| **Availability zone (AZ)** | One data centre, or group of them, inside a region. Spreading VMs over two AZs survives the loss of one. |
| **VPC / virtual network** | Your own private network inside the cloud, with subnets and routing |
| **Security group** | A firewall attached to a VM. Default: everything inbound is blocked. |
| **Instance type** | The size of a VM (`t3.micro` = 2 vCPU, 1 GB). Bigger costs more per hour. |
| **Image (AMI)** | The disk template a VM starts from. A VM image is the cloud's version of a Vagrant box. |
| **Key pair** | The SSH key you use to log in. The provider stores the public half. |

**The shared responsibility model.** The provider secures the data centre and the hypervisor. **You** secure what you put in it: operating-system updates, firewall rules, passwords, data. Most cloud breaches come from the customer side (an open storage bucket, a leaked key), not from the provider.

**Cost is part of the job.** A VM left running costs money every hour. IaC helps twice: `terraform destroy` removes everything you created, and the code tells you exactly what exists. Typical rules: tag every resource with an owner, set a budget alert, and destroy lab environments the same day.

**Why Terraform matters here.** Clicking in a web console is the cloud version of a snowflake server. Every cloud has its own console, but Terraform describes AWS, Azure and Google with the same language and the same four commands. The Docker work in this lecture is the same workflow; only the provider changes.

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
## Step 6. Locals, `for_each` and `depends_on`

`count` numbers copies (0, 1, 2). When the copies have **names**, use `for_each`. Add a second tier to the same project: a database-like container and an app container, each from a map.

```bash
cat > tiers.tf <<'EOF'
locals {
  project = "iac-practice"
  tiers = {
    app = { image = "nginx:alpine", port = 8100 }
    api = { image = "httpd:alpine", port = 8101 }
  }
}

resource "docker_image" "tier" {
  for_each     = local.tiers
  name         = each.value.image
  keep_locally = true
}

resource "docker_container" "tier" {
  for_each = local.tiers
  name     = "${local.project}-${each.key}"
  image    = docker_image.tier[each.key].image_id

  ports {
    internal = 80
    external = each.value.port
  }

  labels {
    label = "owner"
    value = "student"
  }
}
EOF
```

| Syntax | Meaning |
|---|---|
| `locals { ... }` | Named values used inside the code. They are not inputs. |
| `for_each = map` | One copy per entry. `each.key` is the entry name, `each.value` its data. |
| `docker_image.tier[each.key]` | The copy of the image with the same key |
| `labels` | Tags on a resource. In a cloud these carry owner, cost centre, environment. |

```bash
terraform plan  # Two images and two containers are added. Notice the addresses: docker_container.tier["app"], not [0].
```

```bash
terraform apply -auto-approve  # Create them.
```

```bash
curl -sI http://localhost:8100 | head -1 && curl -sI http://localhost:8101 | head -1  # Both answer with HTTP 200.
```

Why `for_each` beats `count` for named things: remove the `app` entry and only `app` is destroyed. With `count`, removing item 0 shifts every number and Terraform would change all the others.

Terraform builds the order from references. When there is **no** reference but one thing must wait for another, say it with `depends_on`:

```hcl
resource "docker_container" "late" {
  name       = "late"
  image      = docker_image.nginx.image_id
  depends_on = [docker_container.web]
}
```

Use it rarely: a real reference is better.

---
## Step 7. Read the plan like a reviewer

Change one setting and read what Terraform says. Edit `tiers.tf`: change the `api` port from 8101 to 8102, then:

```bash
terraform plan -no-color | grep -E "^\s+[~+-]|Plan:"  # Look for "~" (change in place) or "-/+" (destroy and recreate).
```

```bash
terraform apply -auto-approve  # Apply it. A port cannot change on a running container, so Terraform replaces it.
```

Learn the symbols. They matter much more in a cloud, where "replace" can mean a lost database.

| Symbol | Meaning | Risk |
|---|---|---|
| `+` | Create | Low |
| `~` | Update in place | Usually low |
| `-/+` | Destroy, then create | **Check for data loss** |
| `-` | Destroy | Confirm it is intended |

A habit used by professionals: save the plan, review it, then apply exactly that plan.

```bash
terraform plan -out=tfplan -no-color | tail -2  # Save the plan to a file.
```

```bash
terraform apply tfplan  # Apply exactly what you reviewed. No prompt is needed because the plan is fixed.
```

---
## Step 8. The same workflow in the cloud (read and validate)

You do **not** need a cloud account this week. A cloud account needs a credit card, and a wrong command can cost money. You will write real AWS code and let Terraform **check** it, without creating anything.

Make a folder:

```bash
mkdir -p ~/iac-practice/cloud && cd ~/iac-practice/cloud  # Create the cloud folder and move into it.
```

```bash
cat > main.tf <<'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "ca-central-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = { Name = "iac-practice-vpc", Owner = "student" }
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  tags       = { Name = "iac-practice-public" }
}

resource "aws_security_group" "web" {
  name   = "iac-practice-web"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = "ami-0123456789abcdef0"
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  tags                   = { Name = "iac-practice-web", Owner = "student" }
}

output "web_private_ip" {
  value = aws_instance.web.private_ip
}
EOF
```

Read it. Everything from Step 2 is here: a provider, resources, references (the instance uses the subnet and the security group, so Terraform creates them first), variables and an output. Only the provider and the resource types changed.

| Resource | What it is |
|---|---|
| `aws_vpc` | Your private network, `10.0.0.0/16` |
| `aws_subnet` | A slice of that network, `10.0.1.0/24` |
| `aws_security_group` | The firewall: allow web traffic in (port 80), everything out |
| `aws_instance` | The VM. `ami` is its disk image (this one is a placeholder). |

```bash
terraform init  # Download the AWS provider (a large download, about 1 minute).
```

```bash
terraform fmt -check && terraform validate  # Check the formatting and the code. No account is needed. You should see "Success! The configuration is valid."
```

**Do not run `terraform apply` here.** There are no credentials, and the AMI is a placeholder. In a real project you would also: set credentials through environment variables (never in the code), look up the current AMI with a `data` source, keep the state in a remote bucket, and run `terraform destroy` when finished.

Now break it on purpose and read the error:

```bash
sed -i.bak 's/subnet_id              = aws_subnet.public.id/subnet_id              = aws_subnet.private.id/' main.tf && terraform validate; mv main.tf.bak main.tf  # Point at a subnet that does not exist, read the error, then restore the file.
```

The message `Reference to undeclared resource` names the file and line. A cloud mistake caught by `validate` costs nothing.

### Azure in two lines

Azure is the same idea with a different provider and names:

| AWS | Azure |
|---|---|
| `aws_vpc` | `azurerm_virtual_network` |
| `aws_security_group` | `azurerm_network_security_group` |
| `aws_instance` | `azurerm_linux_virtual_machine` |
| Region `ca-central-1` | Location `canadacentral` |

Week 12 uses Ansible against servers like this. Terraform makes the server, Ansible sets it up.

---
## Step 9. State in a team

On your laptop, state is a file. A team cannot share a file on one laptop, so real projects use a **remote backend**: the state lives in a shared bucket and is **locked** while someone applies, so two people never change the same thing together. The setting looks like this (read only):

```hcl
terraform {
  backend "s3" {
    bucket = "my-team-terraform-state"
    key    = "web/terraform.tfstate"
    region = "ca-central-1"
  }
}
```

| Question | Answer |
|---|---|
| Why not Git? | State can hold passwords, and two people can overwrite each other. |
| What does the lock do? | A second `apply` waits or fails instead of corrupting the state. |
| What if state is lost? | Terraform forgets what it built and tries to create it again. Back it up. |

---
## Step 10. Destroy

```bash
cd ~/iac-practice/tf  # Go back to the Docker project.
```

```bash
terraform destroy  # Show what would be deleted and ask. Type yes. Everything Terraform created is removed, in the right order.
```

```bash
docker ps -a --filter name=tf-web --filter name=iac-practice  # Nothing is left.
```

The `.tf` files are all you need to build it again. That is the point of IaC.

---
## Practice questions

Answer these in your head or on paper before the lab. The answers follow.

1. A colleague logs in to a server and edits a config file by hand. Which two IaC problems does that cause?
2. What is the difference between `plan` and `apply`?
3. Why is `for_each` safer than `count` for a list of named servers?
4. Your plan shows `-/+` on a database. What do you do?
5. A teammate says "the cloud is just someone else's computer, so security is their job". Which model contradicts this?

**Answers:** (1) Drift and a snowflake that nobody can rebuild. (2) `plan` only previews; `apply` changes things. (3) Each entry has a stable key, so removing one does not renumber and change the others. (4) Stop and read why it is replaced; it means the data is destroyed. Change the code so the resource is updated in place, or back up first. (5) The shared responsibility model.

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
| `terraform plan -out=FILE` | Save a reviewed plan |
| `terraform apply FILE` | Apply exactly that plan |

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
| `Error: Reference to undeclared resource` | A name in a reference is misspelled or the resource does not exist. Read the file and line. |
| `terraform: command not found` | Terraform is not installed in this terminal. See [W11_Setup_Terraform.md](W11_Setup_Terraform.md). |
| macOS: `unix:///var/run/docker.sock` not found | Docker Desktop > Settings > Advanced: enable **Allow the default Docker socket to be used**, or set `provider "docker" { host = "unix:///Users/YOU/.docker/run/docker.sock" }`. |
| Windows: Docker works in Ubuntu but Terraform does not | Run Terraform in the **Ubuntu** terminal, with Docker Desktop's WSL integration on. |

## Summary

- A VM is a whole computer in software, run by a hypervisor. Vagrant describes VMs as code for development.
- Infrastructure as Code keeps infrastructure in text files in Git, so it is reviewable and repeatable.
- Terraform workflow: `init`, `plan`, `apply`, `destroy`. Always read the plan. State is Terraform's memory: never edit it, never commit it.
- Variables make code reusable. `count` makes numbered copies, `for_each` makes named ones. A hand change causes drift, and `apply` repairs it.
- The cloud rents you VMs and networks by the hour (IaaS, PaaS, SaaS). You secure what you put in it (shared responsibility), and you destroy what you do not need.
- The same Terraform workflow works for AWS and Azure; only the provider and resource types change. `validate` checks cloud code for free.

**Next:** the Week 11 lab (graded) builds a Vagrantfile and a Terraform project with your own seed.
