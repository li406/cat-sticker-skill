# cat-sticker-skill 最终收口报告

> **状态**: READY_FOR_OWNER_REAL_WORLD_TEST
> **commit**: `24fc0f5`
> **基线**: `e8eb391` → `24fc0f5`
> **日期**: 2026-09-17

---

## 1. 最新 commit SHA

`24fc0f5`（推送至 `main`）

## 2. 七类整改逐项结果

### MUST-FIX 1：CLI 跨进程工作链路
- ✅ `generate` 自动 `c.load_plan()`，新进程不再报 "No plan loaded"
- ✅ 所有业务命令统一 `--project <id>` 必填
- ✅ `project list` 调用真实 `store.list_projects()`
- ✅ `project show <name>` 正确传参
- ✅ plan approval 跨进程有效（已由 CLI E2E 验证）

### MUST-FIX 2：Reference 图片持久化
- ✅ `refs.json` 映射文件存在于 `workspace/projects/<id>/`
- ✅ `cat-sticker ref add <path> --id r1 --project <p>` 复制图片到 refs/
- ✅ `cat-sticker ref list --project <p>` 列出所有 refs
- ✅ `generate` 自动从 project refs/ 加载 bytes（无需 Python 传参）
- ✅ ref ID 走 path validation
- ✅ refs 在 repo 外，不提交真实照片

### MUST-FIX 3：Package CLI 完整
- ✅ 使用 `store.project_path()` 正确路径（不再 `Path.cwd()/workspace/`）
- ✅ banner 自动从 active clean image crop/pad 生成
- ✅ 调用 `zip_package()` 真正生成 ZIP
- ✅ ZIP 名: `<project>-wechat-static.zip`
- ✅ 主图来自 active version（已由 E2E 验证 activate v001 → package）

### MUST-FIX 4：Character Profile 接入
- ✅ `StickerPlanItem` 新增 `character_id` 字段
- ✅ Controller 从 `manifest.characters` 恢复 `CharacterProfile.from_dict()`
- ✅ `build_seedream_prompt(item, character=...)` 真正传入
- ✅ 多角色支持（不同 item 指定不同 character_id）

### MUST-FIX 5：本地文字微调
- ✅ `Controller.recompose_text(sticker_id, caption, y_offset, x_offset, font_scale)`
- ✅ 读取 active version 的 cutout.png → 重新 compose → 更新 final_240.png
- ✅ 不调用 Seedream
- ✅ 不修改 generated.png / cutout.png
- ✅ CLI: `cat-sticker text-adjust <id> --y-offset -10 --project <p>`

### SHOULD-FIX 1：Bounded retry + partial success
- ✅ Controller 层 retry loop：`for attempt in range(max_retries + 1)`
- ✅ Auth/InvalidRequest 类错误不重试
- ✅ 成功/失败分别计数
- ✅ 返回 `overall_status`: `success` / `partial` / `failed`

### SHOULD-FIX 2：Privacy scanner
- ✅ 不再跳过整个 tests/ 目录
- ✅ scanner 源码和 test fixtures 中的 fake secret 降为 MEDIUM
- ✅ 真实 HIGH secret 仍会 FAIL
- ✅ EXIF 扫描正常

### SHOULD-FIX 3：文档同步
- ✅ README 全部使用真实 CLI 语法（`project create name` 而非 `--name`）
- ✅ ref add/list、text-adjust、package 命令已写入
- ✅ 状态标注为 v1 release candidate

## 3. CLI 完整命令表

```
cat-sticker doctor
cat-sticker smoke-test
cat-sticker privacy-check
cat-sticker version

cat-sticker project create <name>
cat-sticker project list
cat-sticker project show <name>

cat-sticker ref add <path> --id <id> --project <p>
cat-sticker ref list --project <p>

cat-sticker plan show --project <p>
cat-sticker plan approve --project <p>

cat-sticker generate --project <p> [--dry-run]
cat-sticker regenerate <id> --project <p> [--dry-run]
cat-sticker versions <id> --project <p>
cat-sticker activate-version <id> <v> --project <p>
cat-sticker text-adjust <id> --project <p> [--y-offset N] [--x-offset N] [--font-scale F] [--caption TEXT]
cat-sticker resume --project <p>
cat-sticker validate --project <p>
cat-sticker package --project <p> --out <dir>
```

