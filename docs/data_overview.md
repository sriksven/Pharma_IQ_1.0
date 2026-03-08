# Data Overview

## About the Dataset

PharmaIQ is powered by a **pharmaceutical sales and field operations dataset**, modeled around a company selling two drugs -- **BRAND_A** and **BRAND_B** -- across three US sales territories. The dataset follows a classic **star schema** (fact tables + dimension tables) and covers the first half of **2024** (January-June).

---

## Fact Tables (What Happened)

| Table | Description |
|---|---|
| `fact_rx` | Prescription volume per doctor, per brand, per month. `trx_cnt` = total Rx refills, `nrx_cnt` = **new** prescriptions only. |
| `fact_rep_activity` | Sales rep field activities -- doctor visits, sample drops, call notes logged per HCP. |
| `fact_ln_metrics` | Territory-level market share data over time vs. competitors (`market_share`, `competitor_trx`). |
| `fact_payor_mix` | Insurance / payer coverage data for each account -- Commercial, Medicare, and Medicaid breakdowns. |

---

## Dimension Tables (Who / Where / When)

| Table | Description |
|---|---|
| `hcp_dim` | Doctors (Healthcare Professionals) -- name, specialty (Cardiology, Oncology, Rheumatology), priority tier (A/B/C), and territory assignment. |
| `rep_dim` | Sales reps -- name, territory assignment, and hire date. |
| `territory_dim` | The 3 sales territories -- Northeast, Southeast, Midwest -- each with an assigned regional manager. |
| `account_dim` | Hospital and clinic accounts that reps call on (e.g., Metro General Hospital, Eastside Clinic). |
| `date_dim` | Monthly calendar spine -- provides `full_date`, `month`, `quarter`, `year`, and `month_name` for time-based slicing. |

---

## The Business Story

> A pharma company's field sales team (4 reps across 3 territories of the US) visits doctors to promote BRAND_A and BRAND_B. The goal is to increase **new prescription volume** (`nrx_cnt`), grow **market share**, and track which reps, territories, and doctor specialties are driving the most growth -- all while monitoring payer mix and account coverage.

This is a compact but realistic **pharma commercial analytics** dataset -- the type commonly used in Sales Force Effectiveness (SFE) reporting at companies like Pfizer, AbbVie, or any specialty pharma firm.

---

## Key Metrics

| Metric | Column | Table |
|---|---|---|
| New Prescriptions | `nrx_cnt` | `fact_rx` |
| Total Prescriptions | `trx_cnt` | `fact_rx` |
| Market Share | `market_share` | `fact_ln_metrics` |
| Competitor Volume | `competitor_trx` | `fact_ln_metrics` |
| Estimated Market Share | `est_market_share` | `fact_payor_mix` / `fact_ln_metrics` |
| Covered Lives | `covered_lives` | `fact_payor_mix` |

---

## Schema Relationships

```
date_dim ──────────────────┐
                           │
hcp_dim ──── fact_rx ──────┤
                           │
rep_dim ── fact_rep_activity──territory_dim
                           │
account_dim ── fact_payor_mix
                           │
               fact_ln_metrics
```

All fact tables link to `date_dim` via `date_id`, and most link to `territory_dim` or `hcp_dim` via their respective foreign keys.
