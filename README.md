# AI Agent Public Assets Repo

这个仓库用于维护可公开发布、可复用的 `AI Agent` 系列资产。

这里适合放：

- 共享图示与可编辑源文件
- Prompt 资产
- Function Calling / MCP schema
- 评测样本、Judge 配置、公开报告
- 可运行示例
- 公开参考资料索引
- 面向公开资产的管理规范

这里不放：

- 大纲
- 私有写作规范
- 未发布或不公开的文章正文
- 文章专属配图
- 只服务于私有写作过程的内部材料

## 目录结构

```text
.
├─ README.md
├─ AGENTS.md
├─ assets/
├─ prompts/
├─ tool-schemas/
├─ evals/
├─ examples/
├─ references/
└─ editorial/
   ├─ asset-policy.md
   └─ repo-management.md
```

## 与私有仓库的关系

- 私有仓库可以引用本仓库内容
- 本仓库不依赖私有仓库
- 如果某个说明必须依赖私有大纲或私有草稿，那它不应该放在本仓库
