# Agent Compatibility

## Status Matrix

| Capability | Implemented | Dry-Run Verified | Owner Real-World Verified |
|---|---|---|---|
| Project create/load/save | Yes | Yes | AWAITING_OWNER_TEST |
| Generation Plan | Yes | Yes | AWAITING_OWNER_TEST |
| Approval gate | Yes | Yes | AWAITING_OWNER_TEST |
| Budget/ledger | Yes | Yes | AWAITING_OWNER_TEST |
| Seedream provider | Yes | Mock only | AWAITING_OWNER_TEST |
| Flood-fill matting | Yes | Yes | AWAITING_OWNER_TEST |
| Typography | Yes | Yes | AWAITING_OWNER_TEST |
| Version management | Yes | Yes | AWAITING_OWNER_TEST |
| WeChat export | Yes | Yes | AWAITING_OWNER_TEST |
| Resume/rollback | Yes | Yes | AWAITING_OWNER_TEST |
| Privacy scanner | Yes | Yes | AWAITING_OWNER_TEST |

## Target Environment

- **Primary**: 豆包电脑版 / 豆包 App 办公任务
- **Future**: Codex (not required for v1)

## How to Load

In a new 豆包 office task, tell the Agent:
> Read the SKILL.md in this repo and follow its workflow to generate cat stickers.

## Notes

- Codex compatibility is future / not required for current v1
- Real paid Seedream calls require `ARK_API_KEY` set in environment
- Private cat photos are never stored in the repo
