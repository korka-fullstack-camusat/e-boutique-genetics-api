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


# ── Email client ───────────────────────────────────────────────────────────────

def _build_client_email(order_data: dict) -> str:
    total_fmt = f"{order_data['total_amount']:,.0f}"
    table     = _items_table(order_data["items"], total_fmt)

    address_block = ""
    if order_data.get("customer_address"):
        address_block = _info_pill("Adresse de livraison", order_data["customer_address"])

    phone_block = ""
    if order_data.get("customer_phone"):
        phone_block = _info_pill("Téléphone", order_data["customer_phone"])

    body = f"""
    {_header(f"Commande #{order_data['id']} confirmée ✓", "Merci pour votre achat !")}

    <div style="padding:28px 28px 8px">

      <p style="margin:0 0 20px;font-size:15px;color:{C_TEXT}">
        Bonjour <strong style="color:{C_DARK}">{order_data['customer_name']}</strong>,
      </p>
      <p style="margin:0 0 24px;font-size:14px;color:{C_MUTED};line-height:1.6">
        Nous avons bien reçu votre commande. Notre équipe vous contactera
        prochainement pour organiser la livraison.
      </p>

      {table}

      <div style="margin:20px 0;line-height:2">
        {_info_pill("Mode de paiement", order_data['payment_method'])}
        {phone_block}
        {address_block}
      </div>

      <div style="background:{C_AMBER2};border-left:4px solid {C_AMBER};
                  border-radius:0 8px 8px 0;padding:14px 18px;margin:24px 0">
        <p style="margin:0;font-size:13px;color:{C_DARK};font-weight:600">
          📦 Votre commande est en cours de traitement.
        </p>
        <p style="margin:6px 0 0;font-size:12px;color:{C_MUTED}">
          Vous recevrez une notification dès qu'elle sera expédiée.
        </p>
      </div>

    </div>

    {_footer()}"""

    return _wrap(body)


# ── Email admin ────────────────────────────────────────────────────────────────

def _build_admin_email(order_data: dict) -> str:
    total_fmt = f"{order_data['total_amount']:,.0f}"
    table     = _items_table(order_data["items"], total_fmt)

    body = f"""
    {_header(f"Nouvelle commande #{order_data['id']}", "Un client vient de passer commande")}

    <div style="padding:28px 28px 8px">

      <h2 style="margin:0 0 16px;font-size:15px;color:{C_DARK};font-weight:700;
                 text-transform:uppercase;letter-spacing:0.5px">
        Informations client
      </h2>

      <div style="line-height:2">
        {_info_pill("Nom", order_data['customer_name'])}
        {_info_pill("Email", order_data['customer_email'])}
        {_info_pill("Téléphone", order_data.get('customer_phone') or '—')}
        {_info_pill("Adresse", order_data.get('customer_address') or '—')}
        {_info_pill("Paiement", order_data['payment_method'])}
      </div>

      <h2 style="margin:28px 0 4px;font-size:15px;color:{C_DARK};font-weight:700;
                 text-transform:uppercase;letter-spacing:0.5px">
        Détail de la commande
      </h2>

      {table}

      <div style="background:{C_AMBER2};border-left:4px solid {C_AMBER};
                  border-radius:0 8px 8px 0;padding:14px 18px;margin:8px 0 24px">
        <p style="margin:0;font-size:13px;color:{C_DARK};font-weight:600">
          ⚡ Action requise : traitez cette commande dans l'interface admin.
        </p>
      </div>

    </div>

    {_footer()}"""

    return _wrap(body)


# ── Entry point ────────────────────────────────────────────────────────────────

async def send_order_confirmation(order_data: dict) -> None:
    logger.info("Envoi emails commande #%s → %s | admin: %s",
                order_data["id"], order_data["customer_email"], ADMIN_EMAIL)

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
        if ADMIN_EMAIL:
            tasks.append(
                _send(client,
                      ADMIN_EMAIL,
                      "Admin Groupe Genetics",
                      f"🛒 Nouvelle commande #{order_data['id']} — {order_data['customer_name']} ({order_data['total_amount']:,.0f} FCFA)",
                      admin_html)
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error("Erreur envoi email : %s", r)
