"""Tests for approval gate and budget ledger."""

from cat_sticker_skill.models.plan import GenerationPlan, StickerPlanItem
from cat_sticker_skill.workflow.approval import ApprovalGate, BudgetLedger, CallRecord


def _make_plan():
    items = [
        StickerPlanItem(id="s001", reference_type="single", caption="test1"),
        StickerPlanItem(id="s002", reference_type="single", caption="test2"),
        StickerPlanItem(id="s003", reference_type="single", caption="test3"),
    ]
    return GenerationPlan(project_id="test", items=items)


def test_not_approved_blocks_generation():
    plan = _make_plan()
    gate = ApprovalGate(plan)
    allowed, reason = gate.can_generate()
    assert not allowed
    assert "not approved" in reason.lower()


def test_approve_allows_generation():
    plan = _make_plan()
    gate = ApprovalGate(plan)
    gate.approve()
    allowed, _ = gate.can_generate()
    assert allowed


def test_plan_change_invalidates_approval():
    plan = _make_plan()
    gate = ApprovalGate(plan)
    gate.approve()
    gate.invalidate_approval()
    allowed, reason = gate.can_generate()
    assert not allowed
    assert "revision mismatch" in reason.lower() or "not approved" in reason.lower()


def test_budget_ledger_tracks_calls():
    ledger = BudgetLedger(planned_count=3, max_total_calls=5, max_retries_per_item=2)
    assert ledger.can_call("s001")
    ledger.record_call(CallRecord(item_id="s001", attempt=1, success=True))
    assert ledger.paid_calls_used == 1
    assert ledger.remaining_budget == 4


def test_budget_exhaustion():
    ledger = BudgetLedger(planned_count=3, max_total_calls=2, max_retries_per_item=2)
    ledger.record_call(CallRecord(item_id="s001", attempt=1, success=True))
    ledger.record_call(CallRecord(item_id="s002", attempt=1, success=True))
    assert not ledger.can_call("s003")


def test_retry_limit_per_item():
    # Semantics: 1 initial + max_retries retries = 1+max_retries total attempts
    ledger = BudgetLedger(planned_count=3, max_total_calls=10, max_retries_per_item=1)
    ledger.record_call(CallRecord(item_id="s001", attempt=1, success=False))
    # Still allowed: this is the 1st retry (2nd attempt total)
    assert ledger.can_call("s001")
    ledger.record_call(CallRecord(item_id="s001", attempt=2, success=False))
    # Now blocked: 2 attempts used = 1 initial + 1 retry
    assert not ledger.can_call("s001")
