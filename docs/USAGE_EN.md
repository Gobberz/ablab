# ABLab Quant — Guide

I cover each tab: **why it exists, what to enter, how to read the result, and common mistakes**.

---

## Quick Start in 60 Seconds

1. Open `src/index.html` in your browser, or use the hosted version.
2. Go to the **Data** tab → click **Generate** in the "Synthetic Generator" section. The default settings are `n=5000`, `lift=2%`.
3. Go to the **Tests** tab → click **Run**. You will see a t-test on the generated data.
4. Go to the **CUPED / CUPAC** tab → click **Run CUPED**. Compare the p-value before and after adjustment.
5. Go to the **Report** tab → **Export Markdown**. All steps will be exported.

This lets you run through the whole stack in one minute and understand the logic.

---

## 01 · Data — Three Ways to Load Data

**CSV Upload.** The file must contain the columns `group`, `metric`, and optionally `pre` for CUPED. Groups are recognized as `a`/`b`, `0`/`1`, `control`/`treatment`/`variant`. The delimiter is detected automatically — switch it manually if the parser makes a mistake, for example with semicolon-separated Russian exports. The preview shows the first 30 rows.

Example: see `examples/sample_experiment.csv`.

**Manual Summary.** If you only have aggregated numbers from a dashboard, such as mean / std / n, enter them and click **Save as active**. The fields `pA`, `pB` are optional and are needed only for z-prop / chi² at the summary level.

**Synthetic Generator.** Used for A/A simulations and test dry runs. Choose a distribution: Normal / Log-normal / Bernoulli / Poisson. `lift` is the percentage effect embedded into group B. `Add pre-period covariate` creates a correlated covariate with ρ ≈ 0.5 — exactly what is needed for CUPED.

After loading data, the **Active Dataset** block appears at the bottom. This signals that the data has been picked up and is available to the other tabs.

**Common mistake:** forgetting to click **Save as active** for manual summary → other tabs will say “no data.”

---

## 02 · Sample Size & MDE — How Many Users You Need

Three blocks:

**Continuous Metric.** Enter the baseline `μ` and `σ`, the desired MDE in **absolute** units. If the metric is revenue in rubles, then MDE = 50 ₽, not 5%. Then enter `α`, usually 0.05, and power, usually 0.8. You get `n` per group. Under the hood: `n = (σ·(z_{α/2}+z_β)/Δ)² · (1 + 1/k)`.

**Proportion Metric.** For conversions. Here, MDE is **relative**: `0.02 = +2%` relative to baseline. `p=0.1, MDE=0.02` means: “I want to detect a shift from 10% to 10.2%.”

**Reverse: MDE at given n.** The reverse problem: you have fixed traffic, for example 5000 users over 2 weeks. What is the minimum effect you can detect? This is the right question for slow-traffic experiments. Often the answer is: “no useful effect.”

**Power Curve.** After calculating Continuous, click **Draw from Continuous params**. You will see how power grows with n. The red line is 0.8. Where the curve reaches a plateau, there is no point collecting more traffic.

**Pro tip:** sanity-check yourself — if you double the MDE, n should drop by about 4× because of the quadratic relationship.

---

## 03 · Tests — Statistical Tests

**Source.** `Active dataset` uses raw data from CSV/synthetic generation. `Manual summary` uses summary numbers only.

**Test choice — short cheat sheet:**

| Test | When to use |
|---|---|
| Welch | Default for means, works with unequal variances — use it if unsure |
| Student | If you know Var(A)=Var(B) — rarely worth choosing manually |
| Mann-Whitney | Nonparametric test, heavy tails, ranked metrics |
| z-prop | Conversions / binary metrics |
| chi² 2×2 | Equivalent to z-prop, gives the same p-value |
| Bootstrap | Strange distributions, ratio metrics, sensitivity checks |

Bootstrap iterations: 5000 is enough for CI; for p-value, better use 10000+.

**Reading the result:** `t / z` is the statistic, `p-value` is the probability of seeing this difference or a larger one under H₀, `diff` is the observed effect, `se` is the standard error. A green badge means significant; a red one means not significant.

**When something does not match:** if z-prop² ≠ χ² exactly, it is rounding — do not worry. If MWU is significant but Welch is not, you likely have a skewed distribution: the median shifted, but the mean did not. Think about what matters more for your business metric.

---

## 04 · Backtest — A/A Validation

**Why it is needed:** to check that the test is calibrated on your data. If the empirical FPR at α=0.05 is, for example, 12%, then the test systematically lies: heavy tails, clustering, or repeated observations from the same user.

