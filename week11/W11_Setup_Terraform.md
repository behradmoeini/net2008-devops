# Week 11 Setup: Terraform and Virtual Machines
**NET2008 DevOps · Algonquin College**

You do this setup **once**, before the Week 11 lecture. It assumes you finished the [Week 9 setup](../week09/W09_Setup_Your_Laptop.md): a working terminal (Ubuntu on WSL 2 for Windows) and Docker running.

## 1. Terraform

**macOS:**

```bash
brew tap hashicorp/tap && brew install hashicorp/tap/terraform
```

**Windows (Ubuntu terminal) and Ubuntu or Debian Linux:**

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
```

```bash
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

```bash
sudo apt update && sudo apt install -y terraform
```

**Check:**

```bash
terraform version
```

## 2. VirtualBox and Vagrant (optional)

Virtual machines on a laptop depend on the processor. The Week 11 lab is written so that you finish **without** a virtual machine. Install these only if your laptop can run them, and only if you want to try `vagrant up`.

- **Windows 10 or 11 and Intel or AMD Linux:** VirtualBox (<https://www.virtualbox.org>) and Vagrant (<https://developer.hashicorp.com/vagrant/install>). VirtualBox can conflict with WSL 2 and Docker Desktop on some Windows laptops. If Docker stops working after you install it, uninstall VirtualBox. **Vagrant must be installed in Windows, not in Ubuntu.**
- **macOS with Intel:** the same two tools with Homebrew: `brew install --cask virtualbox vagrant`.
- **macOS with Apple silicon (M1 to M4):** VirtualBox does not run Intel boxes. Skip this section. The lab has a path for you.
