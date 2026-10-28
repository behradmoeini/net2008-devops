# Week 10 Lecture: Container Orchestration with Kubernetes
**NET2008 DevOps · Algonquin College**

Follow this guide from top to bottom. You type every command in a real terminal **on your own laptop** (Terminal on macOS, your Linux terminal, the **Ubuntu (WSL 2) app** on Windows). You need Docker running and `kubectl` and `minikube` installed (see [W10_Setup_Kubernetes.md](W10_Setup_Kubernetes.md)). Run `python3 ../week09/lab/check_tools.py` to check.

## How to follow this guide

- Every grey box is **one command** (or one file you create). Everything after the `#` on the first line is a comment that says what the command does. Copy the whole box, paste it into the terminal, press Enter, then go to the next box.
- **You should see** shows roughly what the terminal prints. Names with random letters (like `hello-7d9f8-x2k4p`) will differ.
- Do the steps in order. All practice work happens in one folder, `~/k8s-practice`.

---
## The big picture: read this first

### The problem

One container on one laptop is easy. A real service needs **ten** copies of a container, spread over several servers, restarted when they crash, updated without downtime, and reachable under one address. Doing that by hand with `docker run` does not scale. **Kubernetes** (K8s) is a system that does it for you. You tell it **what you want** ("three copies of this image, reachable on port 80") and it works continuously to make reality match.

### Declarative: describe the goal, not the steps

| Imperative (Docker) | Declarative (Kubernetes) |
|---|---|
| "Start a container. Start another. One died, start a new one." | "I want 3 copies." Kubernetes starts, counts and replaces by itself. |

This is the most important idea of the week. You write a YAML file with the **desired state**. Kubernetes compares it with the **actual state** and fixes the difference, again and again.

### Eight words to know

| Word | Meaning |
|---|---|
| **Cluster** | All the machines Kubernetes manages. On your laptop it is one small machine. |
| **Node** | One machine in the cluster that runs containers |
| **Pod** | The smallest unit: one or more containers that run together. Usually one. |
| **Deployment** | "Keep N identical pods running, and update them safely" |
| **ReplicaSet** | What a Deployment creates to keep the count right (you rarely touch it) |
| **Service** | A stable name and address in front of a changing set of pods |
| **Namespace** | A folder inside the cluster, to keep projects apart |
| **ConfigMap / Secret** | Settings and sensitive settings, kept outside the image |

### Labels and selectors glue everything

Pods carry **labels** (`app: bytown-web`). A Deployment and a Service find their pods with a **selector** that matches labels. If the labels do not match, the Service points at nothing. Most Kubernetes mistakes in this course are label mistakes.

```text
Deployment (replicas: 3) --creates--> 3 pods (label app=bytown-web)
Service (selector app=bytown-web) --sends traffic to--> those 3 pods
```

### minikube

**minikube** runs a real one-node Kubernetes cluster inside a Docker container on your laptop. `kubectl` is the command-line tool that talks to any cluster.

---
## Step 1. Start your cluster

```bash
minikube start --driver=docker --cpus=2 --memory=2048  # Create and start a one-node cluster that runs inside Docker. The first start downloads about 500 MB and takes a few minutes.
```

```bash
kubectl get nodes  # List the nodes. You see one node named minikube with the status Ready.
```

```bash
kubectl cluster-info  # Show where the cluster's control point (the API server) listens.
```

```bash
mkdir -p ~/k8s-practice && cd ~/k8s-practice  # Create the practice folder and move into it.
```

If `minikube start` fails with a memory message, give Docker Desktop more memory (Settings > Resources) and run it again. If you close the laptop, the cluster stops; run `minikube start` again and everything comes back.

---
## Step 2. Run a pod the quick way

```bash
kubectl run hello --image=nginx:alpine  # Create one pod named hello that runs nginx.
```

```bash
kubectl get pods  # List pods. The status goes ContainerCreating, then Running.
```

```bash
kubectl describe pod hello  # Show everything about the pod. Read the Events list at the bottom: it tells you what happened and what went wrong.
```

```bash
kubectl logs hello  # Show the output of the container.
```

```bash
kubectl exec hello -- nginx -v  # Run one command inside the pod.
```

```bash
kubectl delete pod hello  # Delete the pod. Nobody brings it back: a bare pod is not supervised.
```

A pod you create by hand is not replaced when it dies. You will use Deployments instead.

