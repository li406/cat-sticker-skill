# Project Operating Manual

## 每次工作

### 1. Restore

读取长期规则和四层文件。

### 2. Orient

回答：

- 我们为什么做这个产品？
- 当前在哪个 Stage？
- 当前 Stage 完成后用户能多做什么？
- 本次任务直接服务哪个验收项？

### 3. Execute

只执行 Current Stage。

新问题先分类，不自动扩大 Scope。

### 4. Verify

运行与当前修改直接相关的：

- tests
- build
- lint/typecheck
- 必要的用户流程验证

不要默认要求全项目“零问题”。

### 5. Report

用 Owner 能理解的格式：

```text
完成了什么：
当前 Stage 前进了什么：
验证结果：
发现的 Blocker：
新增 Backlog：
需要 Owner 实际测试什么：
```

### 6. Persist

会影响未来的信息必须落盘。

聊天本身不是长期状态。

### 7. Commit

有意义、已验证的切片再 commit/push。

---

# 阶段完成流程

1. 技术验证通过
2. Owner 按 CURRENT-STAGE 实际验收
3. 确认无 Blocker
4. Important / Polish 进入 Backlog
5. ROADMAP 标记 Stage done
6. 定义下一 Stage
7. commit/push
8. 建议开启干净新会话

---

# 禁止的循环

```text
实现
→ 开放式 Review
→ 修小问题
→ 再开放式 Review
→ 又修小问题
→ 无限循环
```

正确：

```text
实现 Current Stage
→ 检查 Blocker
→ Owner 验收
→ 无 Blocker
→ Stage Done
```

---

# 重大决策

如果出现昂贵、不可逆或跨多个 Stage 的决定，可写入：

`docs/decisions/`

例如：

- 更换核心存储
- 改变生产权威
- 大型架构替换
- 安全模型改变

不要为普通实现细节建立 ADR。
