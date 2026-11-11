# Week 11 Lecture: Virtualization and Infrastructure as Code
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Docker running and **Terraform** installed (see [W11_Setup_Terraform.md](W11_Setup_Terraform.md)). **Vagrant and VirtualBox are optional**: the Terraform part of this week runs with Docker only, so every student can finish it.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- Do the steps in order. All practice work happens in one folder, `~/iac-practice`.
- Your "servers" are **Docker containers** on your laptop. Terraform treats them like real servers.

---
## The big picture

### Virtual machines

A **virtual machine** (VM) is a pretend computer that runs inside your real computer. For example, you can run Ubuntu Linux in a window on a Mac without erasing the Mac. A VM has its own pretend disk, its own pretend network card and its own operating system.

A program called a **hypervisor** creates the VMs and shares the real computer's memory and CPU between them. One physical machine can run many VMs (for example one for a web server and one for a database), and the hypervisor keeps them apart.

There are two kinds of hypervisor. The only difference is **where the hypervisor sits**.

| | Type 2 ("hosted") | Type 1 ("bare metal") |
|---|---|---|
| **Simple idea** | An app you install on your laptop | The first and only thing on the server |
| **Underneath it** | Your normal system (macOS, Windows) | Nothing. Just the hardware. |
| **Where you see it** | Your laptop | Data centres (AWS, Azure, Google) |
| **Examples** | VirtualBox, VMware Workstation, Parallels | KVM, VMware ESXi, Microsoft Hyper-V |

```text
  TYPE 2 (your laptop)          TYPE 1 (a cloud server)

  [ VM ]  [ VM ]                [ VM ]  [ VM ]  [ VM ]
  [ VirtualBox app ]            [ Hypervisor ]
  [ macOS / Windows ]           [ Hardware ]
  [ Hardware ]
```

**Examples:**

- You open VirtualBox on your laptop and start Ubuntu in a window. That is **type 2**. It is just an app, like Chrome.
- You click "launch server" on AWS. Amazon runs your VM on a big machine in a data centre, with no desktop and no Chrome on it. That is **type 1**.

**Why the cloud uses type 1:** fewer layers means faster and cheaper, and a data centre has thousands of VMs to run. **Why you use type 2:** you already have a laptop with an operating system, and installing an app is easy.

**What to remember:** type 2 = an app on your laptop (VirtualBox). Type 1 = the cloud's way (no system underneath). Your VM behaves the same either way.

**How does a VM connect to the network?** A VM has a pretend network card. You choose how it plugs in:

| Mode | In plain words | Example |
|---|---|---|
| **NAT** | The VM can go out to the internet through your laptop, but nobody can come in. | The VM downloads updates. Nobody can open its web server. |
| **Host-only (private network)** | The VM can only talk to your laptop and other VMs. Not the internet. | You open the VM's web page from your own laptop. A private lab. |
| **Bridged** | The VM gets its own address on your real network, like a separate computer. | Your phone on the same Wi-Fi can open the VM's web page. |

### The cloud

**Why rent?** On a Monday morning a website gets 10 visitors. On a Friday night it gets 10,000. If you **bought** servers for Friday night, nine of them would sit idle all week. In the cloud you **rent** servers by the hour: ten on Friday evening, one on Monday.

A **cloud provider** (AWS, Microsoft Azure, Google Cloud) owns huge buildings full of servers. You ask for a VM, a network or a database, and you pay for the hours you use. No hardware to buy, and you can ask for 1 server or 100 in a few minutes. You ask through a web page, or through code. Code is faster and repeatable, and that is where today's topic comes in.

**Three ways to rent.** The same website, three ways to run it:

| Model | What you would do | You manage | The provider manages |
|---|---|---|---|
| **IaaS** (Infrastructure as a Service), for example AWS EC2 | Rent an empty VM. Install updates, the web server and the website yourself. | The operating system and everything above it | Hardware, network, hypervisor |
| **PaaS** (Platform as a Service), for example Azure App Service | Upload the website code. The provider runs it. | Your code and its settings | Also the operating system |
| **SaaS** (Software as a Service), for example Gmail | Do not build anything. Just use it. | Only your data and your users | Everything |

