# Week 10 Lab: Bytown Web Service on Kubernetes
**NET2008 DevOps · Algonquin College**

This lab is graded (2% of final grade). You deploy the `bytown-web` images you built in Week 9 to a Kubernetes cluster on **your own laptop**, expose them, configure them, update them and roll back.

**Rules**

- Work in a real terminal: Terminal on macOS, your Linux terminal, or the **Ubuntu (WSL 2) app** on Windows. Docker must be running.
- Do the parts in order. Each part builds on the one before.
- Use the **exact** names, labels and file names given here. The self-check and your instructor look for them.
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

Your number of replicas is `2 + (seed mod 3)`: that is 2, 3 or 4.

```bash
export REPL=$((2 + SEED % 3)) && echo "Replicas: $REPL"  # Compute your replica count and print it.
```

```bash
minikube start --driver=docker --cpus=2 --memory=2048  # Start your cluster (if it is already running, this only checks it).
```

```bash
kubectl get nodes  # The node must be Ready.
```

You need the two images from the Week 9 lab:

```bash
docker images bytown-web  # You must see the tags 1.0 and 1.1. If not, redo Part 2 of the Week 9 lab.
```

```bash
mkdir -p ~/bytown-k8s/k8s ~/bytown-k8s/evidence && cd ~/bytown-k8s && git init -b main  # Create the lab repository with a folder for manifests and a folder for proof.
```

**If you close the terminal**, the variables are lost. Open a new terminal and run both `export` lines again, then `cd ~/bytown-k8s`.

---
## Part 1. Namespace and images (3 points)

```bash
kubectl create namespace bytown  # Create the namespace for this lab.
```

```bash
minikube image load bytown-web:1.0  # Copy your version 1.0 image into the cluster.
```

```bash
minikube image load bytown-web:1.1  # Copy your version 1.1 image into the cluster.
```

```bash
minikube image ls | grep bytown-web | tee evidence/part1-images.txt  # List the images the cluster has and save the list. Both tags must show.
```

---
## Part 2. A Deployment with your replica count (5 points)

Create the manifest. The shell inserts your replica count into the file:

```bash
cat > k8s/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bytown-web
  namespace: bytown
  labels:
    app: bytown-web
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
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 25m
              memory: 32Mi
            limits:
              cpu: 100m
              memory: 64Mi
EOF
```

```bash
grep replicas k8s/deployment.yaml  # Check that your replica count is in the file.
```

```bash
kubectl apply -f k8s/deployment.yaml  # Create the Deployment.
```

```bash
kubectl -n bytown rollout status deployment bytown-web  # Wait until all replicas are ready.
```

```bash
kubectl -n bytown get pods -o wide | tee evidence/part2-pods.txt  # List your pods and save the list. They are all Running.
```

Test self-healing. Delete one pod:

```bash
kubectl -n bytown delete pod $(kubectl -n bytown get pods -o name | head -1)  # Delete one pod of your Deployment.
```

```bash
sleep 15; kubectl -n bytown get pods | tee evidence/part2-healed.txt  # Wait 15 seconds, then list the pods: your replica count is back, all Running, and one pod is new (look at AGE). If one is not Running yet, run the command again.
```

---
## Part 3. A Service (3 points)

```bash
cat > k8s/service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: bytown-web
  namespace: bytown
spec:
  type: ClusterIP
  selector:
    app: bytown-web
  ports:
    - port: 80
      targetPort: 80
EOF
```

```bash
kubectl apply -f k8s/service.yaml  # Create the Service.
```

```bash
kubectl -n bytown get endpoints bytown-web | tee evidence/part3-endpoints.txt  # One address per pod. The number of addresses must equal your replica count.
```

Forward a laptop port to the Service. Your port is `8400 + seed`:

```bash
kubectl -n bytown port-forward svc/bytown-web $((8400 + SEED)):80 > /dev/null &  # Forward your port to the Service, in the background.
```

```bash
sleep 2 && curl -s http://localhost:$((8400 + SEED)) | tee evidence/part3-curl.txt  # Request the page. You must see your seed.
```

```bash
kill %1  # Stop the forward.
```

---
## Part 4. ConfigMap and Secret (4 points)

```bash
kubectl -n bytown create configmap bytown-config --from-literal=SITE=ott-dc1-$SEED  # Create the ConfigMap. The value contains your seed.
```

```bash
kubectl -n bytown create secret generic bytown-secret --from-literal=TOKEN=bytown-$SEED-token  # Create the Secret.
```

Save both as manifests (this is how a team would keep them in Git). **Do not commit the Secret value of a real system; this one is a lab value.**

```bash
kubectl -n bytown get configmap bytown-config -o yaml > k8s/configmap.yaml  # Save the ConfigMap as YAML.
```

```bash
kubectl -n bytown get secret bytown-secret -o yaml > k8s/secret.yaml  # Save the Secret as YAML. Look at it: the value is only base64.
```

Replace the Deployment so that it reads both as environment variables. This is the whole file again, with the `env` block added:

```bash
cat > k8s/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bytown-web
  namespace: bytown
  labels:
    app: bytown-web
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
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
          env:
            - name: SITE
              valueFrom:
                configMapKeyRef:
                  name: bytown-config
                  key: SITE
            - name: TOKEN
              valueFrom:
                secretKeyRef:
                  name: bytown-secret
                  key: TOKEN
          resources:
            requests:
              cpu: 25m
              memory: 32Mi
            limits:
              cpu: 100m
              memory: 64Mi
EOF
```

