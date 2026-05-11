# 贡献说明

## 适合放什么

- 共享图示和图源文件
- Prompt 模板
- 工具 schema
- 评测样本和结果
- 可运行的小示例
- 参考资料笔记和索引

## 不适合放什么

- 只服务于单篇文章的临时材料
- 单篇文章专属配图
- 零散工作笔记
- 敏感数据

## 目录约定

- `assets/`：图示、截图、数据、trace
- `prompts/`：可复用 Prompt
- `tool-schemas/`：函数和协议定义
- `evals/`：评测样本、Judge、结果
- `examples/`：示例代码
- `references/`：参考资料笔记和索引

## 命名建议

尽量使用稳定、清晰的名字。

推荐格式：

`<topic>__<name>__v1.<ext>`

例如：

- `agent-loop__overview__v1.drawio`
- `judge-customer-support__rubric__v2.md`
- `tool-router__schema__v1.json`

## 几条简单规则

- 能保留图源就不要只留导出图
- 示例数据优先使用清洗过的数据
- 不要提交密钥、账号数据或私密日志
- 示例尽量小而清楚
- 同一份资产不要在多个地方重复保存
