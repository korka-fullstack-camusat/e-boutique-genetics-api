from datetime import datetime
from fpdf import FPDF

# Couleurs (R, G, B)
C_GOLD   = (201, 162, 39)
C_DARK   = (17,  24,  39)
C_GRAY   = (107, 114, 128)
C_BORDER = (229, 231, 235)
C_AMBER2 = (254, 243, 199)
C_ORANGE = (234, 88,  12)
C_PURPLE = (91,  33,  182)
C_GREEN  = (21,  128, 61)
C_GREENBG = (240, 253, 244)
C_ORANGEBG = (255, 247, 237)


def _fmt_num(value: float) -> str:
    """Format number with space as thousands separator (French style)."""
    return f"{value:,.0f}".replace(",", " ")


def _invoice_num_from(order_data: dict) -> str:
    created = order_data.get("created_at")
    if hasattr(created, "year"):
        year = created.year
    elif isinstance(created, str):
        try:
            year = datetime.fromisoformat(created).year
        except Exception:
            year = datetime.now().year
    else:
        year = datetime.now().year
    num = str(order_data["id"]).zfill(3)
    acompte = order_data.get("acompte_amount") or 0
    return f"AC-{year}-{num}" if acompte > 0 else f"FA-{year}-{num}"


def generate_invoice_pdf(order_data: dict) -> bytes:
    inv_num     = _invoice_num_from(order_data)
    is_acompte  = (order_data.get("acompte_amount") or 0) > 0
    acompte     = float(order_data.get("acompte_amount") or 0)
    total       = float(order_data["total_amount"])
    solde       = total - acompte
    inv_type    = "Facture d'Acompte" if is_acompte else "Facture"

    created = order_data.get("created_at")
    if hasattr(created, "strftime"):
        date_str = created.strftime("%d/%m/%Y")
    elif isinstance(created, str):
        try:
            date_str = datetime.fromisoformat(created).strftime("%d/%m/%Y")
        except Exception:
            date_str = created[:10]
    else:
        date_str = datetime.now().strftime("%d/%m/%Y")

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── En-tête société ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*C_DARK)
    pdf.cell(0, 8, "GLOBAL ENERGIES AND IT", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 5, "ZAC MBAO, ROND-POINT SIPRES", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Tel : +221 78 879 00 00   RC : SN.DKR.2025.B.22955   NINEA : 012204559",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_draw_color(*C_GOLD)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # ── Titre facture ────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*C_GOLD)
    pdf.cell(0, 10, f"{inv_type} {inv_num}", new_x="LMARGIN", new_y="NEXT")

    badge_color = C_ORANGE if is_acompte else C_GREEN
    badge_label = "[ ACOMPTE ]" if is_acompte else "[ SOLDE ]"
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*badge_color)
    pdf.cell(0, 6, badge_label, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Grille infos (2 colonnes) ────────────────────────────────────────────
    col = 88

    def label(txt: str) -> None:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(col, 5, txt.upper())

    def value(txt: str, ln: bool = False) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_DARK)
        if ln:
            pdf.cell(col, 6, txt, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(col, 6, txt)

    label("Date"); label("Client"); pdf.ln()
    value(date_str); value(order_data["customer_name"], ln=True)

    label("Reference"); label("Email"); pdf.ln()
    value(inv_num); value(order_data.get("customer_email") or "-", ln=True)

    label("Mode de paiement"); label("Telephone"); pdf.ln()
    value(order_data.get("payment_method") or "-")
    value(order_data.get("customer_phone") or "-", ln=True)

    pdf.ln(6)

    # ── Tableau articles ─────────────────────────────────────────────────────
    col_w = [88, 18, 37, 37]
    headers = ["Description", "Qte", "Prix unitaire", "Montant"]
    aligns  = ["L", "C", "R", "R"]

    # En-tête tableau
    pdf.set_fill_color(*C_DARK)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for h, w, a in zip(headers, col_w, aligns):
        pdf.cell(w, 8, h, fill=True, align=a)
    pdf.ln()

    # Lignes articles
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.3)
    alt = False
    for item in order_data["items"]:
        subtotal = float(item["price"]) * int(item["quantity"])
        pdf.set_fill_color(249, 250, 251) if alt else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*C_DARK)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(col_w[0], 8, str(item["product_name"]), border="B", fill=alt, align="L")
        pdf.cell(col_w[1], 8, str(item["quantity"]),        border="B", fill=alt, align="C")
        pdf.cell(col_w[2], 8, f"{_fmt_num(item['price'])} F", border="B", fill=alt, align="R")
        pdf.cell(col_w[3], 8, f"{_fmt_num(subtotal)} F",       border="B", fill=alt, align="R")
        pdf.ln()
        alt = not alt

    pdf.ln(3)

    # ── Totaux ───────────────────────────────────────────────────────────────
    offset_x = 15 + col_w[0] + col_w[1]   # aligné sur les colonnes prix
    lbl_w    = col_w[2]
    val_w    = col_w[3]

    def total_row(lbl: str, val: str, lbl_c=C_DARK, val_c=C_GOLD,
                  fill_c=None, bold: bool = True) -> None:
        pdf.set_x(offset_x)
        if fill_c:
            pdf.set_fill_color(*fill_c)
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.set_text_color(*lbl_c)
        pdf.cell(lbl_w, 8, lbl, fill=bool(fill_c), align="L")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*val_c)
        pdf.cell(val_w, 8, val, fill=bool(fill_c), align="R")
        pdf.ln()

    if is_acompte:
        total_row("Total commande",    f"{_fmt_num(total)} F",
                  C_DARK, C_GOLD, C_AMBER2)
        total_row("Acompte recu (Wave)", f"-{_fmt_num(acompte)} F",
                  C_PURPLE, C_PURPLE)
        total_row("SOLDE RESTANT DU",  f"{_fmt_num(solde)} F",
                  C_ORANGE, C_ORANGE, C_ORANGEBG)
    else:
        total_row("Total regle",       f"{_fmt_num(total)} F",
                  C_GREEN, C_GREEN, C_GREENBG)

    pdf.ln(6)

    # ── Conditions ───────────────────────────────────────────────────────────
    cond = (
        f"Acompte de {_fmt_num(acompte)} F recu. Solde de {_fmt_num(solde)} F du a la livraison."
        if is_acompte
        else "100% a la commande. Paiement integral recu."
    )
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 5, f"Ref. paiement : {inv_num}   |   Condition : {cond}",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    # ── Pied de page ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 4, "admin@groupegenetics.com  |  www.groupegenetics.com",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 4, "Global Energies and IT  -  RC : SN.DKR.2025.B.22955  -  NINEA : 012204559",
             new_x="LMARGIN", new_y="NEXT", align="C")

    return bytes(pdf.output())
