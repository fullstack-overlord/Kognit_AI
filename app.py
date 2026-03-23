# ---------------------------------------------------------------------------------------------------------
# app.py - Kognit AI (Updated for Separate Credit & Capital CSVs, Debt Tracking & Reconciliation, Itemized Transactions in Reports & Summaries, Time-Based Financial Summaries, Smart Business Insights, Robust Credit Accounting & Reporting, Paper-to-Digital Accounting (OCR for both images and documents) and Improved Conversational Capabilities)
# ---------------------------------------------------------------------------------------------------------
import os
import json
import csv
import re
import mimetypes
from datetime import datetime, timedelta
import gradio as gr
from google import genai
from google.genai import types
from dotenv import load_dotenv
from huggingface_hub import HfApi, hf_hub_download

# --- Load environment and init clients
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- HF CONFIGURATION START:
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "fullstack-overlord/kognit_ai_data"
api = HfApi()

def sync_cloud(filename, action="push"):
    """Pulls or Pushes files to HF Dataset to ensure data persists after app restart."""
    if not HF_TOKEN or not REPO_ID:
        return
    try:
        if action == "push":
            api.upload_file(
                path_or_fileobj=filename,
                path_in_repo=filename,
                repo_id=REPO_ID,
                repo_type="dataset",
                token=HF_TOKEN
            )
        elif action == "pull":
            hf_hub_download(repo_id=REPO_ID, filename=filename, repo_type="dataset", token=HF_TOKEN, local_dir=".")
    except Exception: # as e:
        pass # print(f"Cloud sync error: {e}")
# --- HF CONFIGURATION END

# --- IDENTITY HELPER
def create_user_slug(name):
    """Turns 'Mama's Kitchen!' into 'mamas_kitchen' for safe filing."""
    if not name: return "default_user"
    return re.sub(r'[^a-z0-9]', '_', name.lower().strip())

# -----------------------------
# DATABASE & CALCULATION LOGIC
# -----------------------------

# --- CAPITAL: moved from single txt to appendable CSV
def get_capital(biz_slug):
    """
    capital is now stored (in <biz_slug>_capital.csv) as multiple rows.
    This function sums all 'amount' values and returns the total capital.
    """
    capital_file = f"{biz_slug}_capital.csv"
    sync_cloud(capital_file, action="pull")

    if not os.path.exists(capital_file):
        return 0.0

    total_capital = 0.0
    with open(capital_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                total_capital += float(row.get("amount", 0) or 0)
            except Exception:
                continue
    return total_capital

def set_capital(amount, biz_slug, description="Owner added capital"):
    """
    Appends a capital injection row instead of overwriting.
    """
    capital_file = f"{biz_slug}_capital.csv"
    sync_cloud(capital_file, action="pull")
    file_exists = os.path.isfile(capital_file)

    with open(capital_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "type", "amount", "description"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "capital_injection",
            "amount": amount,
            "description": description
        })
    sync_cloud(capital_file, action="push")

# --- LEDGER:
def save_to_ledger(rows, biz_slug):
    """
    Save cash sales / purchases / expenses to <biz_slug>_ledger.csv
    """
    db_file = f"{biz_slug}_ledger.csv"
    sync_cloud(db_file, action="pull")
    file_exists = os.path.isfile(db_file)
    with open(db_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "type", "item", "qty", "unit_price", "total"])
        if not file_exists: writer.writeheader()
        for row in rows:
            row['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(row)
    sync_cloud(db_file, action="push")

# --- CREDIT ACCOUNTING (credit sales/purchases recording)
def save_to_credit(rows, biz_slug):
    """
    Append credit-related rows (credit_sale, credit_purchase,
    payment_received, payment_made) to <biz_slug>_credit.csv
    """
    credit_file = f"{biz_slug}_credit.csv"
    sync_cloud(credit_file, action="pull")
    file_exists = os.path.isfile(credit_file)
    with open(credit_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "type", "entity_name", "item_description", "qty", "unit_price", "total", "status"])
        if not file_exists: writer.writeheader()

        for row in rows:
            r = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": row.get("type", ""),
                "entity_name": row.get("entity_name", "").strip(),
                "item_description": row.get("item_description", "") or "",
                "qty": row.get("qty", 1),
                "unit_price": row.get("unit_price", 0),
                "total": row.get("total", 0),
                "status": row.get("status", "unpaid")
            }
            writer.writerow(r)
    sync_cloud(credit_file, action="push")

