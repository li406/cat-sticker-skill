"""BLOCKER-4: Prompt builder consumes plan fields."""

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.workflow.prompt_builder import build_seedream_prompt


def _item(**kw):
    defaults = dict(id="s1", reference_type="single", reference_ids=["r1"], caption="test")
    defaults.update(kw)
    return StickerPlanItem(**defaults)


def test_prompt_includes_emotion():
    item = _item(caption="happy", emotion="grumpy", pose="sitting")
    prompt = build_seedream_prompt(item)
    assert "grumpy" in prompt
    assert "sitting" in prompt


def test_prompt_includes_no_text_constraint():
    item = _item(caption="hello")
    prompt = build_seedream_prompt(item)
    assert "DO NOT render" in prompt
    assert "white background" in prompt


def test_prompt_includes_character():
    from cat_sticker_skill.models.character import CharacterProfile
    char = CharacterProfile(
        character_id="c1",
        display_name="Mittens",
        coat_color="gray",
        coat_pattern="tabby",
        eye_color="green",
        accessories=["tiny hat"],
    )
    item = _item(caption="sad", emotion="sad")
    prompt = build_seedream_prompt(item, character=char)
    assert "gray" in prompt
    assert "tabby" in prompt
    assert "green" in prompt
    assert "hat" in prompt


def test_prompt_includes_negative_constraints():
    item = _item(caption="test", negative_constraints=["no dogs", "no furniture"])
    prompt = build_seedream_prompt(item)
    assert "no dogs" in prompt
    assert "furniture" in prompt