---
## Step 3. Manifests: write the goal in YAML

A **manifest** is a YAML file that describes an object. Every manifest has four top-level keys: `apiVersion`, `kind`, `metadata` and `spec`.

```bash
cat > pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: hello
  labels:
    app: hello
spec:
  containers:
    - name: web
      image: nginx:alpine
      ports:
        - containerPort: 80
EOF
```

```bash
kubectl apply -f pod.yaml  # Create (or update) what the file describes. apply is the command you use all week.
```

```bash
kubectl get pod hello -o wide  # List the pod with extra columns: its IP and the node it runs on.
```

```bash
kubectl delete -f pod.yaml  # Delete what the file describes.
```

YAML uses **spaces** (never tabs). A dash starts a list item. Indentation shows what belongs to what.

---
## Step 4. Deployments: keep N copies alive

```bash
cat > deploy.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
        - name: web
          image: nginx:alpine
          ports:
            - containerPort: 80
EOF
```

Read it: the Deployment wants 3 replicas. `selector.matchLabels` says which pods it owns. `template` is the pod it creates, with the **same label** as the selector.

```bash
kubectl apply -f deploy.yaml  # Create the Deployment.
```

```bash
kubectl get deployment,replicaset,pods  # Show the three layers: the Deployment, its ReplicaSet and the 3 pods.
```

Now watch self-healing. Copy the name of one pod, then delete it:

```bash
kubectl delete pod $(kubectl get pods -l app=hello -o name | head -1)  # Delete the first pod of the Deployment.
```

```bash
kubectl get pods -l app=hello  # There are 3 pods again. One is new (look at its AGE). Kubernetes saw 2 of 3 and fixed it.
```

```bash
kubectl scale deployment hello --replicas=5  # Ask for 5 copies.
```

```bash
kubectl get pods -l app=hello  # Five pods.
```

`-l app=hello` filters by label. It is the same label the selector uses.

---
## Step 5. Services: one stable address

Pods come and go and change IP addresses. A **Service** gives them one stable name.

```bash
cat > service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: hello
spec:
  type: ClusterIP
  selector:
    app: hello
  ports:
    - port: 80
      targetPort: 80
EOF
```

`port` is the port of the Service. `targetPort` is the port of the container. `selector` picks the pods by label.

```bash
kubectl apply -f service.yaml  # Create the Service.
```

```bash
kubectl get service hello  # Show the Service and its cluster-internal IP.
```

```bash
kubectl get endpoints hello  # Show the pods behind the Service (one IP per pod). If this is empty, your labels do not match.
```

A ClusterIP Service is reachable **inside** the cluster only. To reach it from your laptop, forward a port:

```bash
kubectl port-forward svc/hello 8090:80 &  # Forward port 8090 of your laptop to the Service, in the background (&).
```

```bash
sleep 2 && curl -s http://localhost:8090 | head -4  # Request the page. You should see the nginx welcome page.
```

```bash
kill %1  # Stop the background port-forward.
```

**Important:** `port-forward` connects to **one pod** when it starts. If that pod is deleted (for example during an update), the forward stops working. Stop it and start it again.

---
## Step 6. ConfigMaps and Secrets

Settings belong **outside** the image, so one image runs everywhere.

```bash
kubectl create configmap hello-config --from-literal=SITE=ott-dc1  # Create a ConfigMap with one setting.
```

```bash
kubectl create secret generic hello-secret --from-literal=TOKEN=s3cret-value  # Create a Secret with one value.
```

```bash
kubectl get secret hello-secret -o jsonpath='{.data.TOKEN}'  # Show the stored value. It is only base64, NOT encrypted. Anyone who can read the Secret can decode it.
```

Use both as environment variables in the Deployment. Replace `deploy.yaml`:

```bash
cat > deploy.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
        - name: web
          image: nginx:alpine
          ports:
            - containerPort: 80
          env:
            - name: SITE
              valueFrom:
                configMapKeyRef:
                  name: hello-config
                  key: SITE
            - name: TOKEN
              valueFrom:
                secretKeyRef:
                  name: hello-secret
                  key: TOKEN
EOF
```

```bash
kubectl apply -f deploy.yaml  # Apply the change. A changed pod template makes Kubernetes replace the pods one by one.
```

```bash
kubectl rollout status deployment hello  # Wait until the replacement is finished.
```

