# Security Policy

## Supported Versions

| Version | Supported      |
| ------- | -------------- |
| 0.9.3   | ✅ Active      |
| <0.9.3  | ⚠️ Best effort |

## Reporting a Vulnerability

Please report security issues privately to: **security@waycore.com** or open a GitHub Security Advisory.

Include (when possible):

- Affected version / commit hash
- Reproduction steps / proof of concept
- Expected vs actual behavior
- Impact assessment (confidentiality / integrity / availability)

We target initial response within **5 business days**.

## Disclosure Process

1. Triage & reproduce
2. Assign CVSS qualitative severity
3. Prepare fix & regression tests
4. Coordinate release (security patch notes in CHANGELOG)
5. Public disclosure once fix is available

## Non-Qualifying Issues

- Out-of-scope dependencies with available upstream patches
- Denial of service via unrealistic resource constraints
- Social engineering outside project assets

## Security Hardening Features (0.9.3)

- Policy engine (`.sona-policy.json`) with deny patterns
- Circuit breaker for provider resilience
- Feature flags default OFF (principle of safest baseline)
- Performance logs disabled by default (reduce data surface)
- Deterministic AI planning outputs (no prompt injection risk at stub layer)

## Best Practices for Deployers

- Keep `SONA_POLICY_PATH` under version control with code review
- Enable one infrastructure feature at a time (observe metrics)
- Rotate logs in `SONA_PERF_DIR` and restrict permissions
- Avoid embedding secrets in Sona source files
- Run CI tests before enabling caching or batching in production

## Contact

Questions: security@waycore.com

Thank you for helping keep Sona secure.
