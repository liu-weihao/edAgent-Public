# 工单 MCP Server 示例

这是第 7 篇文章配套的最小 MCP 示例，用一个 `ops-ticket-toolbox` Server 模拟企业工单 Agent 会接触的三类外部能力：

- Knowledge：政策资源和政策检索
- Ticket：工单摘要读取和状态变更请求
- CRM：有限客户画像查询

示例刻意保持在单个 Server 内，避免把文章重点带偏到多服务部署。真实项目可以再拆成 Knowledge / Ticket / CRM 三个 MCP Server。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行 Server

进入本示例目录后运行：

```bash
python server.py
```

Server 默认使用 MCP SDK 的本地 `stdio` 传输，适合接入支持 MCP 的 Host 或调试工具。

如果你使用 MCP Inspector，可以运行：

```bash
mcp dev server.py
```

PowerShell 中也可以直接执行：

```powershell
python server.py
```

## 暴露的能力

Resource：

- `policy://shipping-delay/current`：读取当前延迟发货处理口径

Tools：

- `search_policy(query, top_k)`：从 mock 政策片段里检索处理口径
- `get_ticket(ticket_id)`：读取压缩后的安全工单摘要
- `get_customer_profile(customer_id)`：读取有限 CRM 上下文
- `request_status_change(ticket_id, target_status, reason, approval_token)`：演示低风险写入和高风险审批拦截

## 可试的样例

读取工单：

```json
{
  "ticket_id": "T-1001"
}
```

请求低风险状态变更：

```json
{
  "ticket_id": "T-1001",
  "target_status": "senior_support",
  "reason": "用户为 gold 等级，且存在多次延迟发货投诉。"
}
```

请求高风险状态变更时，不传 `approval_token` 会返回 `ApprovalRequired`：

```json
{
  "ticket_id": "T-1001",
  "target_status": "closed",
  "reason": "Agent 判断问题已解决。"
}
```

这正是示例想表达的核心边界：模型可以提出动作意图，但高风险动作必须在 Server 侧被拦截，先生成 preview，再交给人或规则审批。

## 示例边界

- 所有数据都是内存 mock 数据，不包含真实用户信息。
- `search_policy` 只是关键词匹配，不代表生产检索方案。
- `approval_token` 只用于演示审批边界，不是真实鉴权方案。
- 生产系统应在 Server 侧接入真实身份、租户、权限、审计和 trace。
