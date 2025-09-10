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
            c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, str(row["pon"]))
        c.drawString(55 * mm, y, str(row["step"]))
        c.drawRightString(105 * mm, y, f'{row["qty"]}')
        c.drawRightString(135 * mm, y, f'R {row["rate_cents"] / 100:,.2f}')
        c.drawRightString(190 * mm, y, f'R {row["amount_cents"] / 100:,.2f}')
        y -= 6 * mm

    c.showPage()
    c.save()
    return buf.getvalue()

