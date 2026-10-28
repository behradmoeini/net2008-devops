# Week 10 Setup: Kubernetes Tools
**NET2008 DevOps · Algonquin College**

You do this setup **once**, before the Week 10 lecture. It assumes you finished the [Week 9 setup](../week09/lab/W09_Setup_Your_Laptop.md): a working terminal (Ubuntu on WSL 2 for Windows) and Docker running. Give Docker Desktop **4 GB** of memory (6 GB on a 16 GB laptop) in Settings > Resources, because minikube runs inside Docker.

## Install kubectl and minikube

**macOS.**

```bash
brew install kubectl minikube
```

**Windows (Ubuntu terminal) and Linux.**

```bash
ARCH=$(dpkg --print-architecture)  # amd64 on most laptops, arm64 on ARM laptops.
```

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/$ARCH/kubectl"  # Download kubectl.
```

```bash
sudo install kubectl /usr/local/bin/kubectl  # Put it on your PATH.
```

```bash
curl -LO "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-$ARCH"  # Download minikube.
```

```bash
sudo install "minikube-linux-$ARCH" /usr/local/bin/minikube  # Put it on your PATH.
```

**Check:**

```bash
kubectl version --client
```

```bash
minikube version
```

## Start a cluster

```bash
minikube start --driver=docker --cpus=2 --memory=2048  # Create a one-node cluster inside Docker. The first start downloads images and takes a few minutes.
```

```bash
kubectl get nodes  # You must see one node with STATUS Ready.
```
