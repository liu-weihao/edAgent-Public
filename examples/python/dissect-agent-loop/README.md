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

`sample_sales.csv` 使用 `UTF-8 with BOM` 保存，方便 Windows Excel 直接打开中文内容。

示例会自动为 Matplotlib 选择常见中文字体，例如 `Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`。如果生成图表仍然出现中文方块，请先在系统中安装任一中文字体，然后重新运行示例。

## 注意

这个示例会执行模型生成的 Python 代码，只用于理解 Agent 循环。生产系统必须把代码执行放进沙箱，并限制文件、网络、CPU、内存和执行时间。
