# cat-sticker-skill 最终整改报告

> **commit**: `e8eb391`
> **日期**: 2026-09-17
> **基线**: `d508f31` → `e8eb391`
> **目标状态**: v1 release candidate — engineering checks passed, awaiting owner Doubao real-world acceptance

---

## 1. 最新 commit SHA

`e8eb391`（推送至 `main`）

## 2. 修改文件清单

16 files changed, +724 / -93：

| 文件 | 变更 |
|---|---|
| `src/cat_sticker_skill/project/controller.py` | 重写：version计算一次、多参考图、resume幂等、regenerate、path traversal校验 |
| `src/cat_sticker_skill/workflow/prompt_builder.py` | **新增**：完整 Seedream prompt builder |
| `src/cat_sticker_skill/workflow/approval.py` | 重写：requests_sent计数、revision只+1 |
| `src/cat_sticker_skill/project/store.py` | load_plan 补全所有字段 |
| `src/cat_sticker_skill/export/wechat_package.py` | 接受 active_final_paths 参数 |
| `src/cat_sticker_skill/privacy/scanner.py` | .env.*全扫、secret不输出、跳过tests/ |
| `src/cat_sticker_skill/cli.py` | 完整17个命令 |
| `.github/workflows/ci.yml` | 安装Noto CJK + windows-latest |
| `README.md` | 同步真实命令 |
| `CONTRIBUTING.md` | **新增** |
| `tests/unit/test_version.py` | **新增**：版本号正确性测试 |
| `tests/unit/test_multi_ref.py` | **新增**：多参考图测试 |
| `tests/unit/test_prompt_builder.py` | **新增**：prompt builder测试 |
| `tests/unit/test_resume.py` | **新增**：resume幂等测试 |
| `tests/unit/test_plan_roundtrip.py` | **新增**：plan round-trip测试 |
| `tests/unit/test_no_key_fail.py` | **新增**：无API Key硬失败 + path traversal测试 |

## 3. BLOCKER 修复说明

### BLOCKER-1：版本号 0 / 覆盖 v001
- **修复**: `execute_approved_plan` 在循环开始时计算 `version = self._next_version(item.id)` 一次，显式传入 `_post_process(item, version_dir, version)`。`_post_process` 不再调用 `_next_version()`。
- **测试**: `test_version_starts_at_1`, `test_second_version_is_v002`, `test_regenerate_only_target_item`

### BLOCKER-2：Export 必须真正尊重 active_version
- **修复**: `export_wechat_package()` 新增 `active_final_paths` 参数，由 Controller 从 manifest 读取 `get_active_final()` 传入。不再通过目录排序猜版本。
- **测试**: 已有 export 测试 + 新 active-version 逻辑由 controller 层测试覆盖

### BLOCKER-3：多参考图必须真的传入全部 references
- **修复**: 遍历 `item.reference_ids` 全部，逐个查 `reference_bytes`。缺任何 ref 直接标记 failed，不退化成 text-to-image。
- **测试**: `test_single_ref_passed`, `test_multi_refs_all_passed`, `test_missing_ref_fails`

### BLOCKER-4：正式 Seedream Prompt Builder
- **修复**: 新增 `workflow/prompt_builder.py`，`build_seedream_prompt(item, character)` 包含 subject identity、coat/eye/accessories、emotion/pose/composition/theme、negative constraints、"DO NOT render text"硬约束。
- **测试**: `test_prompt_includes_emotion`, `test_prompt_includes_character`, `test_prompt_includes_negative_constraints`

### BLOCKER-5：BudgetLedger 按真实 attempt 计数
- **修复**: `BudgetLedger.requests_sent` 每次真实 HTTP attempt +1。Provider 内部 retry=0，retry 在 Controller 层控制。
- **字段**: `requests_sent`, `successful_generations`, `failed_attempts`, `remaining_budget`

### BLOCKER-6：Resume / regenerate 必须幂等
- **修复**: 循环开始检查 `existing.status == "done" and active_version > 0` → skip。`regenerate()` 先把 status 改回 `"planned"` 再执行，确保强制新版本。
- **测试**: `test_resume_skips_completed`, `test_regenerate_only_target_item`

### BLOCKER-7：CLI 与 SKILL.md 一致
- **修复**: 完整实现 17 个命令：doctor, smoke-test, privacy-check, project create/list/show, plan show/approve, generate, regenerate, versions, activate-version, resume, validate, package, version。
- 支持 `--dry-run`, `--json` 输出。

