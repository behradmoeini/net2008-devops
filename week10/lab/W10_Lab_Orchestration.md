# Week 10 Lab: Bytown Web Service on a Cluster
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). It is the hands-on companion to the Week 10 lecture. You run the `bytown-web` images from the Week 9 lab on two orchestrators: first as a Docker Swarm stack, then as a Kubernetes Deployment on a K3s cluster. You watch them heal themselves, put a Service in front, and do a rolling update and a rollback. Everything runs on **your own laptop**.

**Rules**

- Work in a terminal: **PowerShell** on Windows, **Terminal** on macOS or Linux. Docker Desktop must be running, and `k3d` and `kubectl` must be installed (see [Week 10 lecture: How to install k3d and kubectl](../W10_Lecture_Orchestration.md#how-to-install-k3d-and-kubectl)).
- **Which box to use:** as in the lecture, where a command differs by system you get a **Windows (PowerShell)** box, open, and a **macOS / Linux (Terminal)** box, collapsed. Every other box works on every system.
- Do the parts in order. Each part builds on the one before.
- Use the **exact** names, tags and file names given here. The self-check and your instructor look for them.
- Every command is one grey box. Run it, read the output, then go on. Do not copy-paste the whole lab at once.
- If you get stuck, use the lecture and the "If something goes wrong" table at the end. Search the error message. Do not ask someone to type the commands for you.
- **Late policy:** submissions received after the deadline receive a grade of 0.

---
## Part 0. Personalize and set up

Your numbers come from your student ID, so your ports and your replica count are different from everyone else's. **Seed** = the sum of the last four digits of your student ID. For example, ID `040112348` gives `2+3+4+8 = 17`.

Replace `17` with **your** seed (a number from 1 to 36), then run:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
export SEED=17  # Remember your seed in a shell variable. Replace 17 with your own number.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
$SEED = 17  # Remember your seed in a variable. Replace 17 with your own number.
```

</details>

Compute your other numbers from the seed. Your replica count is `2 + (seed mod 3)`, so 2, 3 or 4. Your Swarm port is `8500 + seed` and your Kubernetes port is `8600 + seed`:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
export REPL=$((2 + SEED % 3)) SWARM_PORT=$((8500 + SEED)) K8S_PORT=$((8600 + SEED))
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
$REPL = 2 + $SEED % 3; $SWARM_PORT = 8500 + $SEED; $K8S_PORT = 8600 + $SEED
```

</details>

```bash
echo "Seed $SEED, replicas $REPL, Swarm port $SWARM_PORT, Kubernetes port $K8S_PORT"  # Print your numbers. Write them down.
```

```bash
docker images bytown-web  # You must see the tags 1.0 and 1.1 from the Week 9 lab. If not, redo Part 2 of the Week 9 lab.
```

```bash
k3d cluster list  # If the cluster demo from the lecture is still listed, delete it with: k3d cluster delete demo
```

Create the lab folder, with one folder for the proof of your work, one for the Swarm file and one for the Kubernetes files:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
mkdir -p ~/bytown-cluster/evidence ~/bytown-cluster/swarm ~/bytown-cluster/k8s && cd ~/bytown-cluster
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
New-Item -ItemType Directory -Force ~/bytown-cluster/evidence, ~/bytown-cluster/swarm, ~/bytown-cluster/k8s | Out-Null
Set-Location ~/bytown-cluster
```

</details>

```bash
git init -b main  # Make the lab folder a Git repository, as in Week 6.
```

**If you close the terminal**, the variables are lost. Open a new terminal, run the two variable boxes again, then `cd ~/bytown-cluster`.

---
## Part 1. Docker Swarm (25 points)

You run version 1.0 of your image as a Swarm stack, with your replica count, on your Swarm port.

```bash
docker swarm init  # Turn on swarm mode. If it says this node is already part of a swarm, go on.
```

Create the stack file. The terminal fills in your port and your replica count:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > swarm/stack.yaml <<EOF
services:
  web:
    image: bytown-web:1.0
    ports:
      - "${SWARM_PORT}:80"
    deploy:
      replicas: $REPL
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@"
services:
  web:
    image: bytown-web:1.0
    ports:
      - "${SWARM_PORT}:80"
    deploy:
      replicas: $REPL
"@ | Set-Content swarm/stack.yaml -Encoding ascii
```

</details>

```bash
cat swarm/stack.yaml  # Check the file: your Swarm port and your replica count must be in it.
```

```bash
docker stack deploy -c swarm/stack.yaml bytown  # Start the stack named bytown.
```

Docker may warn that the image `could not be accessed on a registry`. On a one-node swarm that is harmless: the image is already on this node.

```bash
docker stack services bytown | tee evidence/part1-services.txt  # Show the service and save the list. Run it again until REPLICAS shows your count, for example 3/3.
```

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$SWARM_PORT | tee evidence/part1-curl.txt  # Ask for the page and save it. You must see your seed.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s http://localhost:$SWARM_PORT | tee evidence/part1-curl.txt  # Ask for the page and save it. You must see your seed.
```

</details>

Now test self-healing. Delete one replica as if it crashed:

```bash
docker ps --filter name=bytown_web  # List the containers of the service. Copy one name from the NAMES column.
```

```bash
docker rm -f NAME  # Replace NAME with the name you copied.
```

```bash
sleep 10; docker service ps bytown_web | tee evidence/part1-healed.txt  # Wait 10 seconds, then list the tasks and save the list.
```

**You should see** your replica count of `Running` tasks again, and one line marked `\_`: the task that Swarm replaced. If fewer tasks run, run the last command again.

Delete the stack and turn swarm mode off. You do not need it for the rest of the lab:

```bash
docker stack rm bytown  # Delete the stack.
```

```bash
docker swarm leave --force  # Turn swarm mode off.
```

---
## Part 2. A K3s cluster (10 points)

The cluster is named `bytown`: one server and two agents. Your Kubernetes port on your laptop goes to port 30080 of the first agent:

```bash
k3d cluster create bytown --agents 2 -p "${K8S_PORT}:30080@agent:0"  # Create the cluster. The first run downloads the K3s image.
```

```bash
kubectl get nodes | tee evidence/part2-nodes.txt  # Three nodes, all Ready, and save the list. If one is NotReady, wait 20 seconds and run it again.
```

The cluster cannot see the images on your laptop: each node has its own image store. This step was not presented in class; read [Run your own image](../W10_Lecture_Orchestration.md#run-your-own-image) (REFERENCE) in the lecture first. Copy both of your images into the cluster:

```bash
k3d image import bytown-web:1.0 bytown-web:1.1 -c bytown  # Copy both images into every node of the cluster bytown.
```

---
## Part 3. A Deployment (25 points)

Create the manifest. The terminal fills in your replica count:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > k8s/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bytown-web
spec:
  replicas: $REPL
  selector:
    matchLabels:
      app: bytown-web
  template:
    metadata:
      labels:
        app: bytown-web
    spec:
      containers:
        - name: web
          image: bytown-web:1.0
          ports:
            - containerPort: 80
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bytown-web
spec:
  replicas: $REPL
  selector:
    matchLabels:
      app: bytown-web
  template:
    metadata:
      labels:
        app: bytown-web
    spec:
      containers:
        - name: web
          image: bytown-web:1.0
          ports:
            - containerPort: 80
"@ | Set-Content k8s/deployment.yaml -Encoding ascii
```

</details>

```bash
cat k8s/deployment.yaml  # Check that your replica count is in the file.
```

```bash
kubectl apply -f k8s/deployment.yaml  # Create the Deployment.
```

```bash
kubectl rollout status deployment/bytown-web  # Wait until all replicas are ready.
```

```bash
kubectl get pods -o wide | tee evidence/part3-pods.txt  # List your pods and the nodes they run on, and save the list. They are all Running.
```

Test self-healing. Delete one pod:

```bash
kubectl delete pod POD_NAME  # Replace POD_NAME with the name of one of your pods.
```

```bash
sleep 10; kubectl get pods | tee evidence/part3-healed.txt  # Wait 10 seconds, then list the pods and save the list.
```

**You should see** your replica count of pods, all `Running`, and one of them younger than the others (look at `AGE`). If one is not `Running` yet, run the last command again.

---
## Part 4. A Service (15 points)

The Service sends the traffic from port 30080 of every node to your pods. A request takes this path, as in the Step 2 figure of the lecture ([Services](../W10_Lecture_Orchestration.md#services-one-stable-address)): your Kubernetes port on your laptop, then port 30080 of `agent-0` (k3d published it in Part 2), then the Service on port 80, then port 80 of one of your containers.

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > k8s/service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: bytown-web
spec:
  type: NodePort
  selector:
    app: bytown-web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
apiVersion: v1
kind: Service
metadata:
  name: bytown-web
spec:
  type: NodePort
  selector:
    app: bytown-web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
'@ | Set-Content k8s/service.yaml -Encoding ascii
```

</details>

```bash
kubectl apply -f k8s/service.yaml  # Create the Service.
```

```bash
kubectl describe service bytown-web  # Endpoints must list one address per pod: as many as your replica count.
```

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$K8S_PORT | tee evidence/part4-curl.txt  # Ask for the page through the Service and save it. You must see your seed.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s http://localhost:$K8S_PORT | tee evidence/part4-curl.txt  # Ask for the page through the Service and save it. You must see your seed.
```

</details>

You can also open `http://localhost:` followed by your Kubernetes port in your browser.

---
## Part 5. Rolling update and rollback (15 points)

Rolling updates were not presented in class. Read [Rolling updates and rollbacks](../W10_Lecture_Orchestration.md#rolling-updates-and-rollbacks) (REFERENCE) in the lecture first.

Update to version 1.1 by changing the **file**, so that Git records the change:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
sed -i.bak 's/bytown-web:1.0/bytown-web:1.1/' k8s/deployment.yaml && rm k8s/deployment.yaml.bak  # Change the image tag in the manifest to 1.1.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
(Get-Content k8s/deployment.yaml) -replace 'bytown-web:1.0', 'bytown-web:1.1' | Set-Content k8s/deployment.yaml -Encoding ascii  # Change the image tag in the manifest to 1.1.
```

</details>

```bash
cat k8s/deployment.yaml  # Check: the image is now bytown-web:1.1.
```

```bash
kubectl apply -f k8s/deployment.yaml  # Apply the new version.
```

```bash
kubectl rollout status deployment/bytown-web  # Watch the rolling update finish.
```

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$K8S_PORT | tee evidence/part5-v11.txt  # The page must show "Version 1.1". If not yet, wait 5 seconds and run it again.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s http://localhost:$K8S_PORT | tee evidence/part5-v11.txt  # The page must show "Version 1.1". If not yet, wait 5 seconds and run it again.
```

</details>

Now roll back to the previous revision with Kubernetes:

```bash
kubectl rollout undo deployment/bytown-web  # Go back to the previous revision (image 1.0).
```

```bash
kubectl rollout status deployment/bytown-web  # Wait for the rollback to finish.
```

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
curl -s http://localhost:$K8S_PORT | tee evidence/part5-undo.txt  # The page shows your seed again, without "Version 1.1".
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
curl.exe -s http://localhost:$K8S_PORT | tee evidence/part5-undo.txt  # The page shows your seed again, without "Version 1.1".
```

</details>

```bash
kubectl rollout history deployment/bytown-web  # List the revisions of your Deployment.
```

**Run the self-check now** (see "Check your work" below), while the cluster still runs.

---
## Part 6. Answers (10 points)

Answer these three questions in your own words in a file named `answers.txt`, one answer per line, in the form `Q1: your answer`:

1. In Part 1 and Part 3 you deleted a running copy, and a new one appeared. Who started it, and why?
2. Give one reason to choose Docker Swarm, and one reason to choose K3s instead of a full Kubernetes installation.
3. During the rolling update in Part 5, the page never went down. Why?

Create the file with placeholders:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
cat > answers.txt <<'EOF'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
EOF
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
@'
Q1: replace this with your answer
Q2: replace this with your answer
Q3: replace this with your answer
'@ | Set-Content answers.txt -Encoding ascii
```

</details>

Open `answers.txt` in any editor (for example `notepad answers.txt` on Windows or `nano answers.txt` on macOS and Linux) and replace each `replace this with your answer`. Each answer needs at least 20 characters.

---
## Check your work

The self-check reads your lab folder and asks your cluster for its objects. It changes nothing. Run it from your lab folder, with the cluster `bytown` still running. Use the path of your copy of the course repository:

<details>
<summary>macOS / Linux (Terminal)</summary>

```bash
python3 ~/net2008-devops/week10/lab/W10_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

</details>

<details open>
<summary>Windows (PowerShell)</summary>

```powershell
python $HOME/net2008-devops/week10/lab/W10_Lab_selfcheck.py --seed $SEED  # Check your work against the lab.
```

</details>

Fix every `FAIL` line, then run it again. It checks that things exist and have the right shape. Your instructor also reads the files in your repository and `answers.txt`.

## Clean up

After the self-check, delete the cluster and free the memory:

```bash
k3d cluster delete bytown  # Delete the cluster and everything in it.
```

## Submit

1. Commit everything and push to a **public** GitHub repository named `bytown-cluster` (the same steps as Week 6, Part 4). First create the empty repository on GitHub, then:

```bash
git add -A  # Stage everything in the lab folder.
```

```bash
git commit -m "Week 10 lab: orchestration"  # Save everything in one commit (add more commits if you prefer).
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-cluster.git  # Link your empty GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 10 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline. Your instructor looks at the history.

## Marking (100 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Swarm stack with your replica count and port, page served, self-healing shown | 25 |
| 2 | K3s cluster `bytown` with three `Ready` nodes | 10 |
| 3 | Deployment `bytown-web` with your replica count, pods running, self-healing shown | 25 |
| 4 | NodePort Service with a correct selector, page reached on your port | 15 |
| 5 | Rolling update to 1.1 and rollback to 1.0 | 15 |
| 6 | `answers.txt` (read by your instructor) | 10 |
| | **Total** | **100** |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$SEED` prints nothing, or a file says `replicas:` with no number | The variables are lost. Run the two variable boxes of Part 0 again, then repeat the failing step. |
| `docker swarm init` says `could not choose an IP address to advertise` | Run `docker swarm init --advertise-addr 127.0.0.1` instead. |
| `docker stack services` stays at `0/` your count | Run `docker service ps bytown_web --no-trunc` and read the `ERROR` column. Usually the image name is wrong or the Week 9 image is missing. |
| `port is already allocated` | Another container or cluster uses the port. `docker ps`, then `docker rm -f NAME`, or `k3d cluster delete demo`. |
| `k3d cluster create` says the cluster `bytown` already exists | Delete it with `k3d cluster delete bytown`, then start again at Part 2. |
| Pods show `ErrImagePull` or `ImagePullBackOff` | The images are not in the cluster. Run the `k3d image import` command of Part 2 again, then `kubectl rollout restart deployment/bytown-web`. |
| `Endpoints` is empty in `kubectl describe service` | The Service selector does not match the pod labels. Both must be `app: bytown-web`. |
| `curl` says `Connection refused` or prints nothing on your Kubernetes port | Check `kubectl get services` shows `80:30080/TCP`. If you created the cluster without the `-p` part, delete it and start again at Part 2. |
| The page still shows the old version after the update | Wait 5 seconds and run the `curl` command again. |
| `python` or `python3` is not found | On Windows try `py` instead of `python`. On macOS and Linux use `python3`. |
| `kubectl` talks to the wrong cluster | Run `kubectl config use-context k3d-bytown`. |
| Everything is a mess | `k3d cluster delete bytown`, then start again at Part 2. For Part 1: `docker stack rm bytown`, `docker swarm leave --force`, then start again at Part 1. |