This course uses mostly IaaS: you get an empty server and you build it up.

**Cloud terminology:**

| Word | Plain meaning | Example |
|---|---|---|
| **Region** | A part of the world where the provider has data centres | Your customers are in Ottawa, so you pick `ca-central-1` (Montréal), the closest one. |
| **Availability zone (AZ)** | One separate data centre inside a region | Put one VM in each of two zones. If one building loses power, your site stays up. |
| **VPC (virtual network)** | Your own private network inside the cloud | Other customers' servers are not on it. |
| **Subnet** | A smaller slice of that network | One slice for web servers, one for databases. |
| **Security group** | A firewall around a VM. It lists who may come in. | "Allow port 80 so people can see the website. Block everything else." |
| **Instance type** | The size of a VM | `t3.micro` is small and cheap (2 CPUs, 1 GB of memory). A bigger size costs more per hour. |
| **Image (AMI)** | The starting disk of a VM | "Ubuntu 22.04". It is the cloud's version of a Vagrant box. |
| **Key pair** | The key you use to log in with SSH | You keep the private half. The cloud keeps the lock. |

**Who is responsible for security? (shared responsibility)** If you store customer names and addresses in the cloud, who protects them?

- The **provider** (AWS) secures the data centre and the hypervisor.
- **You** secure what you put inside: updates on the operating system, the firewall rules, the passwords, the customer data.

Most cloud break-ins are the customer's mistake, not the provider's. Examples: a storage bucket left open to the world, or a password key pasted into a public GitHub repository.

**Money.** A test server you forget to turn off keeps costing money every hour, all weekend. So:

- Put an **owner tag** on everything you create, so people know whose it is.
- Set a **budget alert** so you get an email if the bill grows.
- **Delete lab servers the same day.** With Terraform this is one command: `terraform destroy`.

**Why Terraform matters in the cloud.** You can click through the AWS website to create servers. But three weeks later, nobody remembers what was clicked. With Terraform the list of servers is written in a file. If you move to Azure or Google, Terraform uses the same language and the same four commands. Today you practise with Docker. Later you only change the provider.

### The problem with building servers by hand

You click through an installer, install packages, change settings. Three weeks later nobody can say exactly what is on the server, and nobody can build the same one again. One teammate fixed a bug by editing a file on the server and told nobody. When the server crashes, you cannot rebuild it.

Such a server is called a **snowflake**: every one is different, and fragile. When you build a second server, the bug is back.

### Infrastructure as Code (IaC)

**The idea.** Instead of clicking, you **write** what you want in a text file. A tool reads the file and builds it. The file goes in Git, like your Python code.

**Think of a recipe.** If a chef makes a dish by feel, nobody else can make the same dish. If the chef writes the recipe, any cook can make it, and it tastes the same every time. IaC is the recipe for your servers.

What you get from this:

- **History:** Git shows who changed what and when.
- **Review:** a teammate reads your change before it is applied.
- **Repeat:** run it again and get the same result. Need a copy for testing? Run it twice.
- **Undo:** go back to an older version of the file.

**Three tools, three jobs:**

| Tool | What it does | Example | This week |
|---|---|---|---|
| **Vagrant** | Creates a VM on your own computer, for testing | Run one command and get a fresh Ubuntu VM to test a website. | Read a `Vagrantfile`. Run it if your laptop can. (Step 1) |
| **Terraform** | Creates servers and networks, in the cloud or on your laptop | One file says "make a network and two web servers", and Terraform makes them. | You build real infrastructure (Docker containers). (Steps 2 to 10) |
| **Ansible** | Sets up the **inside** of a server: installs software, copies files | After the servers exist, it installs the web server software and the website on them. | Week 12 |

Three separate jobs. **Vagrant gives you a test VM. Terraform creates the real servers. Ansible installs the software on them.** Vagrant and Terraform are explained in the steps below. Ansible is next week.

---
## Step 1. Vagrant: a VM as code (read, and run if you can)

