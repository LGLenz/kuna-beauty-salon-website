# Kuna's Beauty Salon — Digital Branding & Website Project

> Partnership project managed by **Elias Lenz MBA Beratung** under **ELB Consulting Tech**

## Overview

This repository contains all digital branding and website development assets for **Kuna's Beauty Salon** (also known as **KUSH Beauty Shop** / **Kushy's Beauty Haven**), owned and operated by **Inviolata Kuna Taaban**.

The project is part of the broader partnership framework under the **Mafrick Munene & Advocates** collaboration network, aiming to empower local entrepreneurs with professional digital presence.

## Partner

- **Owner:** Inviolata Kuna Taaban (rep. Jacob Njiru)
- **Business Name:** Kuna's Beauty Salon / KUSH Beauty Shop
- **Focus:** Beauty & wellness center — haircare, skincare, nail services, spa
- **Partnership Contact:** ELB Consulting Tech (elenz@elbconsultingtech.com)

## Project Scope

- [ ] Brand identity design (logo, color palette, typography)
- [ ] Website development (multi-page static or CMS-based)
- [ ] Service menu and pricing pages
- [ ] Online booking integration
- [ ] Social media profile setup
- [ ] Google Business Profile
- [ ] Funding Application 2026 — Digital Branding Component

## Drive Artifacts

| Document | Type | Description |
|---|---|---|
| KUSH BEAUTY SHOP.docx | Word Doc | Business vision, services & investment requirements |
| KUSH BEAUTY SHOP.pdf | PDF | Formal business proposal for Kushy's Beauty Haven |
| Funding_Application_Submission_Package_2026 | Google Doc | Funding application including digital branding plan |
| Kuna_Taaban_Certificates.pdf | PDF | Professional training & industry certifications |
| Kuna_Taaban_Certificates 2.pdf | PDF | Additional certifications & hospitality training records |
| Kuna_Taaban_Letters of Recommendation.pdf | PDF | Employment contracts & letters of recommendation |

## Status

| Milestone | Status |
|---|---|
| Partnership Agreement | Accepted |
| Drive Documentation | Complete |
| GitHub Repository | Initialized |
| Website Design | Pending |
| Website Development | Pending |
| Go-Live | Pending |

## Related Projects

- [mafrick-munene-advocates-website](https://github.com/LGLenz/mafrick-munene-advocates-website) — Legal & NGO partner website
- [ELB Consulting Tech](https://elbconsultingtech.com) — Parent consulting entity

## CI / CD and Deployment Governance

Changes flow through codified GitHub Actions workflows enforced by branch
protection and the `production` environment. The full design lives in
[`docs/Operating-Model.md`](docs/Operating-Model.md).

| Workflow                                  | Trigger                                                   | Purpose |
|-------------------------------------------|-----------------------------------------------------------|---------|
| `.github/workflows/pr-checks.yml`         | `pull_request`, `push:main`, `workflow_dispatch`          | Mandatory PR checks: layout, build, lint, link sanity, secrets. |
| `.github/workflows/deploy-pages.yml`      | `push:main`, `workflow_dispatch`                          | Build & deploy via official `actions/deploy-pages@v5`; records a deployment status against the `production` environment. |
| `.github/workflows/site-health.yml`       | `workflow_run` (after deploy), schedule (6h), `workflow_dispatch` | DNS / TLS / HTTP / title smoke tests of the live site. |

### Live site targets

| Label          | URL                                                              | Status                  |
|----------------|------------------------------------------------------------------|-------------------------|
| pages-default  | https://lglenz.github.io/kuna-beauty-salon-website/              | warn-only (DNS/TLS WIP) |
| custom-domain  | https://kushysbeautyhaven.com                               | warn-only (DNS/TLS WIP) |

The custom domain is warn-only until a `kuna  CNAME  lglenz.github.io.`
record is added in the parent `elbconsultingtech.com` zone — see
[`dns/records.yaml`](dns/records.yaml) and §6 of the Operating Model.

## Project Structure

```
.
├── CNAME                              # Custom domain: kushysbeautyhaven.com
├── README.md
├── index.html                         # Single-page marketing site
├── .github/workflows/                 # PR checks, Pages deploy, site health
├── dns/
│   ├── records.yaml                   # Machine-readable DNS source of truth
│   └── elbconsultingtech.com.zone     # BIND-style excerpt (kuna subdomain)
├── docs/
│   └── Operating-Model.md             # CI/CD and deployment governance
└── scripts/
    ├── check_dns.py                   # Diff dns/records.yaml vs live DNS
    └── site_health.sh                 # DNS/TLS/HTTP/title probe per URL
```

---
*Managed by ELB Consulting Tech · elenz@elbconsultingtech.com*