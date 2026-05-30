import re
import os
import math
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .luau_parser import LuauParser
from .stylua_formatter import format_with_stylua

load_dotenv()

def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env の OPENAI_API_KEY が設定されていません")
    return AsyncOpenAI(api_key=api_key)


class LuauDeobfuscator:
    def __init__(self, code: str, filename: str):
        self.code = code
        self.filename = filename
        self.parser = LuauParser(code)

    async def analyze(self) -> dict:
        parsed = self.parser.parse()

        checks = {
            "gui_tree": parsed["has_gui"],
            "screen_gui": parsed["has_screen_gui"],
            "remote_event": parsed["has_remote_event"],
            "module_script": parsed["has_module_script"],
            "loadstring": parsed["has_loadstring"],
            "require": parsed["has_require"],
            "ast": True,
            "stylua": False,
        }

        readable_code = self._transform_ast(self.code, parsed)

        formatted_code = format_with_stylua(readable_code)
        if formatted_code and formatted_code != readable_code:
            readable_code = formatted_code
            checks["stylua"] = True

        score = self._calculate_obfuscation_score(parsed)

        summary = self._build_summary(parsed, score)

        ai_report = await self._get_ai_report(self.code, parsed, score)

        return {
            "obfuscation_score": score,
            "summary": summary,
            "checks": checks,
            "readable_code": readable_code,
            "ai_report": ai_report,
            "parsed": parsed,
            "filename": self.filename,
        }

    def _transform_ast(self, code: str, parsed: dict) -> str:
        result = code

        hex_pattern = re.compile(r'\\x([0-9a-fA-F]{2})')
        def hex_replace(m):
            return chr(int(m.group(1), 16))
        result = hex_pattern.sub(hex_replace, result)

        dec_pattern = re.compile(r'\\(\d{1,3})')
        def dec_replace(m):
            val = int(m.group(1))
            if 32 <= val <= 126:
                return chr(val)
            return m.group(0)
        result = dec_pattern.sub(dec_replace, result)

        result = re.sub(r'\(\s*function\s*\(\s*\)\s*', '(function() ', result)

        result = re.sub(r'\brepeat\b\s+\buntil\b\s+true\b', '', result)

        for i, var in enumerate(parsed.get("obfuscated_vars", [])):
            clean = f"var_{i}"
            result = result.replace(var, clean)

        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r'[ \t]+\n', '\n', result)

        return result

    def _calculate_obfuscation_score(self, parsed: dict) -> int:
        score = 0

        if parsed["has_loadstring"]:
            score += 25
        if parsed["hex_string_count"] > 5:
            score += 15
        elif parsed["hex_string_count"] > 0:
            score += 8
        if parsed["long_string_count"] > 3:
            score += 10
        if parsed["obfuscated_var_count"] > 10:
            score += 20
        elif parsed["obfuscated_var_count"] > 3:
            score += 10
        if parsed["entropy"] > 4.5:
            score += 15
        elif parsed["entropy"] > 3.5:
            score += 8

        lines = self.code.split("\n")
        avg_len = sum(len(l) for l in lines) / max(len(lines), 1)
        if avg_len > 500:
            score += 15
        elif avg_len > 200:
            score += 8

        return min(score, 100)

    def _build_summary(self, parsed: dict, score: int) -> str:
        parts = []
        if score < 30:
            parts.append("🟢 難読化レベル: 低")
        elif score < 70:
            parts.append("🟡 難読化レベル: 中")
        else:
            parts.append("🔴 難読化レベル: 高")

        parts.append(f"コード行数: {parsed['line_count']} 行")
        parts.append(f"エントロピー: {parsed['entropy']:.2f}")

        if parsed["has_loadstring"]:
            parts.append("⚠️ `loadstring` 使用 (動的コード実行)")
        if parsed["hex_string_count"] > 0:
            parts.append(f"16進文字列: {parsed['hex_string_count']} 個")
        if parsed["obfuscated_var_count"] > 0:
            parts.append(f"難読化変数: {parsed['obfuscated_var_count']} 個")
        if parsed["remote_events"]:
            parts.append(f"RemoteEvent: {', '.join(parsed['remote_events'][:5])}")
        if parsed["gui_elements"]:
            parts.append(f"GUI要素: {', '.join(parsed['gui_elements'][:5])}")

        return "\n".join(parts)

    async def _get_ai_report(self, code: str, parsed: dict, score: int) -> str:
        truncated = code[:4000] if len(code) > 4000 else code

        prompt = f"""あなたはRoblox Luauスクリプトの専門解析AIです。
以下の難読化されたLuauスクリプトを解析してください。

【難読化スコア】{score}/100
【検出情報】
- loadstring使用: {parsed['has_loadstring']}
- RemoteEvent: {parsed['remote_events']}
- GUI要素: {parsed['gui_elements']}
- エントロピー: {parsed['entropy']:.2f}

【コード (先頭4000文字)】
```lua
{truncated}
```

以下の形式で日本語でレポートしてください:
1. **スクリプトの目的**: このスクリプトが何をするか
2. **危険度評価**: 安全/注意/危険 + 理由
3. **難読化手法**: 使われている難読化技術
4. **検出された主要機能**: RemoteEvent呼び出し、GUI操作など
5. **推奨対処**: このスクリプトへの対応策

簡潔に200文字以内でまとめてください。"""

        try:
            c = _get_client()
            response = await c.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI解析エラー: {str(e)}"
