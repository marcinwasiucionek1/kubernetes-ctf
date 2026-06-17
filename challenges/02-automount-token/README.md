# 02 — Automount Service Account Token

**Difficulty:** beginner  
**Topic:** command injection, Kubernetes service account token abuse

## Goal

Read the flag stored in a Kubernetes Secret inside the `02-automount-token` namespace.

## Setup

Build and deploy the challenge:

```sh
task ch-02:deploy
```

The application is now available at `http://localhost:8080`.

## Hints

<details>
<summary>Hint 1</summary>
The web application lets you search for country codes by name. Try unusual input — the search is not sanitised.
</details>

<details>
<summary>Hint 2</summary>
Try establishing reverse shell. <code>ncat</code> is available in the container. Once you have a shell inside the container, look at what Kubernetes credentials are available.

Check <code>/var/run/secrets/kubernetes.io/serviceaccount/</code>.
</details>

<details>
<summary>Hint 3</summary>
The service account has permission to list and read Secrets in its namespace.
The flag is stored in a Secret named <code>02-automount-token-flag</code>.
</details>
