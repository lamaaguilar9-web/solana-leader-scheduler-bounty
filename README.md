# Inside the Block: How Solana Validators Order Transactions

**Autonomous Measurement and Empirical Analysis of Transaction Ordering Policies across Solana Mainnet Validator Forks (Agave, Jito-Solana, Firedancer)**

Built by **Sentinel Fleet Technologies** for the **Superteam Ukraine "Inside the Block" Bounty** ($2,500 USDC).

---

## 🎯 Executive Summary & Mission

The transaction execution sequence within a Solana block is determined by the leader's internal scheduler. In the canonical open-source **Agave** client, this ordering is governed by multi-threaded BankingStage worker channels. However, the exact behavior of validator forks that hold substantial network stake (specifically **Jito-Solana**) and emerging clients like **Firedancer** is rarely documented empirically under controlled conditions.

This repository provides an automated, containerized benchmarking suite that:
1. Measures transaction placement dynamics across **6 distinct Solana Mainnet validators** spanning **3 client software families**.
2. Evaluates whether validator scheduling adheres to a **Strict Priority-Fee Greedy Auction**, **First-In First-Out (FIFO) pipeline queues**, or **Multi-Threaded BankingStage Partitioning**.
3. Enforces strict safety guarantees: **Dry-run mode enabled by default** with a hardcoded **0.05 SOL spend ceiling** enforced at the engine level.

---

## 🔬 Experimental Methodology & Architecture

```
[ Solana Mainnet Leader Schedule ]
              │
              ▼
 ┌─────────────────────────────┐
 │  Sentinel Measurement Suite │
 └─────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
 [ Agave BankingStage ] [ Jito-Solana Engine ]
   • Multi-Channel       • Priority-Fee Auction
   • Lock-Free Queues    • Latency Shuffling
        │             │
        └──────┬──────┘
               ▼
 [ Statistical Monotonic Ordering Analysis ]
```

### Validator Client Matrix
We evaluate transaction slot landings across three primary architectures:
1. **Agave Standard (`v2.0.x / v2.1.x`):** Standard BankingStage scheduler allocating non-conflicting account locks across worker threads.
2. **Jito-Solana (`v2.0.x-jito`):** MEV-boosted scheduler prioritizing higher compute-unit price bids alongside bundle insertion points.
3. **Firedancer / Frankendancer:** High-performance C-based consensus engine with optimized memory pools.

---

## 📊 Mathematical Analysis: Monotonic Fee Ordering

The engine computes an empirical **Fee Monotonic Ordering Ratio ($R_{ord}$)** defined over transaction pairs within the same slot block:

$$R_{ord} = 1 - \frac{\text{Inversions}}{\text{Total Distinct Fee Pairs}}$$

* **$R_{ord} > 0.75$:** Strong Priority-Fee Auction (higher priority fee guarantees earlier index placement).
* **$R_{ord} < 0.40$:** FIFO or packet-arrival network latency dominated.
* **$0.40 \le R_{ord} \le 0.75$:** Partitioned Multi-Thread Scheduler (BankingStage parallel execution).

---

## 🚀 One-Command Reproducibility (Docker Compose)

Per bounty submission criteria, the entire measurement and analysis suite can be executed with a single command:

```bash
docker compose up --build
```

### Running Locally with Pytest

```bash
python -m pytest -v
python -m src.measure
```

---

## 🛡️ Spend Cap & Security Guarantees

* **Zero Key Leakage:** No private keys are stored in code or repository.
* **Dry-Run by Default:** Real transactions are only dispatched if `DRY_RUN=false` is explicitly passed via environment variable.
* **Hard Spend Ceiling:** Clamped at `0.05 SOL` max spend.

---

## 🏛️ Author & Sentinel Fleet Technologies
* **Author:** Luis Aguilar — Founder & CEO, Sentinel Fleet Technologies
* **Contact:** `lamaaguilar9@gmail.com`
* **Repository:** `https://github.com/lamaaguilar9-web/solana-leader-scheduler-bounty`
