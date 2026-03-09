import os
import json
import csv
import re
from datetime import datetime
import gradio as gr
from google import genai
from google.genai import types
from dotenv import load_dotenv
from huggingface_hub import HfApi, hf_hub_download

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- HF CONFIGURATION START:
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "fullstack-overlord/sabi-spend-data" 
api = HfApi()

def sync_cloud(filename, action="push"):
    """Pulls or Pushes files to HF Dataset to ensure data persists after app restart."""
    if not HF_TOKEN or not REPO_ID: return 
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
    except Exception:
        pass
# --- HF CONFIGURATION END

# --- IDENTITY HELPER
def create_user_slug(name):
    """Turns 'Mama's Kitchen!' into 'mamas_kitchen' for safe filing."""
    if not name: return "default_user"
    return re.sub(r'[^a-z0-9]', '_', name.lower().strip())

# --- DATABASE & CALCULATION LOGIC
def get_capital(biz_slug):
    capital_file = f"{biz_slug}_capital.txt"
    sync_cloud(capital_file, action="pull")
    if os.path.exists(capital_file):
        with open(capital_file, "r") as f: return float(f.read())
    return 0.0

def set_capital(amount, biz_slug):
    capital_file = f"{biz_slug}_capital.txt"
    with open(capital_file, "w") as f: f.write(str(amount))
    sync_cloud(capital_file, action="push")

def save_to_ledger(rows, biz_slug):
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

