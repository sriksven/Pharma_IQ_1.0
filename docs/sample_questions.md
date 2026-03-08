# Sample Questions & Expected Answers

These are example questions you can ask PharmaIQ in the chat UI, along with the expected type of answer based on the current dataset (GAZYVA, Aug 2024 – onward, 90 HCPs, 3 territories, 9 reps).

---

## 📊 Prescription Volumes

**1. What is the total NRx count across all HCPs?**
> ~8,322 new prescriptions across all HCPs and time periods.

**2. What is the total TRx count?**
> ~26,059 total prescriptions.

**3. How many total prescriptions were written for GAZYVA?**
> GAZYVA is the only brand in the dataset; all 8,322 NRx and 26,059 TRx belong to it.

**4. Which specialty has the highest NRx volume?**
> Rheumatology leads with ~3,556 NRx, followed by Internal Medicine (~2,582) and Nephrology (~2,184).

**5. What is the NRx breakdown by specialty?**
> Rheumatology: 3,556 | Internal Medicine: 2,582 | Nephrology: 2,184.

**6. Which territory has the highest NRx?**
> Territory 3 (~2,846), followed by Territory 2 (~2,783) and Territory 1 (~2,693) — relatively balanced.

**7. How does NRx compare across territories?**
> Territory 3: 2,846 | Territory 2: 2,783 | Territory 1: 2,693.

**8. Which tier of doctors writes the most prescriptions?**
> Tier C HCPs collectively write the most NRx (~3,154), but individually Tier A HCPs write more per doctor since there are fewer of them.

**9. What is the NRx by HCP tier?**
> Tier C: 3,154 | Tier B: 2,847 | Tier A: 2,321.

**10. Who are the top 5 prescribing doctors?**
> Dr Blake Garcia (128), Dr Phoenix Lee (117), Dr Morgan White (115), Dr Sydney Johnson (113), Dr Taylor Gonzalez (112) — all Rheumatology or Internal Medicine.

---

## 👨‍⚕️ HCP / Doctor Questions

**11. How many unique doctors are in the database?**
> 90 HCPs total.

**12. What specialties are covered in the dataset?**
> Three: Rheumatology, Internal Medicine, and Nephrology.

**13. How many Tier A doctors are there?**
> 26 Tier A HCPs.

**14. How many Tier B and Tier C doctors are there?**
> Tier B: 30 | Tier C: 34.

**15. Which specialty has the most doctors?**
> Each specialty likely has around 30 HCPs (90 total across 3 specialties).

**16. How many doctors are in Territory 1?**
> 30 HCPs are assigned to Territory 1.

**17. Who are the Rheumatology doctors with the highest NRx?**
> Dr Blake Garcia (128), Dr Phoenix Lee (117), Dr Morgan White (115), Dr Taylor Gonzalez (112) — all Rheumatology.

**18. What is the average NRx per doctor?**
> ~92 NRx per HCP (8,322 ÷ 90).

**19. Show me all Tier A doctors in Territory 2.**
> The system will join hcp_dim filtered to tier='A' and territory_id=2.

**20. Which doctors have not had any rep activity?**
> The system will find HCPs with hcp_id not present in fact_rep_activity.

---

## 🧑‍💼 Sales Rep Activity

**21. How many total rep activities are recorded?**
> 2,962 total activities across all reps.

**22. What activity types do reps perform?**
> Two types: `call` (1,514 occurrences) and `lunch_meeting` (1,448 occurrences).

**23. Which rep made the most calls?**
> Taylor Wilson with 189 calls, followed by Taylor Kim (187) and Sage Brown (170).

**24. Who are the top 5 most active reps by total activities?**
> Taylor Wilson, Taylor Kim, Sage Brown, Jamie Thomas, and River White lead in activity count.

**25. How many reps are in Territory 1?**
> 3 reps: Morgan Chen, Jamie Thomas, Casey Gonzalez.

**26. Which reps cover Territory 2?**
> River White, Taylor Wilson, Sage Brown.

**27. Which reps cover Territory 3?**
> River Miller, Reese Miller, Taylor Kim.

**28. What is the average call duration?**
> The system will aggregate `duration_min` from fact_rep_activity for activity_type = 'call'.

**29. How many lunch meetings were held in Territory 3?**
> System will filter fact_rep_activity by reps in Territory 3 and activity_type = 'lunch_meeting'.

**30. Which rep has the highest NRx from the HCPs they visited?**
> System will join fact_rep_activity → hcp_dim → fact_rx to correlate rep visits with prescriptions.

---

## 💊 Payer / Market Access

**31. What payer types are in the dataset?**
> Four: Medicare, Medicaid, Commercial, Other.

**32. What is the average payer mix breakdown?**
> Roughly balanced: Medicare ~25.7%, Other ~25.1%, Commercial ~24.7%, Medicaid ~24.5% of volume.

**33. Which payer type has the highest share of volume?**
> Medicare has the highest average pct_of_volume.

**34. What is the Medicaid share for account A001?**
> System filters fact_payor_mix by account_id = A001 and payor_type = 'Medicaid'.

**35. How has Commercial payer share trended over time?**
> System joins fact_payor_mix with date_dim and filters for payor_type = 'Commercial'.

---

## 🏥 Account Questions

**36. How many accounts are in the database?**
> 24 accounts total.

**37. What account types exist?**
> Hospital and Clinic (from account_dim.account_type).

**38. Which territory has the most accounts?**
> System groups account_dim by territory_id and counts.

**39. How many hospital accounts are there?**
> System filters account_dim where account_type = 'Hospital'.

**40. List all accounts in Territory 2.**
> System filters account_dim by territory_id = 2.

---

## 📈 Launch Metrics

**41. What entity types are tracked in launch metrics?**
> Two: `A` (Account-level) and `H` (HCP-level).

**42. What is the average estimated market share across all accounts?**
> System averages est_market_share from fact_ln_metrics for entity_type = 'A'.

**43. Which account has the highest launch patient count?**
> System finds max(ln_patient_cnt) from fact_ln_metrics for entity_type = 'A'.

**44. What is the market share trend by quarter for GAZYVA?**
> System aggregates est_market_share grouped by quarter_id from fact_ln_metrics.

**45. Which HCPs have the most launch patients?**
> System filters fact_ln_metrics for entity_type = 'H' and orders by ln_patient_cnt descending.

---

## 📅 Time-Based Questions

**46. What date range does the data cover?**
> The date_dim spans from 2024-08-01 through the most recent date loaded (~18 months of data based on 518 rows).

**47. What is the NRx for Q3 2024?**
> System groups fact_rx joined with date_dim where quarter = 'Q3' and year = 2024.

**48. How did NRx trend week over week?**
> System groups fact_rx by week_num and year from date_dim.

**49. What day of the week sees the most rep calls?**
> System joins fact_rep_activity with date_dim grouped by day_of_week.

**50. What is the monthly NRx trend for Rheumatology?**
> System joins fact_rx → hcp_dim (specialty = 'Rheumatology') → date_dim grouped by year + month.

---

## ❌ Questions the System Cannot Answer

The following will result in a polite "I don't have that information" response:

- "What is the stock price of the company?"
- "What are the side effects of GAZYVA?"
- "Who is the CEO?"
- "What are competitor sales numbers?"
- "What is the weather today?"
