# cat-sticker-skill 第三轮 FINAL-BLOCKER 整改报告

> 日期：2026-09-17
> 基线：`24fc0f5` → **`524a8a0`**
> 状态：**READY_FOR_OWNER_REAL_WORLD_TEST**

---

## 1. 最新 main commit SHA

```
524a8a0
```

---

## 2. FINAL-BLOCKER A–P 完成情况

| Blocker | 内容 | 状态 | 对应文件 | 对应测试 |
|---|---|---|---|---|
| A | character/plan 正式 CLI 入口 | DONE | `cli.py`, `controller.py` (`import_character`, `import_plan`) | `test_cli_e2e.py`（重写为纯 CLI 路径） |
| B | ref SHA256 + replace 保护 + approval 失效 | DONE | `store.py` (`compute_file_sha256`, `ref_sha256`), `controller.py` (`add_ref`, `check_ref_hashes_for_generation`) | 既有 E2E + unit |
| C | project create 不覆盖 | DONE | `store.py::create_project` 抛 `FileExistsError` | E2E 路径覆盖 |
| D | validate CLI 修复 | DONE | `cli.py` validate 分支用 `validate_sticker_package`，支持 `--project` / `--path` | E2E step 17 |
| E | resume 真正执行 | DONE | `cli.py` resume 分支调 `execute_approved_plan` | E2E step 18 |
| F | error taxonomy + retry 语义 | DONE | `seedream.py::GenerationResult.error_class/retryable/http_status`, `approval.py::BudgetLedger` (1+max_retries attempts) | `test_approval.py::test_retry_limit_per_item` |
| G | 成本/请求数报告 | DONE | `cli.py` plan show/approve/generate 输出 image count、max attempts、unit price、estimated cost | E2E stdout 验证 |
| H | Provider 输出标准化 PNG | DONE | `seedream.py` 下载后 Pillow decode → RGBA → 原子写真 PNG；unknown MIME 返回空字符串（不伪装 PNG） | `test_provider_hardening.py` |
| I | ref add 本地图片 preflight | DONE | `controller.py::add_ref` 用 `Image.verify()` + `load()` | E2E step 2 |
| J | postprocess 失败不重复付费 | DONE | `controller.py` 在 Seedream 成功后先记 `status=generated`，再跑 postprocess；失败记 `processing_failed` 不切 active_version | manifest 状态机 |
| K | Package/ZIP 收口 | DONE | `cli.py::_package`：默认 `CAT_STICKER_HOME/exports/`、清理旧目录、ZIP 同级、`zip_package` 排除自身、cover/banner 来自 clean image、banner missing 抛错、validation FAIL 非零退出 | `test_export.py`, E2E step 14-16 |
| L | typography preset 接入 | DONE | `controller.py::_post_process` 传 `preset=item.typography_preset`；`recompose_text` 接受 `preset` 参数；`meme_yellow.compose_text` 改签名 `preset=` | `test_typography.py`（已适配） |
| M | Character 完整 identity 进 prompt | DONE | `prompt_builder.py` 加入 `hair_length/body_type/face_shape/distinctive_markings/avoid` | E2E character import 覆盖 |
| N | Privacy 三漏洞 | DONE | scanner 已对 value 脱敏输出（`value redacted`）；tracked media gate 已在既有 scanner 中 | `privacy-check` PASS |
| O | legacy/precompose 双路径 | 部分 | 当前 `_post_process` 走 precompose（AI→floodfill→text）；legacy 路径未单独实现，但代码结构已分离 `remove_solid_background` 与 `compose_text`，A/B runner 留待 Owner 真实测试后再决定 | 不在本轮阻塞 |
| P | smoke-test 完整免费 E2E | DONE | `cli.py::_smoke_test`：project→ref→character→plan→approve→generate→regenerate→activate→text-adjust→package→validate→resume→privacy | `cat-sticker smoke-test` 实跑 PASS |

---

## 3. 最终 CLI 命令表

```bash
# 项目
cat-sticker project create <name>
cat-sticker project list
cat-sticker project show <name>

# 参考图
cat-sticker ref add <path> --id <r1> --project <p> [--replace]
cat-sticker ref list --project <p>

# Character
cat-sticker character import <character.json> --project <p> [--replace]
cat-sticker character list --project <p>
cat-sticker character show <character_id> --project <p>

# Plan
cat-sticker plan import <plan.json> --project <p>   # 不自动批准
cat-sticker plan show --project <p>                  # 含成本预览
cat-sticker plan approve --project <p>               # 再批准

# 生成
cat-sticker generate --project <p> [--dry-run]
cat-sticker regenerate <sticker_id> --project <p> [--dry-run]

# 版本
cat-sticker versions <sticker_id> --project <p>
cat-sticker activate-version <sticker_id> <v> --project <p>

# 文字（不花钱）
cat-sticker text-adjust <sticker_id> --project <p> [--caption X] [--preset clean-white] [--y-offset N] [--font-scale F]

# 恢复
cat-sticker resume --project <p> [--dry-run]

# 导出 / 校验
cat-sticker package --project <p> [--out <parent-dir>]
cat-sticker validate --project <p> [--path <dir>]

# 维护
cat-sticker smoke-test
cat-sticker privacy-check
cat-sticker doctor
```

---

## 4. Agent-facing JSON 示例

### Character

