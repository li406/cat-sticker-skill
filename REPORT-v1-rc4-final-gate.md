# CAT-STICKER-SKILL — RC4 Final Gate Report

**状态**: `READY_FOR_OWNER_REAL_WORLD_TEST`
**Commit**: `2e75577`
**Date**: 2026-09-17
**基线**: `53825b0` → `2e75577`（12 files, +278 / -76）

---

## 1. 本轮整改范围

按 `CAT-STICKER-SKILL-RC4-FINAL-GATE-FIX.md` 8 组 BLOCKER 一次性完成。未做真实 Seedream 付费调用，未读取私人猫图。

## 2. BLOCKER 逐条修复

| # | BLOCKER | 修复 | 验证 |
|---|---------|------|------|
| 1 | `approved_reference_hashes` 未持久化 | `GenerationPlan` 加 `approved_reference_hashes: Dict[str, str]`，`to_dict/load_plan` 全链路恢复；`check_ref_hashes_for_generation` 重新计算磁盘文件 SHA256 对比 | pytest 66 通过 |
| 2 | `CharacterProfile.from_dict` 只认 nested schema | 同时接受 nested（`observable_features`/`identity_constraints`）和 flat（顶层），nested 优先、flat fallback；`character_id` 缺失抛 `ValueError("invalid_input: ...")` | pytest |
| 3 | character/ref replace 跨进程不 invalidate | 加 `_invalidate_approval_for_ref` / `_invalidate_approval_for_character`，内部从磁盘 load plan 再判断；`import_character` / `add_ref` 不再依赖 `self.plan is not None` | pytest |
| 4A | Seedream 成功后立刻切 active | `StickerItem.add_version(activate=False)` 默认不切；`_post_process` 全部成功后才 `mark_active(version)` | smoke-test |
| 4B | resume 对 `processing_failed` 重调 Seedream | `execute_approved_plan` 循环开头加 local recovery：`generated`/`processing_failed` 且 raw 存在 → 直接重跑 `_post_process`，不新建 version、不调 provider | smoke-test step 12 |
| 5 | partial batch 返回 `success=True` | `success = (overall_status == "success")`，partial/failed 返回非零 | pytest |
| 6 | privacy scanner 三处漏洞 | 重写 `scanner.py`：tests/ 不降级 secret（只 allowlist 精确 `FAKE_SECRETS`）；private path 输出 `"value redacted"` 且 severity HIGH；`IMAGE_ALLOWLIST_DIRS = {"tests/public-fixtures", "assets/fixtures"}`，tracked image 不在 allowlist 报 HIGH `unexpected_tracked_media` | `privacy-check` PASS |
| 7 | 文档同步 | SKILL.md `project create <name>`；CHANGELOG 加 0.2.0 条目 | — |
| 8 | matting 双策略未落地 | `StickerPlanItem.matting_strategy` 字段持久化（默认 legacy）；`_post_process` 按策略分流（legacy: text→floodfill；precompose: floodfill→text）；新增 `matting-ab` CLI（读 `CAT_STICKER_PRIVATE_FIXTURES`，未配置则 SKIP exit 0） | pytest + CLI |
| 9 | text-adjust caption/preset 未持久化 | `recompose_text --caption` 同步更新 plan item caption 并 invalidate approval；`--preset` 持久化到 plan item.typography_preset（不 invalidate） | pytest |
| 10 | CI 缺 smoke-test | `.github/workflows/ci.yml` 加 `python -m cat_sticker_skill.cli smoke-test` 步骤到 Ubuntu + Windows matrix | CI |

## 3. 自动验证结果

| 检查 | 命令 | 结果 |
|------|------|------|
| 单元测试 | `pytest -q` | **66 passed** |
| Lint | `ruff check src/` | **All checks passed** |
| Privacy | `python -m cat_sticker_skill.cli privacy-check` | **PASS**（0 findings） |
| Smoke test | `python -m cat_sticker_skill.cli smoke-test` | **PASS**（13 步，0 付费调用） |
| Git push | `git push origin main` | `53825b0..2e75577 main -> main` |

## 4. 未做（按交接文档要求）

- 未调用真实 Seedream 付费 API
- 未读取私人猫图
- 未切换模型（仍 `doubao-seedream-4-5-251128`）
- 未做 Codex E2E 双端口测试
- 未新增 Web/GIF/第二 Provider

## 5. 主人真实世界最短测试步骤

```powershell
# 1. 拉最新代码
git pull origin main

# 2. 安装
pip install -e ".[dev]"

# 3. 设置 API key（替换为你的真实 key）
$env:ARK_API_KEY = "ark-你的key"
$env:CAT_STICKER_HOME = "$env:USERPROFILE\cat-sticker-home"

# 4. 建项目
cat-sticker project create my-cats

# 5. 加一张猫参考图（替换路径）
cat-sticker ref add ref1 --source "C:\path\to\your\cat.jpg" --project my-cats

# 6. 导入 character JSON 和 plan JSON（你之前 GPT 给的格式）
cat-sticker character import char.json --project my-cats
cat-sticker plan import plan.json --project my-cats

# 7. 批准（会显示费用预估）
cat-sticker plan approve --project my-cats

# 8. 生成（只跑 1 张验证链路）
cat-sticker generate --project my-cats

# 9. 检查输出
cat-sticker versions s001 --project my-cats

# 10. 如满意，打包
cat-sticker package --project my-cats --out .\exports
```

## 6. 主人回来后需要确认的点

1. **透明底透彻度**：legacy flood-fill 在某些背景色下仍可能留白边。如果实测发现白边明显，把 plan item 的 `matting_strategy` 改成 `"precompose"` 重跑 `text-adjust` 或重新生成对比。
2. **Banner 单独生成**：本轮未改 banner 生成逻辑（仍从首张主图 clean crop）。如果实测 banner 还是"拉伸感"，需要后续单独用 agent 生图能力做 banner，不在本轮 BLOCKER 范围。
3. **微信上传**：打包后按微信表情开放平台规格上传，主图透明 PNG、封面白底、icon 50×50 白底、横幅 750×400 无文字。

---

**最终状态**: `READY_FOR_OWNER_REAL_WORLD_TEST`
