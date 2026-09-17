"""BLOCKER-9 + 10: Plan round-trip and revision +1."""

import tempfile

from cat_sticker_skill.models.plan import GenerationPlan, StickerPlanItem
from cat_sticker_skill.project import store


def test_plan_roundtrip_all_fields(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        item = StickerPlanItem(
            id="s001",
            reference_type="group",
            reference_ids=["r1", "r2"],
            caption="蚌埠住了",
            emotion="破防",
            pose="趴桌子",
            composition="close-up",
            identity_priority="max",
            typography_preset="meme-yellow",
            status="planned",
            theme="dark humor",
            negative_constraints=["no dogs", "no extra limbs"],
        )
        plan = GenerationPlan(project_id="p1", items=[item])
        store.save_plan(plan)

        loaded = store.load_plan("p1")
        li = loaded.items[0]
        assert li.caption == "蚌埠住了"
        assert li.emotion == "破防"
        assert li.pose == "趴桌子"
        assert li.composition == "close-up"
        assert li.identity_priority == "max"
        assert li.typography_preset == "meme-yellow"
        assert li.theme == "dark humor"
        assert li.negative_constraints == ["no dogs", "no extra limbs"]
        assert li.reference_ids == ["r1", "r2"]


def test_revision_only_plus_one(monkeypatch):
    from cat_sticker_skill.project.controller import ProjectController
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", caption="a", reference_type="single", reference_ids=["r"])])
        rev1 = c.plan.plan_revision
        c.modify_plan([StickerPlanItem(id="s1", caption="b", reference_type="single", reference_ids=["r"])])
        rev2 = c.plan.plan_revision
        assert rev2 - rev1 == 1, f"Expected +1, got {rev2-rev1}"
