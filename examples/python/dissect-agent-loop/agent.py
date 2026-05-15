import json
import os
import sys
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd


SYSTEM_PROMPT = """
你是一个数据分析 Agent。你必须只输出 JSON，不要输出 Markdown。

可用工具：
1. inspect_csv(): 查看 CSV 的字段、样本、缺失值和数值列统计。
2. run_python(code): 读取 CSV 为 df，并执行你提供的 Python 代码。

run_python 的执行环境里已经有 df、pd、plt、out_dir。
如果要返回文字结果，把它赋值给 result。
如果要生成图表，把图片保存到 out_dir，例如 out_dir / "chart.png"。
CSV 路径由外层控制器提供，不要编造或修改文件名。
绘图环境已经配置中文字体，可以直接使用中文标题、坐标轴和图例。

每轮只能输出以下三种 JSON 之一：
{"thought": "...", "tool": "inspect_csv", "args": {}}
{"thought": "...", "tool": "run_python", "args": {"code": "..."}}
{"thought": "...", "final": "..."}

如果观察结果里出现报错，请根据 error_type、error_message、available_columns、
failed_code 和 hint 修正下一次工具调用。
"""


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ask_llm(messages):
    body = json.dumps({
        "model": require_env("LLM_MODEL"),
        "messages": messages,
        "temperature": 0.2,
    }).encode("utf-8")

    request = urllib.request.Request(
        require_env("LLM_CHAT_URL"),
        data=body,
        headers={
            "Authorization": f"Bearer {require_env('LLM_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"]


def parse_action(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"模型没有返回 JSON：{text}")
    return json.loads(text[start:end + 1])


def configure_matplotlib_for_chinese():
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "PingFang SC",
        "Heiti SC",
        "WenQuanYi Micro Hei",
        "Arial Unicode MS",
    ]
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for name in candidates:
        if name in available_fonts:
            plt.rcParams["font.sans-serif"] = [
                name,
                *plt.rcParams.get("font.sans-serif", []),
            ]
            plt.rcParams["axes.unicode_minus"] = False
            return name

    plt.rcParams["axes.unicode_minus"] = False
    return None


def resolve_csv_path(csv_path):
    path = Path(csv_path)
    if path.is_absolute() and path.exists():
        return path

    candidates = [
        Path.cwd() / path,
        Path(__file__).parent / path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    checked = "\n".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        f"CSV file not found: {csv_path}\nChecked:\n{checked}"
    )


def inspect_csv(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    numeric = df.select_dtypes(include="number")
    numeric_summary = (
        numeric.describe().round(3).to_dict()
        if len(numeric.columns) > 0
        else {}
    )

    return {
        "ok": True,
        "shape": list(df.shape),
        "columns": list(df.columns),
        "sample_rows": df.head(5).to_dict(orient="records"),
        "missing": df.isna().sum().to_dict(),
        "numeric_summary": numeric_summary,
    }


def run_python(path, code):
    df = pd.read_csv(path, encoding="utf-8-sig")
    font_name = configure_matplotlib_for_chinese()
    out_dir = Path(__file__).parent / "agent_outputs"
    out_dir.mkdir(exist_ok=True)
    before = {item.name for item in out_dir.iterdir()}

    env = {
        "df": df,
        "pd": pd,
        "plt": plt,
        "out_dir": out_dir,
        "font_name": font_name,
    }

    try:
        exec(compile(code, "<agent-code>", "exec"), env, env)
        plt.close("all")
        created = [
            str(item)
            for item in out_dir.iterdir()
            if item.name not in before
        ]
        return {
            "ok": True,
            "result": str(env.get("result", ""))[:2000],
            "artifacts": created,
            "matplotlib_font": font_name,
        }
    except Exception as exc:
        plt.close("all")
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "failed_code": code[:2000],
            "available_columns": list(df.columns),
            "hint": (
                "代码执行失败，请根据 error_type、error_message、"
                "available_columns 和 failed_code 修正下一步动作。"
            ),
        }


def call_tool(action, csv_path):
    tool = action.get("tool")
    args = action.get("args", {})

    if tool == "inspect_csv":
        return inspect_csv(csv_path)
    if tool == "run_python":
        return run_python(csv_path, args.get("code", ""))

    return {
        "ok": False,
        "error_type": "UnknownTool",
        "error_message": f"未知工具：{tool}",
        "available_tools": ["inspect_csv", "run_python"],
        "hint": "请只调用 available_tools 中列出的工具，或在任务完成时输出 final。",
    }


def run_agent(csv_path, question, max_steps=6):
    csv_path = resolve_csv_path(csv_path)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"CSV 路径由控制器固定为：{csv_path}\n"
                f"分析任务：{question}\n"
                "你只需要选择工具和生成代码，不要在工具参数里改写 CSV 路径。"
            ),
        },
    ]

    for step in range(1, max_steps + 1):
        reply = ask_llm(messages)
        print(f"\n[step {step}] {reply}")

        try:
            action = parse_action(reply)
        except Exception as exc:
            observation = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "raw_reply": reply[:1000],
                "hint": "模型必须只返回约定 JSON，请重新输出合法动作。",
            }
        else:
            if "final" in action:
                return action["final"]
            observation = call_tool(action, csv_path)

        print("OBSERVATION:")
        print(json.dumps(observation, ensure_ascii=False, default=str, indent=2))

        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": "OBSERVATION:\n"
            + json.dumps(observation, ensure_ascii=False, default=str),
        })

    return "达到最大轮次，Agent 已停止。请缩小任务或检查工具返回。"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python agent.py <csv_path> <question>\n"
            "Example: python agent.py sample_sales.csv \"找出销售额最高的品类，并生成一张图\""
        )
        raise SystemExit(2)

    csv_path = sys.argv[1]
    question = " ".join(sys.argv[2:])
    print(run_agent(csv_path, question))