**How to use it:**
1. Load a large historical dataset without an A/B split, just the metric for the pre-experiment period.
2. Choose `metric column`.
3. `Iterations = 1000` is fine for a quick answer; `5000` is better for production validation.
4. Click **Run backtest**.

**What to look at:**
- **Empirical FPR** should be close to α, usually 0.05, considering the 95% CI. Green is good.
- **KS vs Uniform** is the Kolmogorov test on p-values. If the p-value is above 0.05, the p-value distribution is close to uniform, as it should be under H₀.
- **Histogram** should be flat, like the red dashed line. A bump near zero means the test rejects H₀ too often, meaning it is anti-conservative. A bump on the right means it is too conservative.

**What to do if FPR is broken:** switch to bootstrap or MWU; check whether one user appears many times in the data. You may need to aggregate to user-level or use cluster bootstrap.

---

## 05 · Switchback — When You Cannot Split by Users

**Why:** marketplace effects, price changes, dispatching algorithms, and other cases where A affects B through the system. User-level splitting does not work here — you need to alternate by time.

**Parameters:**
- **Horizon** — test duration in hours.
- **Block size** — length of one block. It should be at least as long as the system response time. For price changes, 30–60 minutes is usually fine; for matching, 15–30 minutes.
- **Randomization:**
  - `Permuted blocks` — balanced AB/BA pairs. Best default.
  - `Bernoulli` — each block independently assigned. Can create imbalance, but is simpler to analyze.
  - `Latin square` — for day×hour effects, when you want both groups to cover all hours and days.
- **Carryover buffer** — how many minutes to discard at the beginning of a block. This handles the previous block’s effect carrying over into the new one.

**What to look at:** “Detectable MDE” — green means your expected effect is detectable with 80% power; red means the horizon is too short. Increase duration or decrease block size if the system lag allows it.

**Important caveat:** real SE in switchback tests is always higher than the theoretical one because of autocorrelation. CV in the form is your rough adjustment for this. For production analysis, calculate SE using **block-bootstrap** or **cluster-robust SE by day**; otherwise, significance will be inflated.

---

## 06 · CUPED / CUPAC — Variance Reduction

