"""Shared Excel styling helpers."""
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEADER_BG = "1F4E78"
HEADER_FG = "FFFFFF"
UP_FILL   = "C6EFCE"
DOWN_FILL = "FFC7CE"
UP_TEXT   = "006100"
DOWN_TEXT = "9C0006"

_thin  = Side(style="thin", color="D9D9D9")
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)


def style_header(ws):
    fill = PatternFill("solid", fgColor=HEADER_BG)
    font = Font(color=HEADER_FG, bold=True)
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER
    ws.freeze_panes = ws.cell(row=2, column=1)


def autosize(ws, min_w=10, max_w=24):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        longest = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[letter].width = max(min_w, min(max_w, longest + 2))


def safe_close_excel():
    """Close any Excel process holding output files (Windows only)."""
    import subprocess, platform
    if platform.system() != "Windows":
        return
    for name in ("EXCEL", "et", "wps", "soffice"):
        subprocess.run(["taskkill", "/F", "/IM", f"{name}.exe"],
                       capture_output=True)
