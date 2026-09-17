"""Prompt builder: construct Seedream prompts from plan items + character profiles."""

from __future__ import annotations

from cat_sticker_skill.models.character import CharacterProfile
from cat_sticker_skill.models.plan import StickerPlanItem


def build_seedream_prompt(
    item: StickerPlanItem,
    character: CharacterProfile | None = None,
) -> str:
    """Build a complete Seedream generation prompt.

    The caption is semantic intent only — explicitly tell the model NOT to render text.
    """
    parts = []

    # Subject identity from character profile
    if character:
        if character.coat_color:
            parts.append(f"{character.coat_color} cat")
        if character.coat_pattern:
            parts.append(character.coat_pattern)
        if character.eye_color:
            parts.append(f"{character.eye_color} eyes")
        if character.hair_length:
            parts.append(f"hair length: {character.hair_length}")
        if character.body_type:
            parts.append(f"body type: {character.body_type}")
        if character.face_shape:
            parts.append(f"face shape: {character.face_shape}")
        if character.distinctive_markings:
            parts.append(f"distinctive markings: {', '.join(character.distinctive_markings)}")
        if character.accessories:
            parts.append(f"wearing {', '.join(character.accessories)}")
        if character.preserve:
            parts.append(f"preserve: {', '.join(character.preserve)}")
        if character.avoid:
            parts.append("negative identity: " + ", ".join(character.avoid))
    else:
        parts.append("a cat")

    # Emotion / pose / composition from plan
    if item.emotion:
        parts.append(f"expression: {item.emotion}")
    if item.pose:
        parts.append(f"pose: {item.pose}")
    if item.composition:
        parts.append(f"composition: {item.composition}")
    if item.theme:
        parts.append(f"style: {item.theme}")

    # Caption as semantic intent (NOT rendered as text)
    if item.caption:
        parts.append(f"mood: {item.caption}")

    # Identity priority
    parts.append(f"identity priority: {item.identity_priority}")

    # Negative / background constraints
    parts.append("plain white background")
    parts.append("DO NOT render any text, letters, words, or captions into the image")
    parts.append("no watermark, no logo, no extra animals, no extra limbs")

    # Custom negative constraints
    if item.negative_constraints:
        parts.append("avoid: " + ", ".join(item.negative_constraints))

    return ". ".join(parts) + "."