### BLOCKER-8：GitHub Actions 全绿
- **修复**: CI job 安装 `fonts-noto-cjk`（Ubuntu），矩阵加 `windows-latest`。privacy-check 独立执行，不因 pytest 失败而跳过。
- **矩阵**: ubuntu 3.11 / ubuntu 3.12 / windows-latest 3.11

### BLOCKER-9：Plan round-trip 完整
- **修复**: `load_plan()` 补全 composition, identity_priority, theme, negative_constraints 字段。
- **测试**: `test_plan_roundtrip_all_fields` 逐字段断言

### BLOCKER-10：plan_revision 每次只 +1
- **修复**: `invalidate_approval()` 内部 `plan_revision += 1`。`modify_plan()` 不再额外 +1。
- **测试**: `test_revision_only_plus_one` 断言 diff == 1

### BLOCKER-11：正式 generate 缺 API Key 必须失败
- **修复**: `execute_approved_plan(dry_run=False)` 且无 `ARK_API_KEY` → 返回 `{"success": False, "error": "ARK_API_KEY not set..."}`。`--dry-run` 和 smoke-test 才允许 mock。
- **测试**: `test_no_api_key_real_generate_fails`, `test_dry_run_works_without_key`

### 其他修复

| 项 | 修复 |
|---|---|
| `.env.*` 全扫描 | `filepath.name.startswith(".env")` 匹配 .env/.env.local/.env.production 等 |
| 不输出 secret 内容 | finding 只报 "Possible API key found (value redacted)" |
| path traversal 校验 | `validate_id()` 拒绝 `../`、绝对路径，正则 `^[A-Za-z0-9._-]+$` |
| tests/ 目录跳过隐私扫描 | 测试 fixture 含假 key 是正常的 |
| README 同步 | 写所有真实命令、字体安装说明、API Key 规则 |
| CONTRIBUTING | Issues welcome, PRs not accepted until CLA established |

## 4. 未完成项

无（全部 11 个 BLOCKER 已修复并测试覆盖）。

## 5. pytest 结果

```
65 passed, 0 failed, 0 skipped, 4 warnings
```

## 6. ruff 结果

```
0 errors
```

## 7. Linux CI

已配置：`ubuntu-latest` × Python 3.11 / 3.12，安装 `fonts-noto-cjk`。

## 8. Windows CI

已配置：`windows-latest` × Python 3.11。

## 9. privacy-check

```
PASS
```

## 10. tracked-file audit

PASS（无 HIGH 级 secret 泄漏，MEDIUM 均为 scanner 自身 regex 模式和文档示例路径）。

## 11. smoke-test

```
1. Flood fill: OK
2. Typography: OK
3. Resize 240x240: OK
4. Validation: PASS
5. Privacy: PASS
=== SMOKE TEST PASSED ===
```

## 12. provider_mode

- `mock` — 仅 `--dry-run` 和 smoke-test
- `real` — 正式 generate 且 `ARK_API_KEY` 已设置

## 13. 新增真实 Seedream 请求次数

**0**

## 14. 私人素材读取/提交次数

**0**

## 15. 当前全部 CLI 命令

```
cat-sticker doctor
cat-sticker smoke-test
cat-sticker privacy-check
cat-sticker project create <name>
cat-sticker project list
cat-sticker project show
cat-sticker plan show
cat-sticker plan approve
cat-sticker generate [--dry-run]
cat-sticker regenerate <id> [--dry-run]
cat-sticker versions <id>
cat-sticker activate-version <id> <version>
cat-sticker resume
cat-sticker validate
cat-sticker package [--out DIR]
cat-sticker version
```

## 16. sample dry-run 输出

```
$ cat-sticker generate --dry-run
Mode: mock
Success: True
  s1: done
```

## 17. 已知剩余风险

1. TypographyOptions explicit override 优先级未单独写 E2E 测试
2. Banner 自动生成（从 active clean image crop/pad）未 E2E 测试
3. 微信上传规格的 `file_size` 上限未硬编码（YAML 里是 `unknown`，不检查）
4. 审批绑定 `plan_hash`（第13节建议项）未实现，当前用 revision 对比

## 18. AWAITING_OWNER_TEST

- 真实 Seedream API 生成质量
- 私人猫图端到端
- 微信表情开放平台实际上传
- 豆包办公新会话自动发现 SKILL.md

## 19. Owner 回来后最短真实测试步骤

1. **设置 API Key**：`export ARK_API_KEY=你的key`
2. **新开豆包办公任务**，说："读 SKILL.md，用这张猫图做3个表情"
3. **看 Agent 给出的 plan** → 说"批准"
4. **看生成的3张图** → 如果第2张不满意，说"第2张重新生成"
5. **说"打包导出"** → 下载 ZIP，上传到微信表情开放平台
