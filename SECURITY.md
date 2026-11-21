# Security policy

## Supported code

The `main` branch receives security corrections. Model and runtime projects have their own support policies.

## Report a vulnerability

Do not open a public issue for a vulnerability or an exposed credential.

Use GitHub private vulnerability reporting if it is enabled for this repository. If it is not enabled, contact the repository owner through a private channel listed on the GitHub profile.

Include:

- Affected revision
- Affected component
- Reproduction steps
- Impact
- Suggested mitigation
- Whether a credential or private model was exposed

## Credentials

Never commit:

- `.env`
- API keys
- Hugging Face tokens
- Reverse-proxy credentials
- Private model URLs
- Voice-reference files

If a key appears in a log, issue, pull request, or chat, rotate it immediately.

## Network exposure

The default API binds to loopback. If you bind it to a LAN address or `0.0.0.0`, use:

- An API key
- A host firewall
- A trusted reverse proxy for external access
- TLS for traffic outside a trusted host or network

Do not expose the Docker socket through the public gateway.

## Model risk

Model files are third-party content. Before use:

1. Review the license.
2. Pin the revision.
3. Verify checksums when available.
4. Test the runtime in an isolated environment.
5. Treat voice references as sensitive biometric data.
6. Keep generated content controls appropriate to the deployment.