# --- PROFITABILITY ADVICE
def get_profitability_analysis(biz_slug):
    db_file = f"{biz_slug}_ledger.csv"
    sync_cloud(db_file, action="pull")
    if not os.path.isfile(db_file): return "No data yet to analyze."
    
    analysis = {} # Structure: {item_name: {'cost': 0, 'sales': 0}}
    
    with open(db_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = row['item'].lower().strip()
            total = float(row['total'])
            if item not in analysis: analysis[item] = {'cost': 0, 'sales': 0}
            
            if row['type'] == 'purchase': analysis[item]['cost'] += total
            elif row['type'] == 'sale': analysis[item]['sales'] += total

    if not analysis: return "No transactions found to analyze."

    report = "💡 **SABI-SPEND BUSINESS ADVICE**\n\n"
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

def generate_professional_report(biz_slug):
    db_file = f"{biz_slug}_ledger.csv"
    sync_cloud(db_file, action="pull")
    if not os.path.isfile(db_file): return "No transactions recorded yet."
    
    capital = get_capital(biz_slug)
    purchases = []
    sales = []
    other_expenses = 0
    
    with open(db_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_str = f"{row['qty']} {row['item']} @ ₦{float(row['unit_price']):,.0f}"
            total = float(row['total'])
            if row['type'] == 'purchase': purchases.append((item_str, total))
            elif row['type'] == 'sale': sales.append((item_str, total))
            else: other_expenses += total

    total_expenses = sum(p[1] for p in purchases) + other_expenses
    total_income = sum(s[1] for s in sales)
    profit = total_income - total_expenses
    balance = (capital - total_expenses) + total_income

    report = "📋 **OFFICIAL STATEMENT OF ACCOUNT**\n\n"
    report += "🛒 **PURCHASES (Stock Bought):**\n" + "\n".join([f"• {p[0]}: ₦{p[1]:,.0f}" for p in purchases])
    report += f"\n\n⛽ **OTHER EXPENSES:** ₦{other_expenses:,.0f}"
    report += "\n\n💰 **SALES (Income Made):**\n" + "\n".join([f"• {s[0]}: ₦{s[1]:,.0f}" for s in sales])
    report += f"\n\n---"
    report += f"\n🏦 **Starting Capital:** ₦{capital:,.0f}"
    report += f"\n📉 **Total Expenses:** ₦{total_expenses:,.0f}"
    report += f"\n📈 **Total Income:** ₦{total_income:,.0f}"
    report += f"\n✨ **Net Profit:** ₦{profit:,.0f}"
    report += f"\n💎 **Current Balance:** ₦{balance:,.0f}"
    return report

def sabi_spend_accountant(text_input, audio_input, business_name):

    biz_slug = create_user_slug(business_name) 
    current_report = generate_professional_report(biz_slug)
    current_advice = get_profitability_analysis(biz_slug)

    try:
        # The Master Prompt
        prompt = f"""
        You are 'Sabi-Spend', a Smart AI-Powered Accounting Assistant for Nigerian Businesses. Built by 'Ridwan Oyeniyi (fullstack_overlord)'. 
        You are expert in English, Pidgin, Yoruba, Hausa, and Igbo and you can speak them fluently. You help small business owners track their finances, analyze profitability, and give actionable advice in a friendly, conversational way.

        CONTEXT FOR BUSINESS '{business_name}':
        - Current Report: {current_report}
        - Current Advice: {current_advice}

        YOUR TASK:
        1. If the user wants to see their balance, profit, report or 'statement of account', explain the 'Current Report' in a friendly way.
        2. If the user asks for advice or how the business is doing, use the 'Current Advice'.
        3. If the user mentions starting money, capital, adding capital, or 'investing' in the shop, extract it as:
           [{{"type": "capital", "item": "Starting Capital", "total": 500000}}]
        4. If the user is reporting a sale, purchase, or expense, extract the data into this JSON format:
           [{{"type": "purchase/sale/expense", "item": "name", "qty": 1, "unit_price": 1, "total": 1}}]
        5. Always respond in the SAME language or dialect the user used (especially Pidgin).
        6. If it's just a greeting like 'hello', 'hey', 'who are you', 'who built you', 'how far' or 'hi', respond warmly as a Smart AI Accounting, mention your name (Sabi-Spend) and who built you (Ridwan Oyeniyi (fullstack_overlord)).

        IMPORTANT: If you extract a transaction, ONLY return the JSON. No other text.
        """
        
        contents = [prompt]
        if text_input: contents.append(text_input)
        if audio_input:
            with open(audio_input, "rb") as f:
                contents.append(types.Part.from_bytes(data=f.read(), mime_type='audio/ogg'))

        response = client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=contents)
        response_text = response.text.strip()

        # Check if the response is a JSON transaction
        if response_text.startswith("[") and response_text.endswith("]"):
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            entries = json.loads(clean_json)
            
            for entry in entries:
                if entry.get('type') == 'capital':
                    set_capital(entry.get('total', 0), biz_slug)
                else:
                    save_to_ledger([entry], biz_slug)
            
            return f"✅ Done! I've recorded those {len(entries)} items in the ledger for {business_name}."
        
        return response_text

    except Exception as e:
        return f"❌ Accountant Error: {e}"

# --- CONTROLLER: BRIDGING THE UI AND THE ACCOUNTANT
def chat_wrapper(message, history, business_name):
    # 1. Validation: Ensure user entered a business name
    if not business_name:
        history.append({"role": "user", "content": message.get("text", "🎙️ Audio Note")})
        history.append({"role": "assistant", "content": "⚠️ Please enter your **Business Name** at the top before we start, so I can open the right record for you!"})
        return {"text": "", "files": []}, history

    # Grabs text and audio from the Multimodal input box
    user_text = message.get("text", "")
    files = message.get("files", [])
    user_audio = files[0] if len(files) > 0 else None
    #Sends the input to Sabi-Spend for processing
    bot_response = sabi_spend_accountant(user_text, user_audio, business_name)
    
    # Format the UI chat bubbles
    if user_text:
        user_display = user_text
    elif user_audio:
        user_display = "🎙️ Audio Note"
    else:
        user_display = f"🔑Successfully Logged in: **{business_name}**"
    
    history.append({"role": "user", "content": user_display})
    history.append({"role": "assistant", "content": bot_response})
    
    return {"text": "", "files": []}, history

# --- GRADIO UI ---
with gr.Blocks() as demo:
    gr.Markdown("# 📊 Sabi-Spend: Your Smart AI-Powered Accounting Assistant")
    gr.Markdown("Built by **Ridwan Oyeniyi (fullstack_overlord)** for The 3MTT Knowledge Showcase.")
    
    # Business Name Row
    with gr.Row():
        biz_name_box = gr.Textbox(
            label="Business Name", 
            placeholder="e.g. Seriki Autos Ltd.",
            interactive=True
        )

    # The Conversation Bubbles
    chatbot = gr.Chatbot(
        label="Chat History",
        height=450,
        show_label=False
    )
    
    # The unified input bar
    chat_input = gr.MultimodalTextbox(
        interactive=True,
        placeholder="Type a message or tap the mic to speak...",
        show_label=False,
        sources=["microphone", "upload"],
        file_count="single",
        file_types=["audio", "image"]
    )

    # The submit button
    chat_input.submit(
        chat_wrapper, 
        inputs=[chat_input, chatbot, biz_name_box], 
        outputs=[chat_input, chatbot]
    )

demo.launch(theme=gr.themes.Soft(), inline=False)