A `Vagrantfile` is a recipe for a VM: which Ubuntu, how much memory, which network address. The command `vagrant up` builds the VM with VirtualBox, and `vagrant destroy` deletes it. If you break the VM, delete it and get an identical one back in a few minutes. A new teammate gets the same VM from the same file.

```text
Vagrantfile (what VM you want) --vagrant up--> a VM on your laptop (VirtualBox)
```

Read this `Vagrantfile`. It describes one Ubuntu VM:

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

Read it line by line:

| Line | In plain words |
|---|---|
| `config.vm.box` | Start from this ready-made Ubuntu image (called a "box") |
| `config.vm.hostname` | Name the VM `demo-vm` |
| `config.vm.network "private_network"` | Give it a private address, `192.168.56.20`, that only your laptop can reach |
| `vb.memory`, `vb.cpus` | Give it 1 GB of memory and 1 CPU |
| `config.vm.provision "shell"` | Run this one command inside the VM the first time it starts |

**Install VirtualBox and Vagrant (optional).** Do this only if you have an Intel or AMD laptop. Apple silicon (M1 to M4) cannot run these Intel VMs: skip this and read the file only. VirtualBox can conflict with WSL 2 and Docker Desktop on some Windows laptops. If Docker stops working after you install it, uninstall VirtualBox.

<details>
<summary>macOS (Intel) / Linux (Terminal)</summary>

macOS with Intel:

```bash
brew install --cask virtualbox vagrant  # Install both tools with Homebrew. macOS asks you to allow the VirtualBox system extension in System Settings > Privacy & Security, then restart.
```

Ubuntu or Debian Linux (this uses the HashiCorp repository from the [setup guide](W11_Setup_Terraform.md)):

```bash
sudo apt update && sudo apt install -y virtualbox vagrant  # Install both tools.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

Vagrant must be installed in **Windows**, not in the Ubuntu terminal. Open **PowerShell as Administrator** (right-click the Start button, choose Terminal (Admin)):

```powershell
winget install --id Oracle.VirtualBox -e  # Install VirtualBox.
```

```powershell
winget install --id Hashicorp.Vagrant -e  # Install Vagrant.
```

Close PowerShell and open a new one (not as Administrator), then check:

```powershell
vagrant --version  # Vagrant must answer with a version number.
```

</details>

**If you installed Vagrant and VirtualBox**, try it. Windows students run these commands in PowerShell. The commands after the first one are the same on every system.

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
mkdir -p ~/iac-practice/vm && cd ~/iac-practice/vm  # Create a folder for the VM and move into it.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
New-Item -ItemType Directory -Force ~/iac-practice/vm | Out-Null; Set-Location ~/iac-practice/vm  # Create a folder for the VM and move into it.
```

</details>

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

You write what you want to exist in `.tf` files (the language is called HCL and is easy to read). Terraform compares your file with what exists now and does only the work needed to match. If the file says "2 web servers" and 0 exist, it creates 2. If 2 exist, it does nothing. If 3 exist, it removes 1.

```text
.tf files (what you want) --terraform plan--> list of changes --terraform apply--> real infrastructure
                                                                                          |
terraform.tfstate (what Terraform believes exists) <------------ updated after every apply
```

Today a "server" is a Docker container, because you already have Docker. New words (provider, resource, plan, state, variable, output) are explained at the moment you first use them.

Create a folder:

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

Read the file in plain words:

- `terraform { ... }`: "I need the Docker plug-in. Version 3.x is fine."
- `provider "docker" {}`: "Use the Docker on this laptop."
- `resource "docker_image" "nginx"`: "I want the nginx image to exist." The two words after `resource` are the **type** (`docker_image`) and the **name** you choose (`nginx`).
- `resource "docker_container" "web"`: "I want a container called `tf-web`. Make it reachable on port 8095 of my laptop."
- `image = docker_image.nginx.image_id`: this line points at the image above. Because of it, Terraform knows to make the **image first**. You never write the order. Terraform works it out from these pointers.

Now the workflow. Four commands, always in this order:

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

**You should see** `Plan: 2 to add, 0 to change, 0 to destroy.` That means: "I will create 2 things (the image and the container)."

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

