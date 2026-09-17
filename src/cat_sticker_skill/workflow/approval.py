"""Approval gate and budget ledger — hard code-level safety for paid generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cat_sticker_skill.models.plan import GenerationPlan


def _plan_hash(plan: GenerationPlan) -> str:
    """Stable hash of plan content for tamper detection."""
    canonical = json.dumps(plan.to_dict(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


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
    requests_sent: int = 0
    successful_generations: int = 0
    failed_attempts: int = 0
    records: List[CallRecord] = field(default_factory=list)

    @property
    def remaining_budget(self) -> int:
        return max(0, self.max_total_calls - self.requests_sent)

    @property
    def paid_calls_used(self) -> int:
        return self.successful_generations

    @property
    def retry_calls_used(self) -> int:
        # retry = extra attempts beyond the first attempt per item
        # For each item: attempts_sent - 1 (clamped at 0)
        per_item: dict[str, int] = {}
        for r in self.records:
            per_item[r.item_id] = per_item.get(r.item_id, 0) + 1
        return sum(max(0, n - 1) for n in per_item.values())

    def can_call(self, item_id: str) -> bool:
        if self.requests_sent >= self.max_total_calls:
            return False
        item_attempts = sum(1 for r in self.records if r.item_id == item_id)
        # allowed: 1 initial + max_retries_per_item retries
        if item_attempts >= 1 + self.max_retries_per_item:
            return False
        return True

    def record_call(self, record: CallRecord) -> None:
        self.records.append(record)
        self.requests_sent += 1
        if record.success:
            self.successful_generations += 1
        else:
            self.failed_attempts += 1


class ApprovalGate:
    """Hard gate: no paid generation without approval."""

    def __init__(self, plan: GenerationPlan):
        self.plan = plan
        self.ledger: Optional[BudgetLedger] = None

    def approve(self) -> None:
        """Mark current plan as approved."""
        self.plan.approved_for_generation = True
        self.plan.approved_revision = self.plan.plan_revision

    def invalidate_approval(self) -> None:
        """Invalidate approval and bump revision (single increment)."""
        self.plan.approved_for_generation = False
        self.plan.plan_revision += 1

    def can_generate(self) -> tuple[bool, str]:
        if not self.plan.approved_for_generation:
            return False, "Plan not approved. Call approve() first."
        if self.plan.plan_revision != self.plan.approved_revision:
            return False, (
                f"Plan revision mismatch: plan={self.plan.plan_revision}, "
                f"approved={self.plan.approved_revision}"
            )
        return True, ""

    def create_ledger(self, max_total_calls: int, max_retries_per_item: int = 2) -> BudgetLedger:
        self.ledger = BudgetLedger(
            run_id=f"run_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            planned_count=self.plan.total_images,
            max_total_calls=max_total_calls,
            max_retries_per_item=max_retries_per_item,
        )
        return self.ledger
