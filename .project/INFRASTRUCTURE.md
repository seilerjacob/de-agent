# Infrastructure Conventions

All infrastructure is code. Everything needed to run or rebuild the system — locally or in production — is committed to the repository and executable without manual steps.

---

## The Local Stack

Every project must be runnable locally from a single command after cloning:

```bash
docker compose up
```

This command brings up all services the application depends on: databases, caches, queues, mock external services, any sidecar processes. The application itself may be run via compose or separately (e.g., `npm run dev`, `go run .`) depending on the development workflow, but all *dependencies* are always containerized.

**The single-command test:** delete every local artifact (containers, volumes, built images) and run `docker compose up` from a clean clone. The stack should reach a ready state without any additional steps beyond credential configuration.

---

## docker-compose.yml Conventions

- Every service needed for local development is defined here
- Use named volumes for stateful data (databases, object storage); do not use bind mounts for data that should persist across container restarts
- Define a `healthcheck` for any service that other services depend on; use `depends_on: condition: service_healthy` to enforce startup order
- Expose ports explicitly and document them in a comment or in the README
- Use a `.env` file for local configuration; check in `.env.example` with safe defaults and document which values require real credentials

```yaml
# .env.example
POSTGRES_PASSWORD=localdev
REDIS_URL=redis://localhost:6379
EXTERNAL_API_KEY=      # requires a real key — see internal docs
```

---

## Containerization

- Application services are built from Dockerfiles committed to the repository
- Dockerfiles use multi-stage builds where appropriate to keep production images minimal
- Do not pull images from personal or team registries for core application services — build from source so the build is always reproducible
- Pin base image versions (e.g., `node:22.3-alpine`, not `node:latest`)
- The production image and the local development image may differ, but the Dockerfile for both lives in the repo

---

## Production Infrastructure

Production infrastructure is defined in IaC (Terraform, CDK, Pulumi, or equivalent). The IaC code lives in a committed directory (e.g., `infra/` or `deploy/`).

**Requirements:**
- `terraform plan` (or equivalent) must produce a readable diff before any apply
- Destroying and recreating the full environment from scratch must be documented and tested at least once
- Secrets are managed through a secrets service (e.g., AWS Secrets Manager, Vault) — never hardcoded in IaC or committed to the repo
- Environment-specific configuration (dev, staging, prod) is expressed as variable overrides, not separate IaC files

---

## Bootstrap Script

Any one-time setup steps (tool installation, registry authentication, initial secret population) that cannot be expressed in `docker compose up` or IaC must be captured in a bootstrap script:

```
scripts/bootstrap.sh   # or Makefile target: make bootstrap
```

The bootstrap script is idempotent — running it multiple times on a machine that is already set up does nothing harmful.

---

## Rebuild Sequence

The authoritative rebuild sequence must be documented in the project README:

```bash
# Destroy all local state
docker compose down -v

# Rebuild from scratch
docker compose build --no-cache
docker compose up
```

For production: the equivalent sequence using IaC should be documented and tested at least once per major release cycle.

---

## What Belongs Here vs. README

This file documents conventions. Project-specific commands, port numbers, and service names belong in the project README. The README is the human-readable guide; the `docker-compose.yml` and IaC are the authoritative source of truth.
