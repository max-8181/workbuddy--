# notes/ — 跨设备续接笔记

放**项目上下文**，用来在其他客户端接着干同一个活儿，而不是从头解释一遍。

## 与 .workbuddy/memory 的区别

| | 位置 | 生命周期 | 用途 |
|---|---|---|---|
| 工作区 memory | `<工作区>/.workbuddy/memory/` | 随工作区目录，路径每台机器不同 | 当次会话的过程记录 |
| **本目录 notes/** | `workbuddy-configs/notes/` | **跟着仓库走，全设备可见** | 跨设备续接：做了什么、结论是什么、待办是什么 |

简单说：**会话结束前，把「下次开机还想拿到的东西」写进这里**。

## 命名约定

- `YYYY-MM-DD-<主题>.md` — 主续接笔记（结论 + 待办 + 其他客户端怎么继续）
- `YYYY-MM-DD-原始工作日志.md` — 当天工作区 memory 的副本，保留踩坑细节

## 同步

```bash
./sync_configs.sh push    # notes 在 workbuddy-configs/ 下，随配置一起提交推送
```

其他客户端 `git pull` 后直接在 `workbuddy-configs/notes/` 查看。
