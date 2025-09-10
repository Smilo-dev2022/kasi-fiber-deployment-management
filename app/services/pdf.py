from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def render_pay_sheet_pdf(header: dict, lines: list[dict]) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = h - 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "SMME Pay Sheet")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    for k in ("SMME", "Period", "Status", "Total (ZAR)"):
        c.drawString(20 * mm, y, f"{k}: {header.get(k, '')}")
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "PON")
    c.drawString(55 * mm, y, "Step")
    c.drawString(90 * mm, y, "Qty")
    c.drawString(110 * mm, y, "Rate")
    c.drawString(140 * mm, y, "Amount")
    y -= 6 * mm
    c.setFont("Helvetica", 10)

    for row in lines:
        if y < 25 * mm:
            c.showPage()
            y = h - 20 * mm
        c.drawString(20 * mm, y, str(row["pon"]))
        c.drawString(55 * mm, y, str(row["step"]))
        c.drawRightString(105 * mm, y, f'{row["qty"]}')
        c.drawRightString(135 * mm, y, f'R {row["rate_cents"] / 100:,.2f}')
        c.drawRightString(190 * mm, y, f'R {row["amount_cents"] / 100:,.2f}')
        y -= 6 * mm

    c.showPage()
    c.save()
    return buf.getvalue()


def render_test_pack_pdf(meta: dict, sections: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Cover
    y = h - 25 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "Fiber Test Pack")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    for k in ("PON", "LinkCount", "GeneratedAt"):
        c.drawString(20 * mm, y, f"{k}: {meta.get(k, '')}")
        y -= 6 * mm
    c.showPage()

    # Sections
    def section(title: str, rows: list[dict], cols: list[str]):
        nonlocal c, w, h
        y2 = h - 20 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y2, title)
        y2 -= 8 * mm
        c.setFont("Helvetica-Bold", 9)
        x = 20 * mm
        for col in cols:
            c.drawString(x, y2, col)
            x += 40 * mm
        y2 -= 6 * mm
        c.setFont("Helvetica", 9)
        for r in rows:
            if y2 < 25 * mm:
                c.showPage()
                y2 = h - 20 * mm
            x = 20 * mm
            for col in cols:
                v = r.get(col, "")
                c.drawString(x, y2, str(v))
                x += 40 * mm
            y2 -= 6 * mm
        c.showPage()

    if sections.get("Closures"):
        section("Closures", sections["Closures"], ["Code", "GPS", "Status"]) 
    if sections.get("Trays"):
        section("Trays", sections["Trays"], ["Closure", "Tray", "Planned", "Done"]) 
    if sections.get("Splices"):
        section("Splices", sections["Splices"], ["Tray", "Core", "Loss dB", "Pass"]) 
    if sections.get("OTDR"):
        section("OTDR", sections["OTDR"], ["Link", "λ nm", "Loss dB", "Events"]) 
    if sections.get("LSPM"):
        section("LSPM", sections["LSPM"], ["Link", "λ nm", "Loss dB", "Pass"]) 
    if sections.get("Inspect"):
        section("Connector Inspection", sections["Inspect"], ["Where", "Port", "Grade", "Pass"]) 

    c.save()
    return buf.getvalue()
