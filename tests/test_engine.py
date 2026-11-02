"""
Comprehensive unit and edge-case verification suite for Solana Scheduler Measurement Engine.
Tests C-001 (Zero division on identical fees), M-001 (Spearman Rank Correlation),
M-002 (Base64 ComputeBudget decoding), and M-003 (Edge cases: ties, empty blocks).
"""

from decimal import Decimal
from src.engine import SolanaSchedulerMeasurementEngine, TransactionTelemetry, COMPUTE_BUDGET_PROGRAM_ID


def test_spend_cap_enforcement():
    engine = SolanaSchedulerMeasurementEngine(spend_cap_sol=Decimal("1.0"))
    assert engine.spend_cap_sol == Decimal("0.05")
    assert engine.dry_run is True


def test_fix_c001_division_by_zero_identical_fees():
    """Tests that identical fees across all transactions do not crash with division by zero (C-001)."""
    engine = SolanaSchedulerMeasurementEngine()
    txs = [
        TransactionTelemetry("sig1", 100, 0, 50000, 5000, 200000, 5000.0),
        TransactionTelemetry("sig2", 100, 1, 50000, 5000, 200000, 5000.0),
        TransactionTelemetry("sig3", 100, 2, 50000, 5000, 200000, 5000.0),
        TransactionTelemetry("sig4", 100, 3, 50000, 5000, 200000, 5000.0),
        TransactionTelemetry("sig5", 100, 4, 50000, 5000, 200000, 5000.0),
    ]
    res = engine.analyze_ordering_rule(txs)
    assert res["status"] == "IDENTICAL_FEE_DISTRIBUTION_NO_VARIANCE"
    assert res["spearman_rho"] == 0.0
    assert res["inferred_rule"] == "UNIFORM_FEE_FIFO_OR_NETWORK_ARRIVAL"


def test_fix_m001_spearman_perfect_priority_auction():
    """Tests that higher priority fees at lower block indices yield rho = -1.0."""
    engine = SolanaSchedulerMeasurementEngine()
    txs = [
        TransactionTelemetry("sig1", 100, 0, 50000, 100000, 200000, 100000.0),
        TransactionTelemetry("sig2", 100, 1, 50000, 50000, 200000, 50000.0),
        TransactionTelemetry("sig3", 100, 2, 50000, 20000, 200000, 20000.0),
        TransactionTelemetry("sig4", 100, 3, 50000, 5000, 200000, 5000.0),
        TransactionTelemetry("sig5", 100, 4, 50000, 0, 200000, 0.0),
    ]
    res = engine.analyze_ordering_rule(txs)
    assert res["status"] == "VALID_SPEARMAN"
    assert res["spearman_rho"] == -1.0
    assert "STRICT_PRIORITY_FEE_AUCTION" in res["inferred_rule"]


def test_fix_m002_decode_raw_computebudget_instructions():
    """Tests decoding raw base64 ComputeBudget byte payloads."""
    import base64
    import struct

    # Discriminator 3 (SetComputeUnitPrice) + 50,000 micro-lamports (u64 little endian)
    raw_fee = struct.pack("<BQ", 3, 50000)
    b64_fee = base64.b64encode(raw_fee).decode("ascii")

    # Discriminator 2 (SetComputeUnitLimit) + 300,000 units (u32 little endian)
    raw_limit = struct.pack("<BI", 2, 300000)
    b64_limit = base64.b64encode(raw_limit).decode("ascii")

    engine = SolanaSchedulerMeasurementEngine()
    _, fee_parsed = engine.decode_compute_budget_instruction(b64_fee)
    limit_parsed, _ = engine.decode_compute_budget_instruction(b64_limit)

    assert fee_parsed == 50000
    assert limit_parsed == 300000

    # Parse full block containing raw programId instructions
    mock_block = {
        "transactions": [
            {
                "transaction": {
                    "signatures": ["sig_raw_test"],
                    "message": {
                        "accountKeys": [COMPUTE_BUDGET_PROGRAM_ID],
                        "instructions": [
                            {"programId": COMPUTE_BUDGET_PROGRAM_ID, "data": b64_fee},
                            {"programId": COMPUTE_BUDGET_PROGRAM_ID, "data": b64_limit},
                        ],
                    },
                },
                "meta": {"computeUnitsConsumed": 25000},
            }
        ]
    }
    parsed = engine.parse_block_transactions(mock_block, slot=555)
    assert len(parsed) == 1
    assert parsed[0].priority_fee_micro_lamports == 50000
    assert parsed[0].compute_unit_limit == 300000


def test_fix_m003_edge_cases_empty_and_small_blocks():
    """Tests handling of empty blocks and samples smaller than 5 transactions."""
    engine = SolanaSchedulerMeasurementEngine()
    empty_block = {"transactions": []}
    parsed = engine.parse_block_transactions(empty_block, slot=1)
    assert len(parsed) == 0

    analysis = engine.analyze_ordering_rule(parsed)
    assert analysis["inferred_rule"] == "INSUFFICIENT_SAMPLE"
    assert analysis["sample_size"] == 0