# -----------------------------
#  PROFITABILITY ADVICE & ANALYSIS
# -----------------------------
def get_profitability_analysis(biz_slug):
    db_file = f"{biz_slug}_ledger.csv"
    sync_cloud(db_file, action="pull")
    if not os.path.isfile(db_file): return "No data yet to analyze."

    analysis = {}  # Structure: {item_name: {'cost': 0, 'sales': 0}}

    with open(db_file, 'r', newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = row['item'].lower().strip()
            # Defensive programming: String data treated as 0
            try:
                total = float(row['total'])
            except Exception:
                total = 0.0
            if item not in analysis: analysis[item] = {'cost': 0, 'sales': 0}

            if row['type'] == 'purchase': analysis[item]['cost'] += total
            elif row['type'] == 'sale': analysis[item]['sales'] += total

    if not analysis: return "No transactions found to analyze."

    report = "💡 **KOGNIT AI BUSINESS ADVICE**\n\n"
    best_item = None
    max_profit = -float('inf')

    for item, figures in analysis.items():
        profit = figures['sales'] - figures['cost']
        # Only analyze if we have both purchase and sale data
        if figures['cost'] > 0:
            margin = (profit / figures['cost']) * 100
            report += f"🔸 **{item.capitalize()}**: Profit ₦{profit:,.0f} ({margin:.1f}% margin)\n"
            if profit > max_profit:
                max_profit = profit
                best_item = item
        else:
            report += f"🔸 **{item.capitalize()}**: Currently in stock (No sales recorded yet).\n"

    if best_item:
        report += f"\n⭐ **Recommendation:** Your best performing item is **{best_item.upper()}**. You should consider stocking more of it to maximize your returns!"

    return report

# -----------------------------
# STATEMENT OF ACCOUNT / REPORT GENERATION
# -----------------------------
def generate_professional_report(biz_slug):
    """
    Updated generate_professional_report with robust credit/payout logic.
    - Replaces credit parsing with per-entity aggregation so the report can:
        * show "No credit purchase history" when there are no credit purchases
        * show "All supplier debts cleared" when all supplier debts are fully paid
        * list unpaid supplier debts when outstanding exists
        * show payments made itemized or suitable fallback message
        * same logic mirrored for customer credit sales & payments received
    This makes the report intelligent, adapt based on data and not just static.
    """

    db_file = f"{biz_slug}_ledger.csv"
    credit_file = f"{biz_slug}_credit.csv"
    capital_file = f"{biz_slug}_capital.csv"

    # --- Pull cloud copies
    sync_cloud(db_file, action="pull")
    sync_cloud(credit_file, action="pull")
    sync_cloud(capital_file, action="pull")

    # --- If no ledger exists at all
    if not os.path.isfile(db_file):
        return "No transactions recorded yet."

    # --- Capital (sum) and (detailed list will be read later for report)
    capital = get_capital(biz_slug)

    purchases = []
    sales = []
    other_expenses = 0.0

    # --- Ccredit data aggregates
    payments_received = 0.0
    payments_made = 0.0
    payments_received_list = []  # itemized list
    payments_made_list = []      # itemized list

    # --- Builds both full history lists and per-entity outstanding summaries:
    credit_purchase_rows = []   # all credit_purchase rows
    credit_sale_rows = []       # all credit_sale rows
    payment_made_rows = []      # all payment_made rows
    payment_received_rows = []  # all payment_received rows

    # --- Read ledger.csv
    with open(db_file, 'r', newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_str = f"{row.get('qty','')} {row.get('item','')} @ ₦{float(row.get('unit_price',0) or 0):,.0f}"
            try:
                total = float(row.get('total', 0) or 0)
            except Exception:
                total = 0.0
            if row.get('type') == 'purchase':
                purchases.append((item_str, total))
            elif row.get('type') == 'sale':
                sales.append((item_str, total))
            else:
                other_expenses += total

    # --- Read credit.csv and aggregate into structured lists for robust per-entity math
    if os.path.exists(credit_file):
        with open(credit_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r_type = (row.get("type") or "").strip()
                try:
                    total = float(row.get("total", 0) or 0)
                except Exception:
                    total = 0.0
                date = row.get("date", "")
                entity = row.get("entity_name", "").strip()
                desc = row.get("item_description", "").strip()
                status = (row.get("status") or "").lower().strip()
                try:
                    qty = int(float(row.get("qty", 1) or 1))
                except Exception:
                    qty = 1

                # Collect full rows for history & itemized payments
                if r_type == "credit_purchase":
                    credit_purchase_rows.append({
                        "date": date, "entity": entity, "desc": desc, "qty": qty,
                        "total": total, "status": status, "unit_price": row.get("unit_price", 0)
                    })

                elif r_type == "credit_sale":
                    credit_sale_rows.append({
                        "date": date, "entity": entity, "desc": desc, "qty": qty,
                        "total": total, "status": status, "unit_price": row.get("unit_price", 0)
                    })

                elif r_type == "payment_made":
                    payment_made_rows.append({
                        "date": date, "entity": entity, "desc": desc, "qty": qty,
                        "total": total, "status": status, "unit_price": row.get("unit_price", 0)
                    })
                    payments_made += total
                    payments_made_list.append((entity, desc, total, date))

                elif r_type == "payment_received":
                    payment_received_rows.append({
                        "date": date, "entity": entity, "desc": desc, "qty": qty,
                        "total": total, "status": status, "unit_price": row.get("unit_price", 0)
                    })
                    payments_received += total
                    payments_received_list.append((entity, desc, total, date))

    # -----------------------------
    #  Per-entity outstanding calculation (SUPPLIERS / CUSTOMERS)
    # -----------------------------
    # --- Build supplier map:
    supplier_map = {}
    for r in credit_purchase_rows:
        key = r["entity"].strip().lower()
        if not key:
            continue
        ent = supplier_map.setdefault(key, {"name": r["entity"], "purchases": 0.0, "payments": 0.0, "qty": 0, "first_date": r["date"], "descriptions":[]})
        ent["purchases"] += float(r["total"] or 0)
        try:
            ent["qty"] += int(r.get("qty", 1) or 0)
        except Exception:
            ent["qty"] += 0
        if r.get("date") and (not ent["first_date"] or ent["first_date"] == ""):
            ent["first_date"] = r.get("date")
        if r.get("desc"):
            ent["descriptions"].append(r.get("desc"))

    for r in payment_made_rows:
        key = r["entity"].strip().lower()
        if not key:
            continue
        ent = supplier_map.setdefault(key, {"name": r["entity"], "purchases": 0.0, "payments": 0.0, "qty": 0, "first_date": r.get("date",""), "descriptions":[]})
        ent["payments"] += float(r["total"] or 0)
        if r.get("desc"):
            ent["descriptions"].append(r.get("desc"))

    # --- Compute outstanding per supplier and prepare unpaid list
    credit_purchases_unpaid = []   # list of (display_name, outstanding_amount, first_date, description_summary)
    total_outstanding_payables = 0.0

    for k, v in supplier_map.items():
        # outstanding = total purchases - total payments for that supplier
        outstanding = float(v.get("purchases", 0.0) or 0.0) - float(v.get("payments", 0.0) or 0.0)
        # treat tiny float rounding as zero
        if abs(outstanding) > 1e-6:
            qty = int(v.get("qty", 0) or 0)
            # Derive a sensible unit_price for the summary if qty > 0, else 0
            try:
                unit_price = float(v["purchases"]) / qty if qty > 0 else 0.0
            except Exception:
                unit_price = 0.0

            credit_purchases_unpaid.append({
                "entity": v.get("name", ""),
                "total": outstanding,
                "date": v.get("first_date", ""),
                "desc": ", ".join(v.get("descriptions", [])[:2]) if v.get("descriptions") else "",
                "qty": qty,
                "unit_price": unit_price
            })
            total_outstanding_payables += outstanding

    # --- Build customer map: Mirror same logic for customers (credit sales / payments received)
    customer_map = {}
    for r in credit_sale_rows:
        key = r["entity"].strip().lower()
        if not key:
            continue
        ent = customer_map.setdefault(key, {"name": r["entity"], "sales": 0.0, "payments": 0.0, "qty": 0, "first_date": r.get("date",""), "descriptions":[]})
        ent["sales"] += float(r["total"] or 0)
        try:
            ent["qty"] += int(r.get("qty", 1) or 0)
        except Exception:
            ent["qty"] += 0
        if r.get("desc"):
            ent["descriptions"].append(r.get("desc"))

    for r in payment_received_rows:
        key = r["entity"].strip().lower()
        if not key:
            continue
        ent = customer_map.setdefault(key, {"name": r["entity"], "sales": 0.0, "payments": 0.0, "qty": 0, "first_date": r.get("date",""), "descriptions":[]})
        ent["payments"] += float(r["total"] or 0)
        if r.get("desc"):
            ent["descriptions"].append(r.get("desc"))

    # --- Compute outstanding per customer and prepare unpaid list  
    credit_sales_unpaid = []
    total_outstanding_receivables = 0.0

    for k, v in customer_map.items():
        outstanding = float(v.get("sales", 0.0) or 0.0) - float(v.get("payments", 0.0) or 0.0)
        if abs(outstanding) > 1e-6:
            qty = int(v.get("qty", 0) or 0)
            try:
                unit_price = float(v["sales"]) / qty if qty > 0 else 0.0
            except Exception:
                unit_price = 0.0

            credit_sales_unpaid.append({
                "entity": v.get("name", ""),
                "total": outstanding,
                "date": v.get("first_date", ""),
                "desc": ", ".join(v.get("descriptions", [])[:2]) if v.get("descriptions") else "",
                "qty": qty,
                "unit_price": unit_price
            })
            total_outstanding_receivables += outstanding

    # --- UPDATED CALCULATIONS
    total_expenses = sum(p[1] for p in purchases) + other_expenses + payments_made
    total_income = sum(s[1] for s in sales) + payments_received
    profit = total_income - total_expenses
    balance = (capital - total_expenses) + total_income

    # --- BUILD REPORT & STATEMENT OF ACCOUNT
    capital_entries = []
    if os.path.exists(capital_file):
        with open(capital_file, "r", newline="") as cf:
            cap_reader = csv.DictReader(cf)
            for row in cap_reader:
                desc = row.get("description", "").strip() if row.get("description") else ""
                try:
                    amt = float(row.get("amount", 0) or 0)
                except Exception:
                    amt = 0.0
                capital_entries.append((amt, desc, row.get("date", "")))

    report = "📋 **OFFICIAL STATEMENT OF ACCOUNT**\n\n"

    # CAPITAL CONTRIBUTIONS
    report += "🏦 CAPITAL CONTRIBUTIONS\n"
    if capital_entries:
        for amt, desc, date in capital_entries:
            label = desc if desc else "Capital injection"
            report += f"• ₦{amt:,.0f} — {label}\n"
    else:
        report += "• ₦0 — No capital contributions recorded yet\n"

    report += "\n-----------------------\n\n"

    # CASH PURCHASES
    report += "🛒 CASH PURCHASES\n"
    if purchases:
        report += "\n".join([f"• {p[0]}: ₦{p[1]:,.0f}" for p in purchases]) + "\n"
    else:
        report += "• No cash purchases recorded.\n"

    report += "\n\n"

    # CREDIT PURCHASES (Suppliers' Debts Unpaid)
    report += "💳 CREDIT PURCHASES (List of Suppliers' Debts)\n"
    if not credit_purchase_rows:
        # Case: No credit purchase history at all
        report += "• You haven't purchased any goods on credit, No credit purchase history.\n"
    else:
        # There is credit purchase history; all cleared or list unpaid
        if total_outstanding_payables <= 1e-6:
            # Case: All cleared (sum of purchases equals sum of payments)
            report += "• All suppliers' debts paid\n"
        else:
            # Case: Some outstanding remains; itemized list of unpaid suppliers' debts
            report += "\n".join([
            f"• {c['entity']} — {c['qty']} {c['desc']} @ ₦{float(c['unit_price']or 0):,.0f} (₦{c['total']:,.0f}) — {c['date']}"
            for c in credit_purchases_unpaid
            ]) + "\n"

    report += "\n\n"

    # PAYMENTS MADE (Suppliers' Debts Paid)
    report += "📤  PAYMENTS MADE (List of Paid Suppliers' Debts)\n"
    if payments_made_list:
        # Case: Itemized payments exist
        report += "\n".join([f"• {p[0]} — ₦{p[2]:,.0f} ({p[3]}){(' - '+p[1]) if p[1] else ''}" for p in payments_made_list]) + "\n"
    else:
        # No payments_made rows
        if not credit_purchase_rows:
            # Case: No credit purchase history at all
            report += "• No credit purchase history\n"
        else:
            # Case: There are credit purchases but nothing has been paid yet
            report += "• No supplier debt has been paid\n"

    report += "\n\n"

    # OTHER EXPENSES
    report += "⛽ OTHER EXPENSES\n"
    report += f"• ₦{other_expenses:,.0f}\n"

    report += "\n-----------------------\n\n"

    # CASH SALES
    report += "💰 CASH SALES\n"
    if sales:
        report += "\n".join([f"• {s[0]}: ₦{s[1]:,.0f}" for s in sales]) + "\n"
    else:
        report += "• No cash sales recorded.\n"

    report += "\n\n"

    # CREDIT SALES (Customers still Owing)
    report += "🧾 CREDIT SALES (List of customers' debts)\n"
    # Case: No credit sale history at all
    if not credit_sale_rows:
        report += "• You haven't sold any goods on credit, No credit sale history\n"
    else:
        # There is credit sale history; all cleared or list unpaid
        if total_outstanding_receivables <= 1e-6:
            # Case: All cleared
            report += "• All customers' debts cleared\n"
        else:
            # Case: Some outstanding remains; itemized list of unpaid customers' debts
            report += "\n".join([
            f"• {c['entity']} — {c['qty']} {c['desc']} @ ₦{float(c['unit_price']or 0):,.0f} (₦{c['total']:,.0f}) — {c['date']}"
            for c in credit_sales_unpaid
            ]) + "\n"

    report += "\n\n"

    # PAYMENTS RECEIVED (Customers Debt Payoff)
    report += "📥 PAYMENTS RECEIVED (List of Customers' Debt Payoff)\n"
    if payments_received_list:
        # Case: Itemized payments exist
        report += "\n".join([f"• {p[0]} — ₦{p[2]:,.0f} ({p[3]}){(' - '+p[1]) if p[1] else ''}" for p in payments_received_list]) + "\n"
    else:
        # No payments_received rows
        if not credit_sale_rows:
            # Case: No credit sale history at all
            report += "• No credit sale history\n"
        else:
            # Case: There are credit sales but nothing has been paid yet
            report += "• No customer has paid their debt\n"

    report += "\n-----------------------\n\n"

    # Totals & Summary
    report += "**TOTALS & SUMMARY**\n"

    report += f"📉 TOTAL EXPENSES: ₦{total_expenses:,.0f}\n"
    report += f"📈 TOTAL INCOME: ₦{total_income:,.0f}\n"
    # Use computed totals from per-entity outstanding
    report += f"💳 Total Outstanding Payables: ₦{total_outstanding_payables:,.0f}\n"
    report += f"💰 Total Outstanding Receivables: ₦{total_outstanding_receivables:,.0f}\n"
    report += f"✨ NET PROFIT: ₦{profit:,.0f}\n"
    report += f"💎 CURRENT BALANCE: ₦{balance:,.0f}\n"

    return report

# -----------------------------
# TIME-BASED FINANCIAL SUMMARIES + SMART BUSINESS INSIGHTS
# Gemini only handles intent; Python calculates and formats.
# -----------------------------

def _safe_parse_datetime(date_text):
    """
    NEW: Safely parse the timestamp stored in CSV rows.
    Your app writes dates like: YYYY-MM-DD HH:MM:SS
    """
    if not date_text:
        return None

    raw = str(date_text).strip().split(".")[0]  # remove microseconds if any

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass

    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def _get_period_bounds(period):
    """
    Convert a period name into a start/end datetime window.
    Supported periods:
      - Daily
      - Weekly
      - Monthly
    """
    now = datetime.now()
    period = (period or "monthly").lower().strip()

    if period == "daily":
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=1)
        return start_dt, end_dt

    if period == "weekly":
        # Monday 00:00 to next Monday 00:00
        start_dt = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=7)
        return start_dt, end_dt

    # monthly (default)
    start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start_dt.month == 12:
        end_dt = start_dt.replace(year=start_dt.year + 1, month=1, day=1)
    else:
        end_dt = start_dt.replace(month=start_dt.month + 1, day=1)
    return start_dt, end_dt


def _get_previous_period_bounds(period, current_start_dt):
    """
    Get the previous comparable period.
    This is used for Smart Business Insights comparison.
    This lets us compare:
      - today vs yesterday
      - this week vs last week
      - this month vs last month
      - and other specific user's request
    """
    period = (period or "monthly").lower().strip()

    if period == "daily":
        prev_start = (current_start_dt - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        prev_end = current_start_dt
        return prev_start, prev_end

    if period == "weekly":
        prev_start = (current_start_dt - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        prev_end = current_start_dt
        return prev_start, prev_end

    # monthly
    if current_start_dt.month == 1:
        prev_start = current_start_dt.replace(year=current_start_dt.year - 1, month=12, day=1)
    else:
        prev_start = current_start_dt.replace(month=current_start_dt.month - 1, day=1)
    prev_end = current_start_dt
    return prev_start, prev_end


def _aggregate_period_data(biz_slug, start_dt, end_dt):
    """
    Core engine that reads ledger.csv and credit.csv for a specific time window and computes Daily / Weekly / Monthly Financial Summaries and Smart Business Insights for:
      - cash sales
      - credit sales
      - payments received
      - cash purchases
      - other expenses
      - payments made
      - total sales recorded
      - total income collected
      - total expenses paid
      - profit
      - outstanding receivables/payables
      - top customer
      - top expense
      - counts of unpaid customers/suppliers
    """

    db_file = f"{biz_slug}_ledger.csv"
    credit_file = f"{biz_slug}_credit.csv"

    # --- pull cloud copies so we analyze the latest data
    sync_cloud(db_file, action="pull")
    sync_cloud(credit_file, action="pull")

    # --- Core totals
    cash_sales = 0.0
    credit_sales = 0.0
    payments_received = 0.0
    cash_purchases = 0.0
    other_expenses = 0.0
    payments_made = 0.0
    total_credit_purchases = 0.0

    # --- Detailed maps for smarter analytics, rankings and debt insights
    expense_map = {}            # item_name -> {"name": display_name, "total": amount}
    customer_sales_map = {}     # customer_name -> {"name": display_name, "credit_sales": amount}
    customer_payments_map = {}  # customer_name -> {"name": display_name, "payments": amount}
    supplier_purchases_map = {} # supplier_name -> {"name": display_name, "credit_purchases": amount}
    supplier_payments_map = {}  # supplier_name -> {"name": display_name, "payments": amount}

    # -----------------------------
    # Read ledger.csv (cash sales/purchases/expenses)
    # -----------------------------
    if os.path.exists(db_file):
        with open(db_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt = _safe_parse_datetime(row.get("date", ""))
                if not dt or not (start_dt <= dt < end_dt):
                    continue

                row_type = (row.get("type") or "").strip().lower()

                try:
                    total = float(row.get("total", 0) or 0)
                except Exception:
                    total = 0.0

                item_name = (row.get("item") or row_type or "Unknown").strip() or "Unknown"

                if row_type == "sale":
                    cash_sales += total

                elif row_type == "purchase":
                    cash_purchases += total
                    key = item_name.lower()
                    item_bucket = expense_map.setdefault(key, {"name": item_name, "total": 0.0})
                    item_bucket["total"] += total

                else:
                    # Any other ledger row that is non-sale/non-purchase is treated as expense category
                    other_expenses += total
                    key = item_name.lower()
                    item_bucket = expense_map.setdefault(key, {"name": item_name, "total": 0.0})
                    item_bucket["total"] += total

    # -----------------------------
    # Read credit.csv (credit sales/purchases/repayments)
    # -----------------------------
    if os.path.exists(credit_file):
        with open(credit_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt = _safe_parse_datetime(row.get("date", ""))
                if not dt or not (start_dt <= dt < end_dt):
                    continue

                row_type = (row.get("type") or "").strip().lower()
                entity_name = (row.get("entity_name") or "").strip()
                display_name = entity_name if entity_name else "Unknown"

                try:
                    total = float(row.get("total", 0) or 0)
                except Exception:
                    total = 0.0

                # Credit sales (customer owes business)
                if row_type == "credit_sale":
                    credit_sales += total
                    key = display_name.lower()
                    cust_bucket = customer_sales_map.setdefault(key, {"name": display_name, "credit_sales": 0.0})
                    cust_bucket["credit_sales"] += total

                # Payments received from customers
                elif row_type == "payment_received":
                    payments_received += total
                    key = display_name.lower()
                    pay_bucket = customer_payments_map.setdefault(key, {"name": display_name, "payments": 0.0})
                    pay_bucket["payments"] += total

                # Credit purchases (business owes supplier)
                elif row_type == "credit_purchase":
                    total_credit_purchases += total
                    key = display_name.lower()
                    supp_bucket = supplier_purchases_map.setdefault(key, {"name": display_name, "credit_purchases": 0.0})
                    supp_bucket["credit_purchases"] += total

                # Payments made to suppliers
                elif row_type == "payment_made":
                    payments_made += total
                    key = display_name.lower()
                    pay_bucket = supplier_payments_map.setdefault(key, {"name": display_name, "payments": 0.0})
                    pay_bucket["payments"] += total

    # -----------------------------
    # Per-entity outstanding calculations
    # -----------------------------
    outstanding_receivables = 0.0
    outstanding_payables = 0.0
    unpaid_customers = []
    unpaid_suppliers = []

    # --- Customers: credit sales - payments received
    all_customer_keys = set(customer_sales_map.keys()) | set(customer_payments_map.keys())
    for key in all_customer_keys:
        sales_total = customer_sales_map.get(key, {}).get("credit_sales", 0.0)
        payments_total = customer_payments_map.get(key, {}).get("payments", 0.0)
        remaining = sales_total - payments_total

        if remaining > 1e-6:
            name = customer_sales_map.get(key, customer_payments_map.get(key, {"name": key}))["name"]
            unpaid_customers.append((name, remaining))
            outstanding_receivables += remaining

    # --- Suppliers: credit purchases - payments made
    all_supplier_keys = set(supplier_purchases_map.keys()) | set(supplier_payments_map.keys())
    for key in all_supplier_keys:
        purchase_total = supplier_purchases_map.get(key, {}).get("credit_purchases", 0.0)
        payments_total = supplier_payments_map.get(key, {}).get("payments", 0.0)
        remaining = purchase_total - payments_total

        if remaining > 1e-6:
            name = supplier_purchases_map.get(key, supplier_payments_map.get(key, {"name": key}))["name"]
            unpaid_suppliers.append((name, remaining))
            outstanding_payables += remaining

    # -----------------------------
    # Cash-basis summary numbers
    # -----------------------------
    total_sales_recorded = cash_sales + credit_sales
    total_income_collected = cash_sales + payments_received
    total_expenses_paid = cash_purchases + other_expenses + payments_made
    profit_cash_basis = total_income_collected - total_expenses_paid

    # --- Top customer by credit sales
    top_customer = None
    if customer_sales_map:
        top_customer_key = max(customer_sales_map.keys(), key=lambda k: customer_sales_map[k]["credit_sales"])
        top_customer = (
            customer_sales_map[top_customer_key]["name"],
            customer_sales_map[top_customer_key]["credit_sales"]
        )

    # --- Top expense item
    top_expense = None
    if expense_map:
        top_expense_key = max(expense_map.keys(), key=lambda k: expense_map[k]["total"])
        top_expense = (
            expense_map[top_expense_key]["name"],
            expense_map[top_expense_key]["total"]
        )

    return {
        "cash_purchases": cash_purchases,
        "credit_purchases": total_credit_purchases,
        "payments_made": payments_made,
        "other_expenses": other_expenses,
        "cash_sales": cash_sales,
        "credit_sales": credit_sales,
        "payments_received": payments_received,
        "total_sales_recorded": total_sales_recorded,
        "total_income_collected": total_income_collected,
        "total_expenses_paid": total_expenses_paid,
        "profit_cash_basis": profit_cash_basis,
        "outstanding_receivables": outstanding_receivables,
        "outstanding_payables": outstanding_payables,
        "unpaid_customers_count": len(unpaid_customers),
        "unpaid_suppliers_count": len(unpaid_suppliers),
        "top_customer": top_customer,
        "top_expense": top_expense,
        "unpaid_customers": unpaid_customers,
        "unpaid_suppliers": unpaid_suppliers,
        "expense_map": expense_map,
    }

# -----------------------------
#  Generates TIME-BASED FINANCIAL SUMMARIES
# -----------------------------
def generate_period_financial_summary(biz_slug, period="monthly"):
    """
    Daily / Weekly / Monthly Financial Summary Report.

    This is the report users can ask for naturally.
    """
    period = (period or "monthly").lower().strip()
    start_dt, end_dt = _get_period_bounds(period)
    data = _aggregate_period_data(biz_slug, start_dt, end_dt)

    # --- Friendly titles and period labels
    if period == "daily":
        title = "📊 Daily Financial Summary"
        period_label = start_dt.strftime("%d %b %Y")
    elif period == "weekly":
        title = "📊 Weekly Financial Summary"
        period_label = f"{start_dt.strftime('%d %b %Y')} - {(end_dt - timedelta(seconds=1)).strftime('%d %b %Y')}"
    else:
        title = f"📊 {start_dt.strftime('%B')} Financial Summary"
        period_label = start_dt.strftime("%B %Y")

    report = f"{title}\n\n"
    report += f"📅 Period: {period_label}\n\n"

    # --- Sales / payments / expenses breakdown
    report += f"🛒 Cash Purchases: ₦{data['cash_purchases']:,.0f}\n"
    report += f"💳 Credit Purchases: ₦{data['credit_purchases']:,.0f}\n"
    report += f"📤 Payments Made: ₦{data['payments_made']:,.0f}\n"
    report += f"⛽ Other Expenses: ₦{data['other_expenses']:,.0f}\n"
    report += f"💰 Cash Sales: ₦{data['cash_sales']:,.0f}\n"
    report += f"🧾 Credit Sales: ₦{data['credit_sales']:,.0f}\n"
    report += f"📥 Payments Received: ₦{data['payments_received']:,.0f}\n"

    report += "\n-----------------------\n\n"

    # --- Totals & Summary
    report += "**TOTALS & SUMMARY**\n"

    report += f"📈 Total Sales (Cash + Credit): ₦{data['total_sales_recorded']:,.0f}\n"
    report += f"💵 Total Income Collected: ₦{data['total_income_collected']:,.0f}\n"
    report += f"📉 Total Expenses: ₦{data['total_expenses_paid']:,.0f}\n"
    report += f"✨ Profit: ₦{data['profit_cash_basis']:,.0f}\n"

    # Helpful business ranking lines
    if data["top_customer"]:
        report += f"🏆 Top Customer: {data['top_customer'][0]} — ₦{data['top_customer'][1]:,.0f}\n"
    else:
        report += "🏆 Top Customer: No credit customer activity recorded for this period.\n"

    if data["top_expense"]:
        report += f"⛽ Top Expense: {data['top_expense'][0]} — ₦{data['top_expense'][1]:,.0f}\n"
    else:
        report += "⛽ Top Expense: No expense activity recorded for this period.\n"

    report += f"💳 Total Outstanding Payables: ₦{data['outstanding_payables']:,.0f}\n"
    report += f"💰 Total Outstanding Receivables: ₦{data['outstanding_receivables']:,.0f}\n"

    return report

# -----------------------------
# Computes SMART BUSINESS INSIGHTS
# -----------------------------
def compute_smart_business_insights(biz_slug, period="weekly"):
    """
    Compare current period to previous comparable period and generate
    short, actionable business insights.
    """
    period = (period or "weekly").lower().strip()
    current_start, current_end = _get_period_bounds(period)
    previous_start, previous_end = _get_previous_period_bounds(period, current_start)

    current = _aggregate_period_data(biz_slug, current_start, current_end)
    previous = _aggregate_period_data(biz_slug, previous_start, previous_end)

    def pct_change(now, before):
        if before <= 0:
            return None
        return ((now - before) / before) * 100.0

    insights = []

    # --- Sales trend comparison
    sales_change = pct_change(current["total_sales_recorded"], previous["total_sales_recorded"])
    if sales_change is not None:
        if sales_change > 0:
            insights.append(f"📈 Sales increased by {sales_change:.1f}% compared to the previous {period}.")
        elif sales_change < 0:
            insights.append(f"📉 Sales decreased by {abs(sales_change):.1f}% compared to the previous {period}.")

    # --- Expense trend comparison
    expense_change = pct_change(current["total_expenses_paid"], previous["total_expenses_paid"])
    if expense_change is not None:
        if expense_change > 0:
            insights.append(f"⚠️ Expenses increased by {expense_change:.1f}% compared to the previous {period}.")
        elif expense_change < 0:
            insights.append(f"✅ Expenses reduced by {abs(expense_change):.1f}% compared to the previous {period}.")

    # --- Profit trend comparison
    profit_change = pct_change(current["profit_cash_basis"], previous["profit_cash_basis"])
    if profit_change is not None:
        if profit_change > 0:
            insights.append(f"✨ Profit improved by {profit_change:.1f}% compared to the previous {period}.")
        elif profit_change < 0:
            insights.append(f"⚠️ Profit dropped by {abs(profit_change):.1f}% compared to the previous {period}.")

    # --- Outstanding customer debts
    if current["outstanding_receivables"] > 0:
        insights.append(
            f"⚠️ You have {current['unpaid_customers_count']} unpaid customer debts worth ₦{current['outstanding_receivables']:,.0f}. You may want to follow up."
        )

    # --- Outstanding supplier debts
    if current["outstanding_payables"] > 0:
        insights.append(
            f"⚠️ You owe suppliers ₦{current['outstanding_payables']:,.0f} across {current['unpaid_suppliers_count']} unpaid supplier debts."
        )

    # --- Top expense trend check / unusual rise
    if current["top_expense"]:
        current_item_name = current["top_expense"][0]
        current_item_total = current["top_expense"][1]
        previous_item_total = previous["expense_map"].get(current_item_name.lower(), {}).get("total", 0.0)

        if previous_item_total > 0 and current_item_total > (previous_item_total * 1.2):
            insights.append(f"⛽ {current_item_name} costs are higher than usual compared to the previous {period}.")

    # --- If nothing triggered, return a calm status message
    if not insights:
        insights.append("✅ No major changes detected. The business looks stable for this period.")

    report = f"💡 **KOGNIT AI BUSINESS INSIGHTS ({period.upper()})**\n\n"
    report += "\n".join([f"• {item}" for item in insights])
    return report

# -----------------------------
#  AI (MASTER PROMPT) & CONTROLLER
# -----------------------------
def kognit_ai_accountant(text_input, audio_input, document_input, business_name):

    biz_slug = create_user_slug(business_name)

    try:
        
        # Gemini is the brain that handles intent and routing; Python is the calculation engine.
        # --- Financial Statements and Product Analysis & Profitability Advice
        current_report = generate_professional_report(biz_slug)
        current_advice = get_profitability_analysis(biz_slug)

        # --- Time-Based Financial Summaries
        current_daily_summary = generate_period_financial_summary(biz_slug, "daily")
        current_weekly_summary = generate_period_financial_summary(biz_slug, "weekly")
        current_monthly_summary = generate_period_financial_summary(biz_slug, "monthly")

        # --- Smart Business Insights (with trend detection and actionable advice)
        current_daily_insights = compute_smart_business_insights(biz_slug, "daily")
        current_weekly_insights = compute_smart_business_insights(biz_slug, "weekly")
        current_monthly_insights = compute_smart_business_insights(biz_slug, "monthly")


        # -----------------------------
        #  THE MASTER PROMPT
        # -----------------------------
        prompt = f"""
        You are 'Kognit AI', a Smart AI-Powered Accounting Assistant & Financial Intelligence AI for Nigerian Businesses (especially SMEs). Built by 'Ridwan Oyeniyi (fullstack_overlord)'.
        You are a Multimodal Accounting Assistant that can understand and process text inputs, voice inputs and uploaded financial documents (audio transactions, receipts, invoices, images, PDFs & txt files) to extract financial data.
        You are an expert in English, Pidgin, Yoruba, Hausa, and Igbo and you can communicate in them fluently.
        You help small business owners automate bookkeeping, track their inventory, manage debts and cash & credit accounts, track their finances (expenses/costs, sales, and profits), draft financial reports and accounting statements, draft time-based financial reports and summaries (daily, weekly and monthly reports), smart business insights (analytics + anomaly/trend detection), answer financial queries and offer personalized financial literacy coaching & interactive financial consulting, analyze profitability & financial health, and give real-time actionable insights & advice in a friendly, conversational way.

        CONTEXT FOR BUSINESS '{business_name}':
        - Current Report: {current_report}
        - Current Advice: {current_advice}

        - Daily Summary: {current_daily_summary}
        - Weekly Summary: {current_weekly_summary}
        - Monthly Summary: {current_monthly_summary}

        - Daily Insights: {current_daily_insights}
        - Weekly Insights: {current_weekly_insights}
        - Monthly Insights: {current_monthly_insights}

        YOUR TASK:
        1. If the user wants to see their profit/loss, report or 'statement of account', explain the 'Current Report' in a friendly, professional and explanatory way. DO NOT remove EMOJIS. DO NOT change the FORMAT and ORDER if the user asks for statement of account or official report. But briefly explain the generated report, the financial position and some accounting terms (like Total Outstanding Payables, Total Outstanding Receivables and other relevant terms) at the end of the report, so that Non-accounting literate users (local SMEs) can understand. If the user asks for only profit or balance or other specific financial statements, summarize the relevant sections of the 'Current Report' in an explanatory, clear and concise way.

        2. If the user requests for other specific financial statements and reports, prepare it using their business/financial data, established accounting standards & principles, and the calculations under 'generate_professional_report(biz_slug)' and other functions defined above. Explain it in a professional, clear, concise and explanatory way, ensuring to clarify any accounting terms for better understanding.

        3. If the user asks for financial advice or how the business is doing or financial health analysis, use the 'Current Advice'. DO NOT remove EMOJIS and explain in a friendly, professional and explanatory way.

        4. If the user asks for a DAILY, WEEKLY, or MONTHLY financial report or summary, use the matching summary context exactly:
            - Use 'Daily Summary' for daily requests.
            - Use 'Weekly Summary' for weekly requests.
            - Use 'Monthly Summary' for monthly requests.
        Explain the report/summary clearly, professionally, following the established accounting standards & principles, and in a way the user can easily understand.

        5. If the user asks for financial insights, analysis of business performance, Comparison of current period to previous comparable period to generate actionable business insights, comparison of the business performance/position(Sales, Expenses/Purchases, Profit/Loss) between a specific period, business insights, trends, outstanding debt warnings, comparison of performance, red flags, unusual changes, or how the business is changing over time, use the matching insights context exactly:
            - Use 'Daily Insights' for daily-period analysis.
            - Use 'Weekly Insights' for weekly-period analysis.
            - Use 'Monthly Insights' for monthly-period analysis.
        If the user does not mention a time period, use 'Weekly Insights' by default.
        Explain the insights clearly, friendly, professionally, following the established accounting standards & principles, and in a way the user can easily understand..

        6. If the user mentions starting money, capital, adding capital, received donation/funds/support from Investors/VC firms or 'investing' in my business/the shop, extract it as:
           [{{"type":"capital_injection","amount":500000,"description":"capital added"}}]

        7. If the user reports a cash sale, purchase, or expense, extract the data into this JSON format:
           [{{"type":"sale/purchase/expense","item":"name","qty":1,"unit_price":1,"total":1}}]

        8. If the user says a customer bought something (on Credit) but will pay later, record a CREDIT SALE:
           [{{"type":"credit_sale","entity_name":"customer","item_description":"item","qty":1,"unit_price":1,"total":1,"status":"unpaid"}}]

        9. If the user says they bought goods (on Credit) from a supplier but will pay later, record a CREDIT PURCHASE:
           [{{"type":"credit_purchase","entity_name":"supplier","item_description":"item","qty":1,"unit_price":1,"total":1,"status":"unpaid"}}]

        10. If a customer pays back their debt, record PAYMENT RECEIVED:
           [{{"type":"payment_received","entity_name":"customer","item_description":"debt repayment","qty":1,"unit_price":1,"total":1,"status":"paid"}}]

        11. If the business pays a supplier debt, record PAYMENT MADE:
           [{{"type":"payment_made","entity_name":"supplier","item_description":"debt repayment","qty":1,"unit_price":1,"total":1,"status":"paid"}}]

        12. When checking debts, Take Note and understand that if a credit transaction (credit sale/purchase) with status 'unpaid' later appears with THE SAME entity_name, unit_price and total but status 'paid', the debt has been settled(paidoff).

        13. ALWAYS RESPOND in THE SAME LANGUAGE or DIALECT the user used (especially Pidgin).

        14. If it's just a greeting like 'hello', 'hey', 'who are you', 'who built you', 'how far' or 'hi', respond warmly and conversationally as a Smart AI-Powered Accounting Assistant & Financial Intelligence AI, mention your name (Kognit AI) and who built you (Ridwan Oyeniyi (fullstack_overlord)).
        DON'T MENTION YOUR NAME AND YOUR CREATOR'S NAME IN EVERY RESPONSE, only when asked and in greetings. If the user is asking for help or how to use you, explain your features and capabilities in a friendly and concise way.

        15. If the user asks for a report, summary, advice, or insight and the relevant context above is available, rely on the provided context first before inventing. If something is not available in the context, prepare it using their business/financial data, following the established accounting standards & principles, and explain it professionally, concisely, honestly and clearly.
        But if the user is asking about irrelevant matters like confidential information or questions that has nothing to do with what you're built for or things that this app is not meant for, reply politely, honestly, friendly and apologize explaining you are an AI Assistant created for a purpose (mention what you are built for and what you can do), that you understand them but cannot provide answer to their request because you are not built for that.

        16. Kognit AI supports multiple input types (3 Accounting Models):
            - Text Input: Manual data entry via typing (Text-Based Accounting Model)
            - Audio Input: Voice notes & Uploaded Audio files (Voice Accounting Model)
            - Image Input: Images of receipts & invoices (OCR Paper-to-Digital Accounting Model)
            - Document Input: PDF/TXT files of receipts & invoices (OCR Paper-to-Digital Accounting Model)
        If  the user ask whether they can upload audio, image, PDF/TXT files of their receipts & invoices, respond clearly, explaining that they can use any of those supported input types.

        17. When the user uploads an audio file, interpret it as Voice Accounting and extract the relevant financial transaction(s) data from the spoken content.

        18. When the user uploads an image or document file (PDF/TXT), interpret it as Paper-to-Digital (OCR) Accounting and use OCR to scan and extract the relevant readable financial transaction(s) data from the document.

        19. If the uploaded audio or image or document (PDF/TXT) contains multiple transactions, extract all of them and RETURN ONLY JSON when the content is transactional. No other text. If the content is not clear enough to be confidently extracted, ask the user to upload a clearer document or use Text Input (to provide a text description of the transaction).

        20. IMPORTANT: If you extract any transaction, ONLY RETURN THE JSON. No other text.

        """

        contents = [prompt]
        if text_input: contents.append(text_input)
        # --- Handle Dynamic file inputs (audio, image, pdf, txt, etc.) with MIME type detection
        # --- Unified multimodal input handling
        if audio_input:
            file_path = str(audio_input).lower()
            #Default mime
            mime_type = None

            # --- AUDIO HANDLING
            if file_path.endswith(".ogg"):
                mime_type = "audio/ogg"
            elif file_path.endswith(".wav"):
                mime_type = "audio/wav"
            elif file_path.endswith(".mp3"):
                mime_type = "audio/mpeg"
            elif file_path.endswith(".m4a"):
                mime_type = "audio/mp4"
            elif file_path.endswith(".aac"):
                mime_type = "audio/aac"
            elif file_path.endswith(".amr"):
                mime_type = "audio/amr"

            if mime_type:
                with open(audio_input, "rb") as f:
                    contents.append(types.Part.from_bytes(data=f.read(), mime_type=mime_type))

        # --- IMAGES / DOCUMENT HANDLING (OCR)
        if document_input:
            file_path = str(document_input).lower()
            # Default mime
            mime_type = None

            # --- Image Handling
            if file_path.endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif file_path.endswith(".png"):
                mime_type = "image/png"
            elif file_path.endswith(".webp"):
                mime_type = "image/webp"

            # --- PDF / TXT Handling
            elif file_path.endswith(".pdf"):
                mime_type = "application/pdf"
            elif file_path.endswith(".txt"):
                mime_type = "text/plain"

            if mime_type:
                with open(document_input, "rb") as f:
                    contents.append(types.Part.from_bytes(data=f.read(), mime_type=mime_type))

        # --- GEMINI API CALL
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="HIGH",
                ),
                temperature=1.0
            )
        )
        response_text = (response.text or "").strip()

        # --- JSON EXTRACTION HANDLING & ROUTING LOGIC
        if response_text.startswith("[") and response_text.endswith("]"):
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            entries = json.loads(clean_json)

            for entry in entries:
                # --- Route transaction types to the correct handler
                t = entry.get('type', '').lower()

                if t == 'capital_injection':
                    # Append capital injection (history)
                    set_capital(entry.get('amount', 0), biz_slug, entry.get('description', 'capital injection'))

                elif t in ('credit_sale', 'credit_purchase'):

                    normalized = {
                        "type": t,
                        "entity_name": entry.get("entity_name", ""),
                        "item_description": entry.get("item_description", ""),
                        "qty": entry.get("qty", 1),
                        "unit_price": entry.get("unit_price", 0),
                        "total": entry.get("total", 0),
                        "status": entry.get("status", "unpaid")
                    }
                    save_to_credit([normalized], biz_slug)

                elif t in ('payment_received', 'payment_made'):

                    normalized = {
                        "type": t,
                        "entity_name": entry.get("entity_name", ""),
                        "item_description": entry.get("item_description", ""),
                        "qty": entry.get("qty", 1),
                        "unit_price": entry.get("unit_price", 0),
                        "total": entry.get("total", 0),
                        "status": entry.get("status", "paid")
                    }
                    save_to_credit([normalized], biz_slug)

                else:
                    # Fallback: treat as cash ledger entries (sale/purchase/expense)
                    save_to_ledger([entry], biz_slug)

            return f"✅ Done! I've recorded those {len(entries)} transaction(s) for {business_name}."

        return response_text

    except Exception as e:
        return f"❌ Accountant Error: {e}"

# -----------------------------
# CONTROLLER: BRIDGING THE UI AND THE ACCOUNTANT
# -----------------------------
def chat_wrapper(message, history, business_name):
    # --- Validation: Ensure users entered a business name
    if not business_name:
        history.append({"role": "user", "content": message.get("text", "🎙️ Audio Note")})
        history.append({"role": "assistant", "content": "⚠️ Please enter your **Business Name** at the top before we start, so I can open the right record for you!"})
        return {"text": "", "files": []}, history

    # --- Grabs text and uploaded files from the Multimodal input box
    user_text = message.get("text", "")
    files = message.get("files", [])

    user_audio = None
    user_document = None

    # --- Detect file type (audio vs image vs documents)
    if files:
        file_path = str(files[0]).lower()

        # --- Audio files
        if file_path.endswith((".ogg", ".wav", ".mp3", ".m4a", ".aac", ".amr")):
            user_audio = files[0]

        # --- Document Files (Images/PDF/txt): treat same pipeline (OCR)
        elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".pdf", ".txt")):
            user_document = files[0]

        # --- fallback
        else:
            user_document = files[0]

    # --- Sends the input to Kognit AI for processing
    bot_response = kognit_ai_accountant(user_text, user_audio, user_document, business_name)

    # --- Format the UI chat bubbles
    if user_text:
        user_display = user_text
    elif user_audio:
        user_display = "🎙️ Audio Note"
    elif user_document:
        user_display = "📄 Document Upload"
    else:
        user_display = f"🔑Successfully Logged in: **{business_name}**"

    history.append({"role": "user", "content": user_display})
    history.append({"role": "assistant", "content": bot_response})

    return {"text": "", "files": []}, history

