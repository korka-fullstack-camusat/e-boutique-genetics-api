import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

BREVO_API_KEY  = os.getenv("BREVO_API_KEY", "")
SENDER_EMAIL   = os.getenv("BREVO_SENDER_EMAIL", "")
SENDER_NAME    = os.getenv("BREVO_SENDER_NAME", "E-commerce")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL", "")
# Adresse qui doit recevoir les notifications de nouvelles commandes
ORDERS_EMAIL   = os.getenv("ORDERS_NOTIFICATION_EMAIL", "market@groupegenetics.com")
_BREVO_URL     = "https://api.brevo.com/v3/smtp/email"

# ── Palette (matches the frontend) ────────────────────────────────────────────
C_DARK   = "#111827"   # gray-900
C_AMBER  = "#f59e0b"   # amber-500
C_AMBER2 = "#fef3c7"   # amber-100 (light bg)
C_TEXT   = "#374151"   # gray-700
C_MUTED  = "#6b7280"   # gray-500
C_BORDER = "#e5e7eb"   # gray-200
C_BG     = "#f9fafb"   # gray-50


async def _send(client: httpx.AsyncClient, to_email: str, to_name: str,
                subject: str, html: str) -> None:
    response = await client.post(
        _BREVO_URL,
        json={
            "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": html,
        },
        headers={"api-key": BREVO_API_KEY},
        timeout=10,
    )
    if response.status_code not in (200, 201):
        logger.error("Brevo %s → %s : %s", response.status_code, to_email, response.text)
    else:
        logger.info("Email envoyé → %s", to_email)


def _header(title: str, subtitle: str) -> str:
    return f"""
    <div style="background:{C_DARK};padding:32px 24px;text-align:center;border-radius:12px 12px 0 0">
      <div style="display:inline-block;background:{C_AMBER};color:{C_DARK};
                  font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                  padding:4px 14px;border-radius:20px;margin-bottom:14px">
        GROUPE GENETICS
      </div>
      <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;letter-spacing:0.5px">
        {title}
      </h1>
      <p style="color:rgba(255,255,255,0.55);margin:6px 0 0;font-size:13px">{subtitle}</p>
    </div>"""


def _footer() -> str:
    return f"""
    <div style="background:{C_DARK};padding:20px 24px;border-radius:0 0 12px 12px;text-align:center">
      <p style="color:rgba(255,255,255,0.35);margin:0;font-size:11px;letter-spacing:1px">
        © 2024 GROUPE GENETICS — Tous droits réservés
      </p>
    </div>"""


def _info_pill(label: str, value: str) -> str:
    return f"""
    <div style="display:inline-block;background:{C_BG};border:1px solid {C_BORDER};
                border-radius:8px;padding:10px 16px;margin:4px">
      <p style="margin:0;font-size:10px;color:{C_MUTED};text-transform:uppercase;
                font-weight:700;letter-spacing:1px">{label}</p>
      <p style="margin:4px 0 0;font-size:14px;color:{C_TEXT};font-weight:600">{value}</p>
    </div>"""


