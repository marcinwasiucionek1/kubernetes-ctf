# GENERAL ASSUMPTIONS
- Challenges in this Capture The Flag are hosted locally on Kind
- For accessing challenges, there is port-forwarding used 
- Secrets are stored using SOPS
- All challenges are related to Kubernetes
- Challenges are separate units and can be deployed, solved and teared down independently

# BRANCHING AND COMMITS
- Use conventional commits
- Use conventional branching

# TOOLING
- Always use `task` commands for cluster and challenge operations — never raw `helm` or `kubectl` for these
- If needed `task` does not exist yet, propose creating it
- Run `task preflight` first if the environment is unknown
- Tasks should run with no issues on Windows, Linux and MacOS

# CHALLENGE CONVENTIONS
- Challenge IDs follow `NN-slug` (e.g. `02-rbac-escape`), the Helm release name strips the numeric prefix (`rbac-escape`)
- Flag secret is always named `<id>-flag`, mounted at `/etc/ctf/flag.txt` inside the container
- Flags are dynamically generated on deployment of each challenge
- Flags follow the pattern `ctf\{[^}]*\}`

# RULES
- Never run `git commit` without explicit approval
- Ask before creating any file not explicitly requested