# -----------------------------
#  GRADIO (UI & INTERFACE)
# -----------------------------

# --- UI Styling: Reduce chatbot text size
chatbot_css = """
#chatbot .message,
#chatbot .message *,
#chatbot p,
#chatbot span,
#chatbot li,
#chatbot code {
    font-size: 14.8px !important;
    line-height: 1.47 !important;
}
"""

with gr.Blocks() as demo:
    gr.Markdown("# 📊 Kognit AI: Your Smart Accounting Assistant & Financial Intelligence AI")
    gr.Markdown("Built by **Ridwan Oyeniyi (fullstack_overlord)** for The 3MTT Knowledge Showcase.")

    # --- Business Name Row
    with gr.Row():
        biz_name_box = gr.Textbox(
            label="Business Name",
            placeholder="e.g. Seriki Autos Ltd",
            interactive=True
        )

    # --- The Conversation Bubbles
    chatbot = gr.Chatbot(
        label="Chat History",
        height=450,
        show_label=False,
        elem_id="chatbot"
    )

    # --- The unified input bar
    chat_input = gr.MultimodalTextbox(
        interactive=True,
        placeholder="Type a message or tap the mic to speak...",
        show_label=False,
        # autofocus=True,
        sources=["microphone", "upload"],
        file_count="single",
        file_types=["audio", "image", "file", ".aac",  ".pdf", ".txt"]
    )

    # --- The submit button
    chat_input.submit(
        chat_wrapper,
        inputs=[chat_input, chatbot, biz_name_box],
        outputs=[chat_input, chatbot]
    )

# --- Launch
demo.launch(
    theme=gr.themes.Soft(),
    css=chatbot_css,
    # share=True,
    inline=False
)