**"Idempotent"** is a big word for a simple idea: doing it twice gives the same result as doing it once. For example, running `apply` twice does not create four web servers, it keeps the two you asked for.

---
## Step 3. State

Terraform keeps a notebook of everything it built. This notebook is the **state**.

```bash
terraform state list  # List everything Terraform believes it manages.
```

```bash
terraform show | head -30  # Show the stored details of those resources.
```

```bash
ls -la  # Look at the folder: terraform.tfstate is the state file, .terraform.lock.hcl pins the provider version.
```

Which files go into Git?

| File or folder | Commit to Git? | Why |
|---|---|---|
| `*.tf` | **Yes** | Your code |
| `.terraform.lock.hcl` | **Yes** | Makes everyone use the same plug-in version |
| `terraform.tfstate`, `terraform.tfstate.backup` | **No** | The notebook can contain passwords, and it belongs to one real environment. Teams keep it in a shared safe place. |
| `.terraform/` | **No** | Downloaded plug-ins. `terraform init` makes it again. |

---
## Step 4. Variables, outputs and `count`

Hard-coded values are a problem. If the number of servers is typed in the code, you must edit the code every time you need more or fewer servers. A **variable** fixes that: you name the value once, and change it from outside. **`count`** makes that many copies. **Outputs** print useful results (like web addresses) at the end.

Create three files:

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

| Syntax | In plain words | Example |
|---|---|---|
| `var.instances` | The value of the variable `instances` | `2` |
| `count = var.instances` | Make that many copies | `count = 2` makes two containers |
| `count.index` | The copy's number, starting at 0 | 0 for the first, 1 for the second |
| `"text ${expression}"` | Put a value inside a piece of text | `"tf-web-${count.index}"` becomes `tf-web-0`, `tf-web-1` |
| `upload { ... }` | Put a file in the container when it is created | Each web server gets its own page, so you can tell them apart |
| `output` | A value printed at the end of `apply` | The two web addresses |

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

Now change the number of servers **without touching the code**:

```bash
terraform apply -auto-approve -var="instances=3"  # Ask for 3 containers. Terraform adds exactly one.
```

```bash
terraform apply -auto-approve  # Back to the default of 2. Terraform removes exactly one.
```

You can also write the values in a file named `terraform.tfvars` (a line like `instances = 3`). Terraform reads it by itself.

---
## Step 5. Drift: when the real world changes

**Drift** means: reality no longer matches your code. The code says "2 web servers", but a teammate deletes one by hand. Now there is only 1, and nobody told you. Watch Terraform notice.

```bash
docker rm -f tf-web-1  # Delete a container behind Terraform's back.
```

```bash
terraform plan  # Terraform compares the state with the real world and plans to create tf-web-1 again.
```

```bash
terraform apply -auto-approve  # Repair the difference.
```

This is why you change infrastructure **only through the code**. A hand change is lost at the next `apply`, and nobody will understand why it vanished.

---
## Step 6. Names for your copies: `locals` and `for_each`

`count` gives copies a **number** (0, 1, 2). Sometimes the copies have different **names and jobs**: an `app` server and an `api` server. For that use `for_each`. Add them to the same project:

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

| Syntax | In plain words | Example |
|---|---|---|
| `locals { ... }` | Named values used inside the file. They are not inputs. | `project = "iac-practice"` |
| `for_each = map` | One copy per entry in a list of named things | One for `app`, one for `api` |
| `each.key` | The entry's name | `app` |
| `each.value` | The entry's details | `{ image = "nginx:alpine", port = 8100 }` |
| `docker_image.tier[each.key]` | The image copy with the same name | The `app` container uses the `app` image |
| `labels` | A tag on a resource. In a cloud these carry owner, project, cost. | `owner = student` |

```bash
terraform plan  # Two images and two containers are added. Notice the addresses: docker_container.tier["app"], not [0].
```

```bash
terraform apply -auto-approve  # Create them.
```

```bash
curl -sI http://localhost:8100 | head -1 && curl -sI http://localhost:8101 | head -1  # Both answer with HTTP 200.
```