```bash
kubectl apply -f k8s/deployment.yaml  # Apply the change. The pods are replaced.
```

```bash
kubectl -n bytown rollout status deployment bytown-web  # Wait until the replacement is finished.
```

```bash
kubectl -n bytown exec deploy/bytown-web -- sh -c 'echo $SITE' | tee evidence/part4-site.txt  # Read SITE inside a pod. You must see ott-dc1-<your seed>.
```

---
## Part 5. Rolling update and rollback (3 points)

Update to version 1.1 by editing the **file** (so that Git records it):

```bash
sed -i.bak 's#image: bytown-web:1.0#image: bytown-web:1.1#' k8s/deployment.yaml && rm k8s/deployment.yaml.bak  # Change the image tag in the manifest to 1.1.
```

```bash
grep "image:" k8s/deployment.yaml  # Check: the image is bytown-web:1.1.
```

```bash
kubectl apply -f k8s/deployment.yaml  # Apply the new version.
```

```bash
kubectl -n bytown rollout status deployment bytown-web  # Watch the rolling update finish.
```

Start the forward again (the old forward was bound to a pod that no longer exists) and check the new version:

```bash
kubectl -n bytown port-forward svc/bytown-web $((8400 + SEED)):80 > /dev/null &  # Start the forward again.
```

```bash
sleep 2 && curl -s http://localhost:$((8400 + SEED)) | tee evidence/part5-v11.txt  # The page must show "Version 1.1".
```

```bash
kill %1  # Stop the forward.
```

Now go back to the previous revision with Kubernetes (not by editing the file):

```bash
kubectl -n bytown rollout undo deployment bytown-web  # Roll back to the previous revision (image 1.0).
```

```bash
kubectl -n bytown rollout status deployment bytown-web  # Wait for the rollback.
```

```bash
kubectl -n bytown rollout history deployment bytown-web | tee evidence/part5-history.txt  # Save the revision list.
```

```bash
sed -i.bak 's#image: bytown-web:1.1#image: bytown-web:1.0#' k8s/deployment.yaml && rm k8s/deployment.yaml.bak  # Make the file match the cluster again: the manifest says 1.0.
```

**Run the self-check now** (see "Check your work"), while the cluster still has your objects.

---
## Part 6. Answers (2 points)

Answer in a file named `answers.txt`, one answer per line, in the form `Q1: your answer` (at least 20 characters each):

1. A pod you deleted came back. Who brought it back, and why?
2. Why is a Kubernetes Secret not safe to commit to a public repository, even though its value looks scrambled?
3. During the rolling update users saw no outage. Why?

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

The self-check reads your folder and asks the cluster. It changes nothing. Run it from your lab folder, with the cluster running and your objects still in place:

```bash
python3 ~/net2008-devops/week10/W10_Lab_selfcheck.py --seed "$SEED"  # Check your work against the lab.
```

Fix every `FAIL` line, then run it again.

## Clean up

After the self-check, delete the lab objects and stop the cluster:

```bash
kubectl delete namespace bytown  # Delete everything in the namespace.
```

```bash
minikube stop  # Stop the cluster and free the memory.
```

## Submit

1. Commit everything and push to a **public** GitHub repository named `bytown-k8s` (the same steps as Week 6, Part 4). Create the empty repository on GitHub first, then:

```bash
git add -A && git commit -m "Week 10 lab: kubernetes"  # Save everything.
```

```bash
git remote add origin git@github.com:YOUR-USERNAME/bytown-k8s.git  # Link your empty GitHub repository. Use your own user name.
```

```bash
git push -u origin main  # Upload to GitHub.
```

2. Open the repository in a private (incognito) window. If you can see it, your instructor can.
3. Open **Week 10 Lab Submission** on Brightspace and submit **only the URL** of the repository.
4. Do not push after the deadline.

## Marking (20 points = 2%)

| Part | What | Points |
|---|---|---|
| 1 | Namespace `bytown`, both images loaded | 3 |
| 2 | Deployment `bytown-web` with your replica count, pods running, self-healing shown | 5 |
| 3 | Service with a correct selector, reached on your port | 3 |
| 4 | ConfigMap and Secret used by the Deployment, `SITE` read in a pod | 4 |
| 5 | Rolling update to 1.1 and rollback to 1.0, manifest and cluster agree | 3 |
| 6 | `answers.txt` (read by your instructor) | 2 |

## If something goes wrong

| Problem | What to do |
|---|---|
| `$REPL` is empty and the manifest says `replicas: ` | The variable is lost. Run both `export` lines again and recreate the file. |
| Pods `ErrImagePull` or `ImagePullBackOff` | The image is not in the cluster. Repeat `minikube image load` for that tag, then `kubectl -n bytown rollout restart deployment bytown-web`. |
| `Error from server (NotFound): namespaces "bytown" not found` | Create it: `kubectl create namespace bytown`. |
| `get endpoints` is empty | The Service `selector` does not match the pod labels. They must both be `app: bytown-web`. |
| `curl` says `Connection refused` after the forward | Wait 2 seconds, or the forward died. Start it again (and check nothing else uses the port). |
| `bash: kill: %1: no such job` | The forward is not a job of this terminal. `pkill -f "port-forward"`. |
| The page still shows the old version after the update | The forward is bound to an old pod. Stop it and start it again. |
| Cluster does not respond after sleep | `minikube stop` then `minikube start`. Your objects are kept. |
| Everything is a mess | `kubectl delete namespace bytown`, then restart at Part 1. |