```bash
kubectl exec deploy/hello -- sh -c 'echo $SITE'  # Read the variable inside a pod. You see ott-dc1.
```

---
## Step 7. Rolling updates and rollbacks

Change the image version. Kubernetes starts new pods and stops old ones **gradually**, so the service never goes down.

```bash
kubectl set image deployment/hello web=nginx:1.27-alpine  # Change the image of the container named web.
```

```bash
kubectl rollout status deployment hello  # Watch the update finish.
```

```bash
kubectl rollout history deployment hello  # List the revisions of this Deployment.
```

Now break it on purpose with an image that does not exist:

```bash
kubectl set image deployment/hello web=nginx:does-not-exist  # Use an image tag that does not exist.
```

```bash
kubectl get pods -l app=hello  # New pods show ErrImagePull or ImagePullBackOff. The OLD pods keep running: users see no outage.
```

```bash
kubectl rollout undo deployment hello  # Go back to the previous working revision.
```

```bash
kubectl rollout status deployment hello  # Wait until the rollback is finished.
```

---
## Step 8. Your own images

A cluster cannot see the images on your laptop. Copy an image into minikube first:

```bash
minikube image load nginx:alpine  # Copy a local image into the cluster. In the lab you do this with your own bytown-web images from Week 9.
```

In a manifest, `imagePullPolicy: IfNotPresent` tells Kubernetes to use a local copy when it exists and not to download it.

---
## Step 9. Namespaces

```bash
kubectl get namespaces  # List the namespaces. default is where you worked so far.
```

```bash
kubectl create namespace demo  # Create a namespace.
```

```bash
kubectl get pods -n demo  # List pods in the namespace demo. -n selects it. It is empty.
```

Every command without `-n` uses `default`. In the lab you use `-n bytown` everywhere.

---
## Step 10. Clean up

```bash
kubectl delete -f service.yaml -f deploy.yaml  # Delete the Service and the Deployment.
```

```bash
kubectl delete configmap hello-config && kubectl delete secret hello-secret && kubectl delete namespace demo  # Delete the rest.
```

```bash
minikube stop  # Stop the cluster and free the memory. minikube start brings it back.
```

## Cheat sheet

| Command | What it does |
|---|---|
| `kubectl get pods\|deploy\|svc -n NS` | List objects |
| `kubectl describe pod NAME` | Details and **Events** (read these first when something fails) |
| `kubectl logs NAME` | Container output |
| `kubectl exec -it NAME -- sh` | Shell inside a pod |
| `kubectl apply -f FILE` | Create or update from a file |
| `kubectl delete -f FILE` | Delete what the file describes |
| `kubectl rollout status\|history\|undo deployment NAME` | Follow, list, reverse an update |
| `kubectl get ... -o yaml` | Print the live object as YAML |

## If something goes wrong

| Message or symptom | Cause and fix |
|---|---|
| `The connection to the server localhost:8080 was refused` | No cluster is running. `minikube start`. |
| `minikube start` fails with `Exiting due to RSRC_INSUFFICIENT_...` | Docker Desktop has too little memory or CPU. Raise it and retry. |
| Pod stays `Pending` | Not enough resources, or an unmet request. `kubectl describe pod NAME`, read Events. |
| `ErrImagePull` or `ImagePullBackOff` | The image name or tag is wrong, or a local image was not loaded with `minikube image load`. |
| `CrashLoopBackOff` | The container starts and exits. `kubectl logs NAME` shows why. |
| Service answers nothing, `get endpoints` is empty | The Service `selector` does not match the pod labels. Compare them. |
| `error: error parsing ...: yaml: line N` | Indentation or a tab. Use spaces. |
| `port-forward` stops answering | The pod it was bound to is gone. Stop it and start it again. |
| `Unable to connect to the server: ... i/o timeout` after a laptop sleep | `minikube stop` then `minikube start`. |

## Summary

- Kubernetes keeps **actual** state equal to **desired** state. You write YAML and run `kubectl apply -f`.
- A Deployment keeps N pods alive and updates them gradually. A Service gives the pods one stable address. Labels and selectors connect them.
- ConfigMaps and Secrets keep settings out of the image. A Secret is encoded, not encrypted.
- Rolling updates keep the service up. A bad update leaves the old pods running, and `rollout undo` reverses it.

**Next:** the Week 10 lab (graded) deploys your Week 9 images with your own seed.
