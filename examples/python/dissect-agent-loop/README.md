# 数据分析 Agent 示例

这是第 3 篇文章配套的最小可运行示例，用来演示一个裸 Agent 循环：

- 模型输出下一步动作
- Python 控制器调用工具
- 工具结果作为观察返回给模型
- 循环直到输出最终答案或达到最大轮次

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置模型接口

示例使用 OpenAI-compatible Chat Completions 接口，通过环境变量配置：

```bash
export LLM_CHAT_URL="https://your-model-provider/v1/chat/completions"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="your-model-name"
```

PowerShell：

```powershell
$env:LLM_CHAT_URL="https://your-model-provider/v1/chat/completions"
$env:LLM_API_KEY="your-api-key"
$env:LLM_MODEL="your-model-name"
```

## 运行

进入本示例目录后运行：

```bash
python agent.py sample_sales.csv "找出销售额最高的品类，并生成一张图"
```

如果你在其他目录运行，请传入 `sample_sales.csv` 的绝对路径。

生成的图表会写入 `agent_outputs/`。

`run_python` 成功时会返回 `ok/result/artifacts`，失败时会返回结构化错误观察，包括 `error_type`、`error_message`、`available_columns`、`failed_code` 和 `hint`。这样模型下一轮能直接根据观察结果修正动作，而不是只看到一段杂乱 traceback。

## 在完整 Agent 流程里触发一次失败

如果想观察“工具失败 -> 返回结构化错误观察 -> Agent 根据观察结果修正动作”的完整闭环，可以故意让 Agent 先使用不存在的字段名：

```powershell
python agent.py sample_sales.csv "请先按 product_category 和 revenue 汇总销售额，如果失败，再根据观察结果修正字段名并重新分析"
```

运行过程中会先看到类似这样的失败观察：

```json
{
  "ok": false,
  "error_type": "KeyError",
  "error_message": "'product_category'",
  "failed_code": "summary = df.groupby(\"product_category\")[\"revenue\"].sum()",
  "available_columns": ["date", "category", "region", "sales_amount", "orders", "profit"],
  "hint": "代码执行失败，请根据 error_type、error_message、available_columns 和 failed_code 修正下一步动作。"
}
```

这类反馈会在下一轮重新放回 Agent 上下文。随后 Agent 应该根据 `available_columns` 改用 `category` 和 `sales_amount`，再次调用 `run_python` 完成分析。

`sample_sales.csv` 使用 `UTF-8 with BOM` 保存，方便 Windows Excel 直接打开中文内容。

示例会自动为 Matplotlib 选择常见中文字体，例如 `Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`。如果生成图表仍然出现中文方块，请先在系统中安装任一中文字体，然后重新运行示例。

## 注意

这个示例会执行模型生成的 Python 代码，只用于理解 Agent 循环。生产系统必须把代码执行放进沙箱，并限制文件、网络、CPU、内存和执行时间。
