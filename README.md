# Kubernetes Security CTF
Hands-on Kubernetes security labs - deploy a vulnerable workload, find the exploit and capture the flag!

Learn how real-world Kubernetes misconfigurations and CVEs are exploited, one self-contained challenge at a time. Runs entirely on your laptop.

## Purpose 
This is a set of challenges meant for learning Kubernetes security. It is meant to run locally and be completed in a self-paced way for everyone to learn about common security pitfalls.

Each challenge is a Helm chart in `challenges/<NN-name>/` that deploys a vulnerable workload with a flag to be captured. Depending on the challenge, the flag may be stored in a Kubernetes Secret, a file inside a container, or revealed only after executing a specific command. The exact flag location is described in the challenge documentation.

## Prerequisites

The following tools must be installed and available on your `PATH`:

| Tool | Purpose |
| --- | --- |
| [Docker](https://docs.docker.com/get-docker/) | Container runtime for Kind |
| [kind](https://kind.sigs.k8s.io/) | Local Kubernetes cluster |
| [kubectl](https://kubernetes.io/docs/tasks/tools/) | Kubernetes CLI |
| [helm](https://helm.sh/docs/intro/install/) | Deploy challenge charts |
| [task](https://taskfile.dev/installation/) | Run repo tasks |
| [ncat](https://nmap.org/ncat/) | Establish reverse shell |

Run `task preflight` to verify all tools are present before proceeding.

## Quickstart
Entire setup can be done using `task`. `task` is [go-task](https://taskfile.dev/). See [`Taskfile.yml`](Taskfile.yml) for the full list of commands.

```sh
task preflight       # check Docker, kind, kubectl, helm, sops are installed
task bootstrap       # install metrics-server
task ch:deploy -- 01-grafana-cve # deploy first challenge
# … play the challenge, capture the flag …
task ch:teardown -- 01-grafana-cve # teardown first challenge
```

## Layout

```
.claude/      # Claude Code configuration
challenges/   # One Helm chart per challenge
infra/        # Shared Kubernetes services (metrics-server)
```

## Challenges

| id | topic | difficulty |
| --- | --- | --- |
| [`01-grafana-cve`](challenges/01-grafana-cve/README.md) | unauthenticated path traversal, file disclosure | beginner |
| [`02-automount-token`](challenges/02-automount-token/README.md) | command injection, Kubernetes service account token abuse | beginner |
| [`03-image-tag`](challenges/03-image-tag/README.md) | supply chain attack, mutable image tags, container registry security | beginner |

## Resources
List of resources used during work on this repository:
1. [Hacking Kubernetes](https://www.oreilly.com/library/view/hacking-kubernetes/9781492081722/) by Andrew Martin and Michael Hausenblas
2. [Container Security](https://www.oreilly.com/library/view/container-security/9781492056690/) by Liz Rice
3. [Kubernetes OWASP Top Ten](https://owasp.org/www-project-kubernetes-top-ten/)

## License
See [LICENSE](LICENSE)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