**Why:** if a user has a pre-experiment metric, such as last month’s revenue or any proxy, it can be used as a control. The adjustment `Y' = Y − θ·(X − E[X])` reduces Var(Y') ≈ Var(Y)·(1 − ρ²). With ρ=0.7, this is a **49% variance reduction**, so you can run the test with roughly half the traffic.

**How:**
1. The active dataset must contain `metric`, `pre` or another covariate, and `group`.
2. Select the columns in the selectors. They fill automatically if you use standard names.
3. Click **Run CUPED**.

**How to read it:**
- **θ** — regression coefficient: how strongly Y depends on X.
- **ρ²(Y,X)** — expected percentage variance reduction. If it is below 0.1, CUPED gives almost nothing; look for a better covariate.
- **Effective n boost** — how many times fewer users are needed for the same power.
- **raw vs CUPED table** — p-value before and after. CUPED almost always gives a lower, or equal, p-value.

**CUPAC vs CUPED:** in CUPAC, covariate X is an **ML model prediction** based on pre-period features. It is done separately: train GBDT/XGBoost on pre-experiment data, where the target is your metric and features are everything available before the experiment starts. Save predictions as the `pre` column, then the rest is the same. ABLab does not train the model itself — it simply uses the X you provide correctly.

**Pitfall:** do not calculate θ separately for A and B — that introduces bias. The tool calculates it on pooled data, as it should.

---

## 07 · Bayesian — Without the Peeking Problem

**Beta-Binomial for conversions.**
- `Prior α / β` — `1/1` is a uniform prior and a safe default; `0.5/0.5` is Jeffreys; `s/n` is informed. For most tasks, the difference is below 1%.
- Enter `successes / trials` for A and B.
- `Samples = 20000` — Monte Carlo samples for estimating P(B>A) and expected loss.

**How to read it:**
- **P(B > A)** — the main metric. A common decision rule: launch B if it is ≥ 95%.
- **E[lift]** — expected uplift.
- **E[loss | pick A/B]** — expected regret. This is the key metric for business decisions: “if I choose B and I am wrong, how much do I lose on average?” Stopping condition: while both loss functions are above the threshold, continue the test.

**Normal-Normal for means.** Similar, but for continuous metrics. `Prior τ₀ = 1e6` is practically a flat prior and is recommended when you have no prior knowledge. You get P(B>A), a credible interval for the difference, and expected loss.

**When Bayesian is better than frequentist:** when you need to stop the test early, when you have prior knowledge from previous experiments, or when stakeholders care about the interpretation “probability that B is better,” rather than “p-value.”

---

## 08 · SRM — Must-Have Check

Run it **every day** during the test. It is a χ² test checking whether the actual split matches the expected split.

**Input:** `10012, 9988` observed counts, `0.5, 0.5` expected proportions, where the sum equals 1. Works for any number of groups.

**The threshold is not 0.05, but 0.0005.** Industry standard: Microsoft / Booking / Spotify. With so many experiments, false alarms at 5% will burn out the team. Green means OK, yellow means investigate, red means **stop the test and find the cause**.

**Where SRM comes from in reality:** bucketing bug, event loss in one branch, frontend error only in B, bot filtering working differently, or caching that segments by cookie.

---

## 09 · Sequential SPRT — Early Stopping

**Why:** in a fixed-horizon test, peeking is not allowed; otherwise FPR → 1. SPRT/mSPRT solve this: you can check every day and stop as soon as LLR crosses a boundary.

**Parameters:**
- `p₀` — null, the status quo.
- `p₁` — alternative, the minimum effect worth running the test for.
- `α / β` — usually 0.05 / 0.2.
- Current cumulative `successes / trials`.

**Decision rule** is shown at the bottom:
- LLR ≥ upper → stop, there is an effect.
- LLR ≤ lower → stop, there is no effect.
- In between → continue.

**E[n | H1]** — expected sample size on average. Usually around 50% of fixed-horizon size — this is the gain from the sequential approach.

---

## 10 · Multi Testing — Corrections

If you measure 5+ metrics at the same time, you need corrections; otherwise at least one metric will become “significant” by chance.

**Input:** list of p-values separated by commas or new lines.

**Method:**
- **Bonferroni** — the strictest, controls FWER. Use for guardrail metrics where false positives are expensive.
- **Holm** — uniformly better than Bonferroni, also controls FWER. Default if you need FWER.
- **BH (Benjamini-Hochberg)** — controls FDR. Default for exploration, when there are 10+ metrics and 5% false discoveries are acceptable.
- **BY** — for dependent metrics, when metrics are correlated with each other.

**Reading:** the `p adj` column is the adjusted p-value; compare it directly with α. ✓ means H₀ is rejected.

---

## 11 · Ratio Metrics — Delta Method

**Why:** revenue per user, CTR per session, AOV — these are `ΣX / ΣY`, not an average of ratios. A simple t-test on user-level ratios gives a **biased** estimate and underestimates SE, which causes false positives to spike.

**What to enter for groups A and B:**
- `Σnum` — numerator sum, for example total revenue.
- `Σden` — denominator sum, for example total number of sessions.
- `n` — number of clusters, usually users.
- `Var(num)`, `Var(den)`, `Cov(num,den)` — at the **user level**. Calculate them beforehand in SQL/Python:
```sql
SELECT
  VARIANCE(user_revenue) AS var_num,
  VARIANCE(user_sessions) AS var_den,
  COVAR_SAMP(user_revenue, user_sessions) AS cov_nd
FROM user_aggregated
```

**Reading:** SE accounts for covariance — that is the key feature of the delta method. Compare it with a naive `t.test(R_a, R_b)` on the same sample. Usually SE becomes higher and significance drops, which is correct.

---

## 12 · Report — Export

Each calculation is automatically logged in the **Run Log**. You see timestamp, calculation type, and key numbers.

- **Export Markdown** — for Confluence / Notion / Jira ticket.
- **Export JSON** — for machine processing or attaching to documentation.
- **Clear** — reset everything for a new experiment.

---

## Typical Workflow for a New Experiment

1. **Sample Size** — calculate the required n before launch. If traffic is not enough, discuss it with the team earlier, not later.
2. **Backtest** on historical data — make sure the test is calibrated, meaning FPR ≈ α.
3. Launch the experiment in production.
4. **SRM every day** while the test is running.
5. After completion: **Tests** frequentist + **Bayesian** for stakeholder intuition + **CUPED** if pre-period data exists.
6. If there are several metrics — **Multi Testing**.
7. **Report → Export** → attach to the ticket.

---

## What Is Saved and What Is Not

- Data lives **only in the browser/application memory**. Reload the page — everything is gone. This is by design: zero dependencies, no backend.
- **Run Log** also disappears after reload — export it before closing.
- No cookies and no tracking — open it, work with it, close it.