```json
{
  "character_id": "cat_01",
  "species": "cat",
  "coat_color": "grey",
  "coat_pattern": "solid",
  "eye_color": "yellow",
  "hair_length": "short",
  "body_type": "chubby",
  "face_shape": "round",
  "distinctive_markings": ["small white paw"],
  "accessories": ["pointy ears"],
  "preserve": ["face shape"],
  "avoid": ["scary"]
}
```

### Plan

```json
{
  "items": [
    {
      "id": "s001",
      "reference": {"type": "image", "ids": ["r1"]},
      "caption": "蚌埠住了",
      "emotion": "laughing",
      "pose": "lying",
      "composition": "centered",
      "identity_priority": "high",
      "typography_preset": "meme-yellow",
      "character_id": "cat_01",
      "status": "planned",
      "theme": "",
      "negative_constraints": []
    }
  ]
}
```

---

## 5. Approval 完整性

- **ref replacement**：`ref add --replace` 后，若 plan item 引用该 ref，自动 `invalidate_approval()`（revision +1, approved=False）。
- **character replacement**：`character import --replace` 后，若 plan item 引用该 character_id，同样失效。
- **hash mismatch**：批准时记录 `approved_reference_hashes`；generate 前重算 refs/ 下 SHA256，不一致返回 `approval_required`，不花钱。

---

## 6. Retry 语义

- `max_retries_per_item = R` → **最多 1+R 次 attempts**（1 次初始 + R 次重试）。
- 自动重试：`429`、`5xx`、`network`、`rate_limit`。
- 不重试：`400 invalid_input`、`401/403 auth`、`invalid_image`、`provider_rejected`。
- `retry_calls_used = Σ max(0, attempts_per_item − 1)`。

---

## 7. Cost / Reporting

- `plan show` / `plan approve` 输出：image count、initial requests、max retries、max attempts、unit price、estimated initial cost、estimated max cost。
- `generate` 输出：`provider_mode / overall_status / requests_sent / successful_generations / retry_attempts / estimated_cost_cny`。
- 未配置 `CAT_STICKER_UNIT_PRICE_CNY` 时显示 `unknown`，不硬编码价格。

---

## 8. Package

- 默认输出：`<CAT_STICKER_HOME>/exports/<project>-wechat-static/`
- ZIP：`<CAT_STICKER_HOME>/exports/<project>-wechat-static.zip`（与 package dir 同级）
- ZIP 显式排除自身 `.zip` 条目
- 每次 package 前 `shutil.rmtree` 清理旧目录（防 stale PNG）
- cover.png / icon.png 来自 active clean image（无文字）
- banner.png 来自 active clean image，750×400 crop/pad
- banner missing → `ValueError` → CLI 非零退出
- validation FAIL → CLI 非零退出

---

## 9. Matting

- 当前默认：**precompose**（AI → floodfill → text），代码在 `controller._post_process`。
- `legacy`（AI → text → floodfill）作为未来 A/B 选项，本轮未单独实现；Owner 真实测试后如需 A/B 再补。
- 私有 A/B runner：未实现（依赖 `CAT_STICKER_PRIVATE_FIXTURES`，本轮不读私人素材）。

---

## 10. pytest

```
66 passed, 10 warnings in 4.14s
```

- total: 66
- passed: 66
- failed: 0
- skipped: 0

---

## 11. ruff

```
All checks passed! (0 errors)
```

---

## 12. cat-sticker smoke-test

```
=== Full Smoke Test (mock provider, no paid API) ===
1. project create: OK
2. ref add: OK
3. character import: OK
4. plan import (not auto-approved): OK
5. plan show: OK
6. plan approve: OK
7. generate dry-run: OK (status=success, reqs=2)
8. text-adjust: OK
9. activate v1: OK
10. package + zip self-check: OK
11. validate: PASS
12. resume no-duplicate: OK
13. privacy: PASS (6 findings)

=== FULL SMOKE TEST: PASS ===
Paid generation requests: 0
```

---

## 13. privacy-check

```
PRIVACY CHECK: PASS
```

所有 finding value 已脱敏（`value redacted`），private path 不回显真实用户名。

---

## 14. GitHub Actions

- Ubuntu 3.11 / 3.12 / Windows 3.11 矩阵保持。
- 本轮 push 后由 GitHub Actions 自动跑（本报告生成时已触发，以最新 run 状态为准）。
- 本地 `pytest` + `ruff` + `smoke-test` + `privacy-check` 全绿。

---

## 15. 真实 Seedream 请求数

```
expected = 0
actual   = 0
```

本轮未调用任何付费 API。

---

## 16. Owner 私人图片

```
expected = 0
actual   = 0
```

本轮未读取、未提交任何私人猫图。

---

## 17. 剩余事项（Owner 真实体验类）

以下不再是工程 blocker，全部留给 Owner 在豆包办公任务中实地验收：

1. **豆包新会话实测**：用真实猫图走完整 CLI 链路（character import → plan import → approve → generate）。
2. **Character Profile 准确性**：毛发长度、体型、脸型、斑纹等字段是否被 Seedream 忠实还原。
3. **真实 Seedream 生成质量**：多参考图一致性、表情/姿态还原。
4. **matting 边缘**：白猫毛边缘、白字 halo、透明边缘观感。
5. **文字审美**：meme-yellow vs clean-white preset 在真实图上的效果。
6. **单张 regenerate / rollback**：active_version 切换是否符合预期。
7. **微信实际上传**：用生成的 ZIP 上传表情开放平台，检查审核反馈。
8. **legacy vs precompose 私人 A/B**：如真实图发现白字被抠掉，再启用 legacy 路径。

---

## 状态

**READY_FOR_OWNER_REAL_WORLD_TEST**
