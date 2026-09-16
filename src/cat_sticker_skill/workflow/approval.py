"""Approval gate and budget ledger — hard code-level safety for paid generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cat_sticker_skill.models.plan import GenerationPlan


@dataclass
class CallRecord:
    item_id: str
    attempt: int
    success: bool
    error_class: str = ""
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BudgetLedger:
    run_id: str = ""
    planned_count: int = 0
    max_total_calls: int = 0
    max_retries_per_item: int = 2
    paid_calls_used: int = 0
    retry_calls_used: int = 0
    records: List[CallRecord] = field(default_factory=list)

    @property
    def remaining_budget(self) -> int:
        return max(0, self.max_total_calls - self.paid_calls_used)

    def can_call(self, item_id: str) -> bool:
        """Check if another paid call is allowed."""
        if self.paid_calls_used >= self.max_total_calls:
            return False
        # Count attempts for this item
        item_attempts = sum(1 for r in self.records if r.item_id == item_id)
        if item_attempts >= self.max_retries_per_item:
            return False
        return True

    def record_call(self, record: CallRecord) -> None:
        self.records.append(record)
        if record.success:
            self.paid_calls_used += 1
        else:
            self.retry_calls_used += 1


class ApprovalGate:
    """Hard gate: no paid generation without approval."""

    def __init__(self, plan: GenerationPlan):
        self.plan = plan
        self.ledger: Optional[BudgetLedger] = None

    def approve(self) -> None:
        """Mark current plan revision as approved."""
        self.plan.approved_for_generation = True
        self.plan.approved_revision = self.plan.plan_revision

    def invalidate_approval(self) -> None:
        """Call when plan changes; approval must be renewed."""
        self.plan.approved_for_generation = False
        self.plan.plan_revision += 1

    def can_generate(self) -> tuple[bool, str]:
        """Check if generation is allowed. Returns (allowed, reason)."""
        if not self.plan.approved_for_generation:
            return False, "Plan not approved. Call approve() first."
        if self.plan.plan_revision != self.plan.approved_revision:
            return False, f"Plan revision mismatch: plan={self.plan.plan_revision}, approved={self.plan.approved_revision}"
        return True, ""

    def create_ledger(self, max_total_calls: int, max_retries_per_item: int = 2) -> BudgetLedger:
        """Create a budget ledger for a generation run."""
        self.ledger = BudgetLedger(
            run_id=f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            planned_count=self.plan.total_images,
            max_total_calls=max_total_calls,
            max_retries_per_item=max_retries_per_item,
        )
        return self.ledger
