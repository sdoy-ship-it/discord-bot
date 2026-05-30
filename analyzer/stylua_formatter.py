import subprocess
import tempfile
import os
from pathlib import Path


def format_with_stylua(code: str) -> str:
    """
    StyLua がインストールされていれば使用、なければ簡易フォーマットにフォールバック
    """
    try:
        result = subprocess.run(
            ["stylua", "--check", "--"],
            input=b"",
            capture_output=True,
            timeout=5,
        )
        stylua_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        stylua_available = False

    if stylua_available:
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".lua", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                ["stylua", "--indent-type", "Spaces", "--indent-width", "4", tmp_path],
                capture_output=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    formatted = f.read()
                os.unlink(tmp_path)
                return formatted
            os.unlink(tmp_path)
        except Exception:
            pass

    return _basic_format(code)


def _basic_format(code: str) -> str:
    """StyLua が使えない場合の簡易フォーマット"""
    lines = code.split("\n")
    formatted_lines = []
    indent_level = 0
    indent_unit = "    "

    keywords_increase = {"do", "then", "else", "function", "repeat"}
    keywords_decrease = {"end", "until", "else", "elseif"}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue

        first_word = stripped.split()[0] if stripped.split() else ""

        if first_word in keywords_decrease:
            indent_level = max(0, indent_level - 1)

        formatted_lines.append(indent_unit * indent_level + stripped)

        last_word = stripped.rstrip().split()[-1] if stripped.rstrip().split() else ""
        if first_word in keywords_increase or (
            stripped.endswith("do")
            or stripped.endswith("then")
            or stripped.endswith("else")
            or (stripped.startswith("function") and stripped.endswith(")"))
        ):
            indent_level += 1

    return "\n".join(formatted_lines)
