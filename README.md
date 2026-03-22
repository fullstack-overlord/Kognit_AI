# Kognit AI
Smart AI-Powered Accounting Assistant & Financial Intelligence AI for Nigerian SMEs.


# 📊 Kognit AI: Your Smart AI-Powered Accounting Assistant & Financial Intelligence AI

**Kognit AI** is a scalable, high-performance, AI-powered accounting assistant & Financial Intelligence AI designed to help Nigerian small business owners automate bookkeeping, track their inventory, manage debts and cash & credit accounts, track their finances (expenses/costs, sales, and profits), draft financial reports and accounting statements, draft time-based financial reports and summaries (daily, weekly and monthly reports), smart business insights (analytics + anomaly/trend detection), answer financial queries and offer personalized financial literacy coaching & interactive financial consulting, analyze profitability & financial health, and give real-time actionable insights & advice in a friendly, conversational way all in their own language—including English, Pidgin, Yoruba, Hausa, and Igbo.

Built by **Ridwan Oyeniyi [[fullstack_overlord](https://github.com/fullstack-overlord)]** for the **3MTT Knowledge Showcase**.

## 🚀 Live Demo
[[Get started with Sabi-Spend](https://huggingface.co/spaces/fullstack-overlord/Kognit_AI)]

## ✨ Key Features
* **Multilingual Voice Support:** Talk to Kognit AI in English or your local dialect (Yoruba, Hausa, Igbo and Pidgin).
* **Automated Bookkeeping:** Converts natural speech or text into structured accounting data instantl, removing the need for manual data entry.
* **Official Statements & Insights:** Generates insightful financial health reports and professional statements of account tailored to the business's specific performance.
* **Empathic AI Accountant (High Reasoning):** Powered by Gemini 3.1 Flash-Lite's "Thinking Mode." Kognit AI doesn't just calculate; it understands. It provides comfort during business setbacks and offers strategic, actionable advice for financial recovery.
* **Interactive Financial Consulting:** Speak to Kognit AI as you would to a human accountant. Users can ask complex questions about their business health, profit trends, Business wisdom/advice, financial health analysis or expense management and receive deep, nuanced analysis.
* **Cloud Persistence:** Data is synced to Hugging Face Datasets for 100% security and recovery, ensuring your records are never lost.
* **Scalable Multi-Tenant Architecture:** Built with a "Multi-Tenant" architecture; the app dynamically creates and manages separate, private ledger files for every unique Business Name, allowing the system to serve thousands of SMEs simultaneously.

## 🚧 Other Features (Coming Soon)
* **I-O-U Tracker (Debt Management):** Tracks who owes the business money and automated payment reminders. Allow users to record debts using an updated CSV structure with debtor_name and status (paid/debt).
* **Bank-Ready PDF Statements:** Converts messy CSV data into professional, "Bank-Ready" PDF documents using FPDF2. Perfect for business owners applying for loans or grants.
* **AI Anomaly Detection:** An "AI Safety Net" that flags potential entry mistakes (e.g., recording a ₦5,000 sale as ₦50,000) by comparing inputs against previously recorded business prices.
* **Paper-to-Digital (OCR):** Leveraging Gemini’s vision capabilities to turn a photo of a handwritten receipt or printed invoice into an automatic digital entry.
* **Daily/Monthly PDF Reports:** Users can prompt Sabi-Spend to generate the sales/expenses recorded on a specific day or for a specified month. Use Pandas to filter the CSV by date.

## 🛠️ Tech Stack
* **Language:** Python
* **Brain:** Google Gemini 3.1 Flash-Lite (via Google GenAI API)
* **Interface:** Gradio (optimized for mobile)
* **Storage:** Hugging Face Datasets (CSV/TXT)
* **Deployment:** Hugging Face Spaces

## ⚙️ Setup Instructions
1. Clone the repo: `git clone https://github.com/fullstack-overlord/Sabi-Spend.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Setup environment variables in a `.env` file:
   - `GEMINI_API_KEY`
   - `HF_TOKEN`
4. Run the app: `python app.py`

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
**Built with grit during a 7-days (12-hours/day) development sprint for The 3MTT Knowledge Showcase.**
