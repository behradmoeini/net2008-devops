# Week 11 Setup: Terraform and Virtual Machines
**NET2008 DevOps · Algonquin College**

You do this setup **once**, before the Week 11 lecture. It assumes you finished the [Week 9 lecture: How to install Docker](../week09/W09_Lecture_Containers.md#how-to-install-docker): a working terminal (Ubuntu on WSL 2 for Windows) and Docker running.

## 1. Terraform

<details>
<summary>macOS (Terminal)</summary>

```bash
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
```

</details>

<details open>
<summary>Windows (Ubuntu terminal) and Ubuntu or Debian Linux</summary>

Windows students run these in the **Ubuntu (WSL 2)** app, not in PowerShell.

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
```

```bash
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

```bash
sudo apt update && sudo apt install -y terraform
```

</details>

**Check** (in the same terminal):

```bash
terraform version
```

**macOS: if Terraform cannot find Docker.** If `terraform apply` later says it cannot connect to the Docker daemon at `/var/run/docker.sock` while `docker ps` works, run this in the same terminal:

```bash
export DOCKER_HOST=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
```

## 2. A hypervisor and Vagrant (optional)

Virtual machines on a laptop depend on the processor. The Week 11 lab is written so that you finish **without** a virtual machine. Install these only if your laptop can run them.

| Your computer | VM by hand | `vagrant up` |
|---|---|---|
| Windows (Intel or AMD), Mac with an Intel chip, Linux on Intel or AMD | VirtualBox | Yes |
| Mac with Apple silicon (M1 to M4) | **UTM** | Yes, with VirtualBox 7.2 and the ARM version of the box |
| Windows with an ARM chip, Windows 11 **Pro or Enterprise** | **Hyper-V** (built into Windows; the lecture shows the steps) | Maybe: VirtualBox 7.2 on Windows ARM is experimental and untested here. If it fails, run `vagrant validate`. |

VirtualBox can conflict with WSL 2 and Docker Desktop on some Windows laptops. If Docker stops working after you install it, uninstall VirtualBox.

First check your processor (macOS or Linux):

```bash
uname -m  # x86_64 means Intel or AMD. arm64 or aarch64 means Apple silicon or ARM.
```

<details>
<summary>macOS / Linux (Terminal)</summary>

Mac with an Intel chip:

```bash
brew install --cask virtualbox vagrant
```

macOS asks you to allow the VirtualBox system extension in System Settings > Privacy & Security. Allow it and restart.

Mac with Apple silicon:

```bash
brew install --cask utm virtualbox vagrant
```

Ubuntu or Debian Linux on Intel or AMD (the HashiCorp repository from section 1 must be added first):

```bash
sudo apt update && sudo apt install -y virtualbox vagrant
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

**Vagrant must be installed in Windows, not in Ubuntu.** Download and run the installers (click **Yes** if Windows asks for permission):

- VirtualBox: <https://www.virtualbox.org/wiki/Downloads> (click **Windows hosts**)
- Vagrant: <https://developer.hashicorp.com/vagrant/install> (click the **Windows** installer)

Close PowerShell, open a new one, and check:

```powershell
vagrant --version
```

</details>

You also need an Ubuntu Server ISO for the VM by hand. The lecture links to it.

## 3. A free Azure student account (optional)

The cloud hands-on in the lecture needs an Azure account. **Azure for Students** gives 100 US dollars of credit for 12 months and does not ask for a credit card. Go to <https://azure.microsoft.com/free/students> and sign in with your **school email**. If it refuses your email, skip the Azure parts. The graded lab does not need an account.