def _items_table(items: list, total_fmt: str) -> str:
    rows = ""
    for item in items:
        subtotal = item["price"] * item["quantity"]
        rows += f"""
        <tr>
          <td style="padding:12px 14px;border-bottom:1px solid {C_BORDER};color:{C_TEXT};font-size:14px">
            <strong>{item['product_name']}</strong>
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid {C_BORDER};
                     text-align:center;color:{C_MUTED};font-size:14px">
            × {item['quantity']}
          </td>
          <td style="padding:12px 14px;border-bottom:1px solid {C_BORDER};
                     text-align:right;color:{C_AMBER};font-weight:700;font-size:14px">
            {subtotal:,.0f} FCFA
          </td>
        </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;margin:20px 0;
                  border-radius:10px;overflow:hidden;border:1px solid {C_BORDER}">
      <thead>
        <tr style="background:{C_DARK}">
          <th style="padding:11px 14px;text-align:left;color:rgba(255,255,255,0.7);
                     font-size:11px;text-transform:uppercase;letter-spacing:1px">Produit</th>
          <th style="padding:11px 14px;text-align:center;color:rgba(255,255,255,0.7);
                     font-size:11px;text-transform:uppercase;letter-spacing:1px">Qté</th>
          <th style="padding:11px 14px;text-align:right;color:rgba(255,255,255,0.7);
                     font-size:11px;text-transform:uppercase;letter-spacing:1px">Total</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
      <tfoot>
        <tr style="background:{C_AMBER2}">
          <td colspan="2" style="padding:13px 14px;font-weight:800;font-size:14px;color:{C_DARK}">
            Total commande
          </td>
          <td style="padding:13px 14px;text-align:right;font-weight:800;
                     font-size:16px;color:{C_AMBER}">
            {total_fmt} FCFA
          </td>
        </tr>
      </tfoot>
    </table>"""