**Why `for_each` is safer than `count` for named things.** Suppose you have three servers numbered 0, 1 and 2, and you remove server 0. The old 1 becomes the new 0 and the old 2 becomes the new 1: every number changed, so Terraform sees every server as "changed". With names (`app`, `api`), removing `app` only removes `app`.

Terraform works out the order from the pointers. If there is **no** pointer but one thing must wait for another, say it with `depends_on`:

```hcl
resource "docker_container" "late" {
  name       = "late"
  image      = docker_image.nginx.image_id
  depends_on = [docker_container.web]
}
```

Use it rarely: a real pointer is better.

---
## Step 7. Read the plan like a careful person

Always read the plan before you apply. Every line starts with a symbol. Let us change one setting and see.

Change the `api` port from 8101 to 8102:

```bash
sed -i.bak 's/port = 8101/port = 8102/' tiers.tf && rm tiers.tf.bak  # Edit tiers.tf for you. (You can also open the file and change the number by hand.)
```

Now read the plan:

```bash
terraform plan -no-color | grep -E "^\s+[~+-]|Plan:"  # Look for "~" (change in place) or "-/+" (destroy and recreate).
```

```bash
terraform apply -auto-approve  # Apply it. A port cannot change on a running container, so Terraform replaces it.
```

Learn the symbols. They matter much more in a cloud, where "replace" can mean a lost database.

| Symbol | Meaning | Example | Risk |
|---|---|---|---|
| `+` | Create something new | Add a third web server | Low |
| `~` | Change something without deleting it | Change the label on a server | Usually low |
| `-/+` | Delete it and build it again | Change the port of a server. It is deleted and a new one is built. If this were the database, **all the orders stored in it would be lost.** | **High. Stop and read.** |
| `-` | Delete | Remove a web server you no longer need | Check it is what you wanted |

A habit professionals use: save the plan, review it, then apply exactly that plan. Nothing changes between your review and your apply.

```bash
terraform plan -out=tfplan -no-color | tail -2  # Save the plan to a file.
```

```bash
terraform apply tfplan  # Apply exactly what you reviewed. No prompt is needed because the plan is fixed.
```

---
## Step 8. The same workflow in the cloud (read and validate)

Now the same workflow with a cloud provider. You do **not** need a cloud account this week. A cloud account needs a credit card, and a wrong command can cost money. Instead you will write real AWS code for a network and a web server, and let Terraform **check** it, without creating anything. This is like proofreading a letter you do not send.

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

Read it. It looks like the Docker file from Step 2: a provider, resources, pointers, variables and an output. Only the provider and the resource types changed. That is the whole point: **one skill, many clouds**.

| Resource | In plain words |
|---|---|
| `aws_vpc` | Your private network, `10.0.0.0/16` |
| `aws_subnet` | A slice of that network, `10.0.1.0/24` |
| `aws_security_group` | The firewall: let web visitors in on port 80, let everything out |
| `aws_instance` | The VM. `ami` is its starting disk (this one is a made-up placeholder). |

The instance points at the subnet and the security group, so Terraform creates those first.

```bash
terraform init  # Download the AWS provider (a large download, about 1 minute).
```

```bash
terraform fmt -check && terraform validate  # Check the formatting and the code. No account is needed. You should see "Success! The configuration is valid."
```

**Do not run `terraform apply` here.** There are no credentials, and the disk image is a placeholder. In a real project you would also: give credentials through environment variables (never in the code), look up the real disk image with a `data` source, keep the state in a shared bucket, and run `terraform destroy` when you finish.

Now break it on purpose and read the error. Mistakes are the best way to learn:

```bash
sed -i.bak 's/subnet_id              = aws_subnet.public.id/subnet_id              = aws_subnet.private.id/' main.tf && terraform validate; mv main.tf.bak main.tf  # Point at a subnet that does not exist, read the error, then restore the file.
```

The message `Reference to undeclared resource` says which file and which line. A mistake caught by `validate` costs nothing. A mistake caught by the cloud bill costs money.

### Azure in a table

Azure is the same idea with different names:

