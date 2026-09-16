# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately.
Do not open a public GitHub issue.

## API Key Handling

This tool requires an Ark / Volcengine API key to generate images.
The key is read exclusively from the `ARK_API_KEY` environment variable.
It is never written to source code, manifests, logs, test fixtures, or git.

If you accidentally commit a key:
1. Revoke it immediately in the Volcengine console.
2. Rotate it.
3. Do not rely on `git rm` alone — history still contains the secret.

## Private Images

User cat photos and generated stickers are stored in a workspace directory
outside the git repository by design. They are never uploaded to GitHub.
