# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report vulnerabilities by emailing **info@felixbeinssen.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgement:** within 48 hours
- **Initial assessment:** within 5 business days
- **Critical patches:** within 7 days
- **Non-critical patches:** included in the next regular release

### Scope

The following are in scope:

- Backend API (authentication, authorization, injection, SSRF)
- Keycloak configuration and token handling
- Helm chart security (secrets exposure, network policies)
- Docker image supply chain (base images, dependencies)
- Crawler SSRF or unintended data exfiltration

Out of scope:

- Vulnerabilities in upstream dependencies (report directly to the maintainer)
- Denial of service against the staging instance
- Social engineering

## Security Design

Argus follows defense-in-depth principles:

- **Network policies:** Default-deny with explicit allow rules per service
- **Secrets management:** Kubernetes Secrets, never committed to git
- **Authentication:** Keycloak OIDC with PKCE, JWT validation on every request
- **Authorization:** Role-based access control via Keycloak realm roles
- **Container isolation:** Non-root containers where supported, resource limits enforced
