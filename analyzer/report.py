import os
import tempfile
from datetime import datetime
from pathlib import Path


def generate_pdf_report(result: dict, filename: str) -> str | None:
    """
    解析結果をPDFレポートとして生成する
    reportlab が必要: pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        print("reportlab not installed. Skipping PDF generation.")
        return None

    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", delete=False, prefix="luau_report_"
        )
        tmp_path = tmp.name
        tmp.close()

        doc = SimpleDocTemplate(
            tmp_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=20,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#16213e"),
            spaceBefore=12,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        )
        code_style = ParagraphStyle(
            "Code",
            parent=styles["Code"],
            fontSize=8,
            textColor=colors.HexColor("#2d2d2d"),
            backColor=colors.HexColor("#f5f5f5"),
            spaceAfter=4,
        )

        story = []

        story.append(Paragraph("Luau Script Deobfuscation Report", title_style))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            body_style
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4a90d9")))
        story.append(Spacer(1, 6 * mm))

        score = result.get("obfuscation_score", 0)
        if score < 30:
            score_color = colors.green
            score_label = "低 (Low)"
        elif score < 70:
            score_color = colors.orange
            score_label = "中 (Medium)"
        else:
            score_color = colors.red
            score_label = "高 (High)"

        overview_data = [
            ["項目", "値"],
            ["ファイル名", filename],
            ["難読化スコア", f"{score}/100"],
            ["難読化レベル", score_label],
            ["解析日時", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["コード行数", str(result.get("parsed", {}).get("line_count", "N/A"))],
            ["エントロピー", f"{result.get('parsed', {}).get('entropy', 0):.3f}"],
        ]

        overview_table = Table(overview_data, colWidths=[60 * mm, 110 * mm])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a90d9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0f4ff")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 8 * mm))

        story.append(Paragraph("解析チェック項目", heading_style))
        checks = result.get("checks", {})
        check_labels = {
            "gui_tree": "GUI ツリー生成",
            "screen_gui": "ScreenGui 解析",
            "remote_event": "RemoteEvent 解析",
            "module_script": "ModuleScript 解析",
            "loadstring": "loadstring 先取得",
            "require": "require 解析",
            "ast": "AST 変換",
            "stylua": "StyLua 自動整形",
        }
        checks_data = [["チェック項目", "結果"]]
        for key, label in check_labels.items():
            val = checks.get(key, False)
            checks_data.append([label, "✓ 検出" if val else "− 未検出"])

        checks_table = Table(checks_data, colWidths=[100 * mm, 70 * mm])
        checks_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a90d9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(checks_table)
        story.append(Spacer(1, 8 * mm))

        if result.get("ai_report"):
            story.append(Paragraph("AI 解析レポート", heading_style))
            ai_text = result["ai_report"].replace("\n", "<br/>")
            story.append(Paragraph(ai_text, body_style))
            story.append(Spacer(1, 6 * mm))

        parsed = result.get("parsed", {})
        if parsed.get("remote_events"):
            story.append(Paragraph("検出された RemoteEvent", heading_style))
            for ev in parsed["remote_events"][:10]:
                story.append(Paragraph(f"• {ev}", body_style))
            story.append(Spacer(1, 4 * mm))

        if parsed.get("gui_elements"):
            story.append(Paragraph("検出された GUI 要素", heading_style))
            for el in parsed["gui_elements"][:10]:
                story.append(Paragraph(f"• {el}", body_style))
            story.append(Spacer(1, 4 * mm))

        readable = result.get("readable_code", "")
        if readable:
            story.append(Paragraph("可読化コード (先頭 50 行)", heading_style))
            lines = readable.split("\n")[:50]
            code_text = "\n".join(lines).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(f"<font name='Courier' size='7'>{code_text}</font>", code_style))

        doc.build(story)
        return tmp_path

    except Exception as e:
        print(f"PDF generation error: {e}")
        return None
