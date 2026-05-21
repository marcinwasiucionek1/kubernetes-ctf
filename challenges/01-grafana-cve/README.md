# 01 — Grafana CVE-2021-43798

**Difficulty:** beginner  
**Topic:** unauthenticated path traversal, file disclosure

## Goal

Read the flag from a running Grafana instance without logging in.

## Setup

Deploy the challenge and forward the port:

```sh
task ch:deploy -- 01-grafana-cve
task ch:forward -- 01-grafana-cve
```

Grafana is now available at `http://localhost:8080`.

## Hints

<details>
<summary>Hint 1</summary>
Grafana 8.3.0 has a known CVE that lets unauthenticated users read files from the server.
</details>

<details>
<summary>Hint 2</summary>
The vulnerable endpoint is under <code>/public/plugins/</code>. Think path traversal.
</details>

<details>
<summary>Hint 3</summary>
The flag is at <code>/etc/ctf/flag.txt</code> on the container filesystem.
</details>