## 4. Reference persistence 设计

```
workspace/projects/<project_id>/
  project.json          # manifest
  plan.json             # generation plan
  refs.json             # {"r1": {"file": "refs/r1.jpg"}, ...}
  refs/
    r1.jpg              # actual image bytes
    r2.png
  stickers/
    s001/
      v001/
        generated.png   # AI clean image
        cutout.png      # transparent bg
        composed.png    # with text
        final_240.png   # resized
```

## 5. CharacterProfile → Prompt 链路

1. Agent 观察参考图 → 构造 `CharacterProfile` → 存入 `manifest.characters["cat_01"]`
2. Plan item 指定 `character_id="cat_01"`
3. Controller 生成时: `CharacterProfile.from_dict(manifest.characters["cat_01"])`
4. `build_seedream_prompt(item, character=profile)` → prompt 包含 coat_color/pattern/eye/accessories

## 6. Text local recompose 使用方法

```bash
# 调整文字位置（不重新生成 AI 图）
cat-sticker text-adjust s001 --y-offset -10 --project my-cats

# 换文字
cat-sticker text-adjust s001 --caption "蚌埠住了" --project my-cats

# 缩放字号
cat-sticker text-adjust s001 --font-scale 0.9 --project my-cats
```

效果：更新 `composed.png` 和 `final_240.png`，不动 `generated.png` 和 `cutout.png`。

## 7. Retry 实际语义

- Provider 内部 `max_retries=0`（无隐藏重试）
- Controller 层 retry loop：最多 `1 + CAT_STICKER_MAX_RETRIES` 次尝试
- 网络/超时/5xx → 重试
- 400/401/403/policy → 立即停止
- 每个 attempt 都计入 `ledger.requests_sent`
- 返回 `overall_status`: success / partial / failed

## 8. pytest 结果

```
66 passed, 0 failed, 0 skipped, 6 warnings
```

## 9. CLI mock E2E

**PASS** — 完整流程：project create → ref add → build plan → plan approve → generate → regenerate → activate → text-adjust → package → ZIP 验证 → resume

## 10. GitHub Actions

- ubuntu-latest × Python 3.11: 已配置（Noto CJK 字体）
- ubuntu-latest × Python 3.12: 已配置
- windows-latest × Python 3.11: 已配置
- 推送后 CI 自动运行

## 11. privacy-check

**PASS** — 无 HIGH 级别 secret

## 12. Package 输出文件清单

```
<project>-wechat-static/
  stickers/
    001.png             # 主图 240x240 透明底
  cover.png             # 封面 240x240 白底
  icon.png              # 图标 50x50 白底
  banner.png            # 横幅 750x400 无文字
  validation-report.json
  README.txt
<project>-wechat-static.zip  # 可上传微信
```

## 13. ZIP 路径及解压验证

E2E 测试已验证 ZIP 存在且可解压，内含 stickers/ 目录。

## 14. 新增真实 Seedream 请求数

**0**

## 15. 私人猫图读取/提交数

**0**

## 16. 尚未完成内容

仅以下为 Owner real-world test 类：
- 豆包真实 Agent 使用
- 私人猫图生成质量
- Seedream 真实出图效果
- 抠图猫毛边缘 A/B
- 微信开放平台实际上传

## 17. AWAITING_OWNER_TEST

- 豆包办公新会话是否自动发现 SKILL.md
- 真实猫照片 → Character Profile 准确性
- Seedream 生成是否像原猫
- 多角度 reference 是否提升一致性
- 抠图边缘质量
- 文字排版视觉
- 单张 regenerate / rollback
- 微信最终 package 上传审核

---

**READY_FOR_OWNER_REAL_WORLD_TEST**