def _wrap(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{C_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
  <div style="max-width:600px;margin:32px auto;padding:0 16px">
    <div style="background:#fff;border-radius:12px;overflow:hidden;
                box-shadow:0 4px 24px rgba(0,0,0,0.08)">
      {content}
    </div>
  </div>
</body>
</html>"""


_DELIVERY_LABELS = {
    "domicile":  "🏠 Livraison à domicile",
    "retrait":   "🏪 Retrait en boutique",
    "personnel": "🚚 Livraison personnelle",
}


def _section_title(title: str) -> str:
    return f"""
    <h2 style="margin:28px 0 12px;font-size:11px;font-weight:800;color:{C_MUTED};
               text-transform:uppercase;letter-spacing:2px;border-bottom:1px solid {C_BORDER};
               padding-bottom:8px">
      {title}
    </h2>"""


def _row(label: str, value: str, bold: bool = False, color: str = "") -> str:
    val_style = f"font-weight:{'800' if bold else '500'};color:{color if color else C_TEXT}"
    return f"""
    <tr>
      <td style="padding:9px 0;font-size:13px;color:{C_MUTED};width:45%">{label}</td>
      <td style="padding:9px 0;font-size:13px;{val_style};text-align:right">{value}</td>
    </tr>"""


def _info_table(rows: list[tuple]) -> str:
    cells = "".join(_row(label, value, bold, color) for label, value, bold, color in rows)
    return f"""
    <table style="width:100%;border-collapse:collapse">
      {cells}
    </table>"""


def _choices_section(order_data: dict) -> str:
    """Bloc visuel clair des choix du client."""
    delivery_raw   = order_data.get("delivery_method") or ""
    delivery_label = _DELIVERY_LABELS.get(delivery_raw, delivery_raw or "Non précisé")
    delivery_fee   = order_data.get("delivery_fee") or 0
    fee_txt        = f"+{delivery_fee:,.0f} FCFA" if delivery_fee else "Gratuit"
    payment        = order_data.get("payment_method") or "—"

    # Icône paiement
    if "Wave" in payment:
        pay_icon = "📱"
    else:
        pay_icon = "💵"

    return f"""
    <table style="width:100%;border-collapse:collapse;margin:4px 0">
      <tr>
        <td style="padding:12px 14px;background:{C_BG};border-radius:8px 0 0 8px;
                   border:1px solid {C_BORDER};border-right:none;width:50%;vertical-align:top">
          <p style="margin:0;font-size:10px;color:{C_MUTED};text-transform:uppercase;
                    font-weight:700;letter-spacing:1px">Livraison choisie</p>
          <p style="margin:6px 0 0;font-size:14px;color:{C_DARK};font-weight:700">
            {delivery_label}
          </p>
          <p style="margin:4px 0 0;font-size:12px;color:{C_AMBER};font-weight:600">{fee_txt}</p>
        </td>
        <td style="width:8px;background:#fff"></td>
        <td style="padding:12px 14px;background:{C_BG};border-radius:0 8px 8px 0;
                   border:1px solid {C_BORDER};border-left:none;width:50%;vertical-align:top">
          <p style="margin:0;font-size:10px;color:{C_MUTED};text-transform:uppercase;
                    font-weight:700;letter-spacing:1px">Mode de paiement</p>
          <p style="margin:6px 0 0;font-size:14px;color:{C_DARK};font-weight:700">
            {pay_icon} {payment}
          </p>
        </td>
      </tr>
    </table>"""


def _financial_summary(order_data: dict) -> str:
    """Tableau récap financier complet."""
    total      = order_data["total_amount"]
    delivery   = order_data.get("delivery_fee") or 0
    subtotal   = total - delivery
    acompte    = order_data.get("acompte_amount")
    reste      = (total - acompte) if acompte else None

    rows_html = ""

    # Sous-total articles
    rows_html += f"""
    <tr>
      <td style="padding:8px 14px;font-size:13px;color:{C_MUTED}">Sous-total articles</td>
      <td style="padding:8px 14px;font-size:13px;color:{C_TEXT};font-weight:600;text-align:right">
        {subtotal:,.0f} FCFA
      </td>
    </tr>"""

    # Frais de livraison
    rows_html += f"""
    <tr>
      <td style="padding:8px 14px;font-size:13px;color:{C_MUTED}">Frais de livraison</td>
      <td style="padding:8px 14px;font-size:13px;color:{C_TEXT};font-weight:600;text-align:right">
        {"+" + f"{delivery:,.0f} FCFA" if delivery else "Gratuit"}
      </td>
    </tr>"""

    # Séparateur + Total
    rows_html += f"""
    <tr style="background:{C_AMBER2}">
      <td style="padding:12px 14px;font-size:15px;font-weight:800;color:{C_DARK}">
        Total commande
      </td>
      <td style="padding:12px 14px;font-size:15px;font-weight:800;
                 color:{C_AMBER};text-align:right">
        {total:,.0f} FCFA
      </td>
    </tr>"""

    # Acompte Wave (si applicable)
    if acompte:
        rows_html += f"""
    <tr style="background:#f0fdf4">
      <td style="padding:10px 14px;font-size:13px;color:#166534;font-weight:700">
        ✅ Acompte Wave payé
      </td>
      <td style="padding:10px 14px;font-size:13px;color:#16a34a;font-weight:800;text-align:right">
        -{acompte:,.0f} FCFA
      </td>
    </tr>
    <tr style="background:#f0fdf4">
      <td style="padding:0 14px 12px;font-size:12px;color:#166534" colspan="2">
        👉 Reste à régler à la livraison :
        <strong>{reste:,.0f} FCFA</strong>
      </td>
    </tr>"""

    return f"""
    <table style="width:100%;border-collapse:collapse;border-radius:10px;
                  overflow:hidden;border:1px solid {C_BORDER};margin:16px 0">
      <tbody>{rows_html}</tbody>
    </table>"""


# ── Email client ───────────────────────────────────────────────────────────────

def _build_client_email(order_data: dict) -> str:
    table = _items_table(order_data["items"], f"{order_data['total_amount']:,.0f}")

    body = f"""
    {_header(f"Commande #{order_data['id']} confirmée ✓", "Merci pour votre achat !")}

    <div style="padding:28px 28px 8px">

      <p style="margin:0 0 6px;font-size:15px;color:{C_TEXT}">
        Bonjour <strong style="color:{C_DARK}">{order_data['customer_name']}</strong>,
      </p>
      <p style="margin:0 0 24px;font-size:14px;color:{C_MUTED};line-height:1.6">
        Nous avons bien reçu votre commande. Voici le récapitulatif complet.
      </p>

      {_section_title("Vos informations")}
      {_info_table([
          ("Nom",       order_data['customer_name'],                   False, ""),
          ("Email",     order_data['customer_email'],                  False, ""),
          ("Téléphone", order_data.get('customer_phone') or '—',       False, ""),
          ("Adresse",   order_data.get('customer_address') or '—',     False, ""),
      ])}

      {_section_title("Vos choix")}
      {_choices_section(order_data)}

      {_section_title("Articles commandés")}
      {table}

      {_section_title("Résumé financier")}
      {_financial_summary(order_data)}

      <div style="background:{C_AMBER2};border-left:4px solid {C_AMBER};
                  border-radius:0 8px 8px 0;padding:14px 18px;margin:24px 0">
        <p style="margin:0;font-size:13px;color:{C_DARK};font-weight:700">
          📦 Votre commande est en cours de traitement.
        </p>
        <p style="margin:6px 0 0;font-size:12px;color:{C_MUTED}">
          Notre équipe vous contactera prochainement pour organiser la livraison.
        </p>
      </div>

    </div>
    {_footer()}"""

    return _wrap(body)


# ── Email admin ────────────────────────────────────────────────────────────────

def _build_admin_email(order_data: dict) -> str:
    table = _items_table(order_data["items"], f"{order_data['total_amount']:,.0f}")

    body = f"""
    {_header(f"🛒 Nouvelle commande #{order_data['id']}", f"{order_data['customer_name']} — {order_data['total_amount']:,.0f} FCFA")}

    <div style="padding:28px 28px 8px">

      {_section_title("Informations du client")}
      {_info_table([
          ("Nom complet", order_data['customer_name'],                   True,  C_DARK),
          ("Email",       order_data['customer_email'],                  False, ""),
          ("Téléphone",   order_data.get('customer_phone') or '—',       False, ""),
          ("Adresse",     order_data.get('customer_address') or '—',     False, ""),
          ("Date",        order_data.get('created_at', '—') if isinstance(order_data.get('created_at'), str)
                          else (order_data['created_at'].strftime('%d/%m/%Y %H:%M') if order_data.get('created_at') else '—'),
                          False, ""),
      ])}

      {_section_title("Choix du client")}
      {_choices_section(order_data)}

      {_section_title("Articles commandés")}
      {table}

      {_section_title("Résumé financier")}
      {_financial_summary(order_data)}

      <div style="background:{C_AMBER2};border-left:4px solid {C_AMBER};
                  border-radius:0 8px 8px 0;padding:16px 18px;margin:8px 0 28px">
        <p style="margin:0;font-size:14px;color:{C_DARK};font-weight:800">
          ⚡ Action requise
        </p>
        <p style="margin:6px 0 0;font-size:13px;color:{C_TEXT}">
          Connectez-vous à l'interface admin pour valider ou rejeter cette commande.
        </p>
      </div>

    </div>
    {_footer()}"""

    return _wrap(body)


# ── Entry point ────────────────────────────────────────────────────────────────

async def send_order_confirmation(order_data: dict) -> None:
    logger.info("Envoi emails commande #%s → %s | notif commande: %s",
                order_data["id"], order_data["customer_email"], ORDERS_EMAIL)

    client_html = _build_client_email(order_data)
    admin_html  = _build_admin_email(order_data)

    async with httpx.AsyncClient() as client:
        tasks = [
            _send(client,
                  order_data["customer_email"],
                  order_data["customer_name"],
                  f"✅ Commande #{order_data['id']} confirmée — Groupe Genetics",
                  client_html),
        ]
        if ORDERS_EMAIL:
            tasks.append(
                _send(client,
                      ORDERS_EMAIL,
                      "Groupe Genetics — Commandes",
                      f"🛒 Nouvelle commande #{order_data['id']} — {order_data['customer_name']} ({order_data['total_amount']:,.0f} FCFA)",
                      admin_html)
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error("Erreur envoi email : %s", r)
