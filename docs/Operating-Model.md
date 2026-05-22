# Operating Model — CI/CD and Deployment Governance

This document is the single source of truth for how changes flow from an
assistant-drafted edit to a verified production deployment of
**Kuna's Beauty Salon** (`https://kuna.elbconsultingtech.com` — also
reachable as the GitHub Pages default URL while DNS/TLS is being fixed).

The intent is to move governance from "Copilot/assistant remembers to run
the right thing" to **mandatory, codified workflows enforced by GitHub
branch protection, environments, and scheduled smoke tests**.

This model mirrors the first-wave governance rollout used for
[`LGLenz/bridgeaxis-consulting`](https://github.com/LGLenz/bridgeaxis-consulting/pull/23)
and is intended to be reused across every static GitHub Pages property in
the ELB portfolio.

## 1. Flow at a glance

```
  Copilot / assistant drafts change on a branch
                |
                v
        Open Pull Request to main
                |
                v
   ┌────────────────────────────────────┐
   │  PR Mandatory Checks               │  ← required by branch protection
   │  - install-validation              │
   │  - build-validation                │
   │  - lint                            │
   │  - link-sanity                     │
   │  - secrets-config                  │
   └────────────────────────────────────┘
                |
                v
        Reviewer approves & merges
                |
                v
   ┌────────────────────────────────────┐
   │  Deploy GitHub Pages (Production)  │  ← uses `production` environment
   │  - build artifact                  │     (optional reviewers/wait timer)
   │  - actions/deploy-pages@v5         │     records GitHub deployment status
   │  - enforce HTTPS                   │
   └────────────────────────────────────┘
                |
                v
   ┌────────────────────────────────────┐
   │  Site Health (post-deploy)         │  ← triggered by workflow_run
   │  - DNS source-of-truth diff        │     + scheduled every 6h
   │  - HTTPS / TLS / status / title    │     + manual workflow_dispatch
   │  - pages-default (required)        │
   │  - custom-domain (warn-only)       │
   └────────────────────────────────────┘
```

## 2. Workflow inventory

| Workflow file                          | Trigger                                       | Purpose                                                  |
|----------------------------------------|-----------------------------------------------|----------------------------------------------------------|
| `.github/workflows/pr-checks.yml`      | `pull_request`, `push:main`, `workflow_dispatch` | Mandatory PR checks (jobs listed below).             |
| `.github/workflows/deploy-pages.yml`   | `push:main`, `workflow_dispatch`              | Build + deploy Pages artifact via official actions; records deployment status against the `production` environment. |
| `.github/workflows/site-health.yml`    | `workflow_dispatch`, `schedule` (6h), `workflow_run` (after deploy) | DNS, TLS, HTTP, and title smoke tests of live site. |

## 3. PR Mandatory Checks — required-status-checks list

The following job names from `pr-checks.yml` should be marked **required**
in the `main` branch protection rule:

- `Install / tooling validation`
- `Build / artifact validation`
- `Lint / static validation`
- `Link / site artifact sanity`
- `No-secrets / config sanity`

To configure (Settings → Branches → main):

1. ✅ Require a pull request before merging
2. ✅ Require status checks to pass before merging
3. ✅ Require branches to be up to date before merging
4. Add the job names above to the required-checks list.
5. ✅ Require linear history (recommended).
6. ✅ Require conversation resolution before merging (recommended).

## 4. Production environment

The deploy workflow targets a GitHub **environment** named `production`.
Configure it under **Settings → Environments → production**:

- **Required reviewers**: add the maintainers who should approve a deploy.
- **Wait timer**: optional, e.g. 5 minutes to allow a final cancel.
- **Deployment branches**: restrict to `main`.

When `deploy-pages.yml` runs, GitHub will:

1. Record a deployment with status `in_progress`.
2. Block on the environment's approval rules (if any).
3. Run the deploy.
4. Update the deployment status to `success` or `failure`.

This eliminates the "deployments tab is stale" problem because every
`push:main` and every manual dispatch produces a tracked deployment.

## 5. Post-deploy site health

`site-health.yml` runs:

- automatically after `deploy-pages.yml` completes (via `workflow_run`),
- on a 6-hour cron schedule,
- on demand via `workflow_dispatch`.

What it checks, for each target URL:

1. **DNS** — `dig` returns at least one A/AAAA/CNAME record.
2. **TLS** — `openssl s_client` completes without verification errors.
3. **HTTP** — `curl` returns a 2xx/3xx status within 15s.
4. **Title** — response body contains a `<title>` mentioning "Kuna" or "KUSH".

### Targets

| Label          | URL                                                              | Required?       |
|----------------|------------------------------------------------------------------|-----------------|
| pages-default  | https://lglenz.github.io/kuna-beauty-salon-website/              | no (warn-only)  |
| custom-domain  | https://kuna.elbconsultingtech.com                               | no (warn-only)  |

Both targets are **warn-only** today (2026-05-22) because:

1. DNS for `kuna.elbconsultingtech.com` still resolves to the legacy ELB
   origin (`75.126.104.x`) rather than to GitHub Pages, so TLS does not
   hand-shake and GitHub Pages cannot issue a certificate.
2. GitHub Pages, when a custom domain is configured on a repository,
   301-redirects the default `https://lglenz.github.io/<repo>/` URL to
   the custom domain. With the custom-domain TLS broken, the redirected
   request also fails, so the Pages default URL effectively inherits the
   same outage.

Once the CNAME has been added (see §6) and the certificate has been
issued, flip the `custom-domain` target to `required: "true"` in
`site-health.yml`. The `pages-default` target can either be flipped
back to required (it will work again once redirects succeed) or simply
dropped in favour of the custom domain.

When the scheduled run fails, an issue is opened with label `site-health`.

## 6. DNS source of truth

The parent zone `elbconsultingtech.com` is managed **outside this
repository** (ELB Consulting Tech parent infrastructure). The records
this repo cares about are nevertheless captured in:

- `dns/elbconsultingtech.com.zone` — BIND-style excerpt (human-readable).
- `dns/records.yaml` — machine-readable expectations consumed by
  `scripts/check_dns.py`.

Keep them in sync. The `dns-check` job in `site-health.yml` diffs
`dns/records.yaml` against live DNS and reports drift as a **warning**
(not a failure) because the fix lives outside this repo.

### The fix needed

Add this record in the elbconsultingtech.com zone (single CNAME):

```dns
kuna   IN   CNAME   lglenz.github.io.
```

Then, in this repo's GitHub Settings → Pages, confirm the custom domain is
set to `kuna.elbconsultingtech.com` and tick "Enforce HTTPS" once the
certificate has been provisioned.

## 7. Operating principles

- **Copilot/assistant drafts; humans approve.** The assistant opens a PR;
  PR checks run automatically; a human reviewer merges.
- **Branch protection is the enforcer, not memory.** No reliance on the
  assistant "remembering" to run checks — they run because GitHub
  requires them.
- **Production deploys use environment approvals.** Manual deploys via
  `workflow_dispatch` go through the same approval gate as automatic
  push-to-main deploys.
- **Smoke tests verify reality.** A green deploy that produces a broken
  site fails the post-deploy `site-health` workflow and opens an issue.
- **DNS is code (even when we don't own the zone).** Live DNS for the
  records we care about is diffed against `dns/records.yaml` on every
  scheduled run, and drift is surfaced even though it can't be fixed
  from this repo.
- **No secrets in PR checks.** All required PR checks are read-only and
  run on forks safely.

## 8. Troubleshooting

| Symptom                                          | Likely cause                                                       | Where to look |
|--------------------------------------------------|--------------------------------------------------------------------|---------------|
| Deployments tab is stale                         | A previous Pages workflow failed without recording a deployment.   | `deploy-pages.yml` run log + Settings → Environments → production. |
| `kuna.elbconsultingtech.com` shows cert error    | CNAME not yet added in the elbconsultingtech.com zone, or TLS still being issued. | `site-health.yml` → `http-check` (custom-domain target, warn-only) + `dns-check` job summary. |
| `dns-check` job warns                            | Live DNS drifted from `dns/records.yaml`.                          | Parent DNS provider for elbconsultingtech.com + `scripts/check_dns.py` output in job summary. |
| PR check `No-secrets / config sanity` fails      | A secret-shaped string was committed.                              | Job log lists the file and pattern. |

## 9. Required manual follow-ups (UI-only, not code)

1. **Branch protection on `main`** — add as required status checks:
   - `Install / tooling validation`
   - `Build / artifact validation`
   - `Lint / static validation`
   - `Link / site artifact sanity`
   - `No-secrets / config sanity`
2. **Environment `production`** (Settings → Environments) — required reviewers
   and/or wait timer; restrict deployment branches to `main`.
3. **GitHub Pages custom domain** (Settings → Pages) — confirm the value
   `kuna.elbconsultingtech.com`; do NOT tick "Enforce HTTPS" until the
   certificate has been provisioned.
4. **Parent DNS zone** (`elbconsultingtech.com`) — add the CNAME
   `kuna  IN  CNAME  lglenz.github.io.` and remove any A/AAAA records
   for the `kuna` host that point at the legacy origin.
5. Once steps 3–4 are complete, flip the `custom-domain` target in
   `.github/workflows/site-health.yml` from `required: "false"` to
   `required: "true"`.

## 10. How to make changes safely

```bash
# 1. Start from main.
git switch main && git pull

# 2. Branch.
git switch -c feat/your-change

# 3. Edit. Commit. Push.
git push -u origin feat/your-change

# 4. Open a PR. Mandatory checks run automatically.
# 5. After approval + merge, deploy-pages.yml runs.
# 6. site-health.yml runs post-deploy and on schedule.
```
