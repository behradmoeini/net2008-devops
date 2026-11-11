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

## 2. VirtualBox and Vagrant (optional)

Virtual machines on a laptop depend on the processor. The Week 11 lab is written so that you finish **without** a virtual machine. Install these only if your laptop can run them, and only if you want to try `vagrant up`.

- **Windows 10 or 11, macOS with Intel, and Intel or AMD Linux:** use the commands below.
- **macOS with Apple silicon (M1 to M4):** VirtualBox does not run Intel boxes. Skip this section. The lab has a path for you.
- VirtualBox can conflict with WSL 2 and Docker Desktop on some Windows laptops. If Docker stops working after you install it, uninstall VirtualBox.

<details>
<summary>macOS (Intel) / Linux (Terminal)</summary>

macOS with Intel:

```bash
brew install --cask virtualbox vagrant
```

macOS asks you to allow the VirtualBox system extension in System Settings > Privacy & Security. Allow it and restart.

Ubuntu or Debian Linux (the HashiCorp repository from section 1 must be added first):

```bash
sudo apt update && sudo apt install -y virtualbox vagrant
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

**Vagrant must be installed in Windows, not in Ubuntu.** Open **PowerShell as Administrator** (right-click the Start button, choose Terminal (Admin)):

```powershell
winget install --id Oracle.VirtualBox -e
```

```powershell
winget install --id Hashicorp.Vagrant -e
```

Close PowerShell, open a new one (not as Administrator), and check:

```powershell
vagrant --version
```

</details>