| AWS | Azure |
|---|---|
| `aws_vpc` | `azurerm_virtual_network` |
| `aws_security_group` | `azurerm_network_security_group` |
| `aws_instance` | `azurerm_linux_virtual_machine` |
| Region `ca-central-1` | Location `canadacentral` |

Week 12 uses Ansible on servers like this. Terraform makes the server, Ansible sets it up.

---
## Step 9. State in a team

On your laptop the state notebook is one file. But a team cannot share a file on one laptop. Real projects keep the state in a **shared safe place** called a **remote backend**, for example a bucket in AWS. While one teammate runs `apply`, the state is **locked**, so two teammates never change the servers at the same time.

The setting looks like this (read only, do not run it):

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
| Why not keep state in Git? | It can contain passwords, and two people can overwrite each other's version. |
| What does the lock do? | A second `apply` has to wait, instead of corrupting the state. |
| What if the state is lost? | Terraform forgets what it built and tries to create everything again. So back it up. |

---
## Step 10. Destroy

Clean up. One command removes everything Terraform created.

```bash
cd ~/iac-practice/tf  # Go back to the Docker project.
```

```bash
terraform destroy  # Show what would be deleted and ask. Type yes. Everything Terraform created is removed, in the right order.
```

```bash
docker ps -a --filter name=tf-web --filter name=iac-practice  # Nothing is left.
```

The `.tf` files are all you need to build it again. That is the point of IaC: **delete is safe, because the recipe is saved.**

---
## Practice questions

Answer these in your head or on paper before the lab. Open the answers only after you tried.

1. A colleague logs in to a server and edits a config file by hand. Which two IaC problems does that cause?
2. What is the difference between `plan` and `apply`?
3. Why is `for_each` safer than `count` for a list of named servers?
4. Your plan shows `-/+` on a database. What do you do?
5. A teammate says "the cloud is just someone else's computer, so security is their job". Which idea says this is wrong?

<details>
<summary>Show the answers (try the questions first)</summary>

(1) Drift (the real server no longer matches the code) and a snowflake that nobody can rebuild. (2) `plan` only shows a preview; `apply` really makes the changes. (3) Each entry has its own name, so removing one does not renumber and change the others. (4) Stop and read why it is replaced; it means the data is destroyed. Change the code so the resource is updated in place, or back up first. (5) The shared responsibility model: the provider secures the building, you secure what is inside.

</details>

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
| `Error: Reference to undeclared resource` | A name in a pointer is misspelled or the resource does not exist. Read the file and line. |
| `Error: Unsupported argument` | A typo in an attribute name, or the wrong block type. Read the line and column in the message. |
| `Error: container exited immediately` | The image or command is wrong. `docker logs NAME`. |
| `Error acquiring the state lock` | A previous run was killed. Wait a minute, or `terraform force-unlock ID` (the ID is in the message). |
| `terraform: command not found` | Terraform is not installed in this terminal. See [W11_Setup_Terraform.md](W11_Setup_Terraform.md). |
| macOS: `unix:///var/run/docker.sock` not found | Docker Desktop > Settings > Advanced: enable **Allow the default Docker socket to be used**, or set `provider "docker" { host = "unix:///Users/YOU/.docker/run/docker.sock" }`. |
| Windows: Docker works in Ubuntu but Terraform does not | Run Terraform in the **Ubuntu** terminal, with Docker Desktop's WSL integration on. |

## Summary

- A VM is a pretend computer inside a real one, run by a hypervisor. Type 2 is an app on your laptop. Type 1 is what the cloud uses.
- The cloud is rented computers. You secure what you put in it (shared responsibility), and you delete what you do not need.
- Infrastructure as Code means you write the servers you want in text files in Git. That makes them reviewable and repeatable.
- Terraform workflow: `init`, `plan`, `apply`, `destroy`. Always read the plan. State is Terraform's notebook: never edit it, never commit it.
- Variables make code reusable. `count` makes numbered copies, `for_each` makes named ones. A hand change causes drift, and `apply` repairs it.
- The same workflow works for AWS and Azure; only the provider and resource types change. `validate` checks cloud code for free.

**Next:** the Week 11 lab (graded) builds a Vagrantfile, a Terraform project with your own seed, and AWS code that you validate.
