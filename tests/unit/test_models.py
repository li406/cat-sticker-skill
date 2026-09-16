"""Tests for data models."""

from cat_sticker_skill.models import CharacterProfile, GenerationPlan, StickerPlanItem


def test_character_profile_roundtrip():
    c = CharacterProfile(
        character_id="cat_01",
        coat_color="blue-grey",
        eye_color="yellow",
        accessories=["pointy ear hat"],
        preserve=["grey coat", "yellow eyes"],
    )
    d = c.to_dict()
    c2 = CharacterProfile.from_dict(d)
    assert c2.coat_color == "blue-grey"
    assert c2.accessories == ["pointy ear hat"]
    assert c2.preserve == ["grey coat", "yellow eyes"]


def test_generation_plan_needs_reapproval():
    plan = GenerationPlan(project_id="test")
    assert not plan.approved_for_generation
    assert plan.needs_reapproval

    plan.approved_revision = 1
    plan.plan_revision = 1
    assert not plan.needs_reapproval

    plan.plan_revision = 2
    assert plan.needs_reapproval


def test_sticker_plan_item():
    item = StickerPlanItem(
        id="sticker_001",
        reference_type="single",
        reference_ids=["photo_01"],
        caption="不想上班",
        emotion="生无可恋",
    )
    d = item.to_dict()
    assert d["reference"]["type"] == "single"
    assert d["caption"] == "不想上班"
