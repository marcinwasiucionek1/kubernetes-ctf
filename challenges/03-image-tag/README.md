# 03 — Image Tag

**Difficulty:** beginner  
**Topic:** supply chain attack, mutable image tags, container registry security

## Goal

Replace the running container with your own image to capture the flag mounted at `/etc/ctf/flag`.

## Setup

Deploy the challenge:

```sh
task ch-03:deploy
```

The application is now available at `http://localhost:8080`.

## Hints

<details>
<summary>Hint 1</summary>
Read the web page carefully — it tells you exactly what access you have and how to use it.
</details>

<details>
<summary>Hint 2</summary>
The running pod uses a mutable image tag. You have access to the cluster node and can load new images into it. Loading a different image under the same tag means the next pod restart will run your image.
</details>

<details>
<summary>Hint 3</summary>
Build a simple nginx image whose entrypoint reads <code>/etc/ctf/flag</code> and writes it into the HTML served at port 80. Tag it as <code>image-tag:1.0.0</code> and load it into the cluster with <code>kind load docker-image</code>. The deployment restarts automatically every minute.
</details>
