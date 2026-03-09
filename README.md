# Sabi-Spend
Smart AI-Powered Accounting Assistant for Nigerian SMEs.


# 📊 Sabi-Spend: Your Smart AI-Powered Accounting Assistant

**Sabi-Spend** is a high-performance, AI-powered accounting assistant designed to help Nigerian small business owners track sales and purchases, calculate profit and loss, give profitability advice and draft statement of account all in their own language—including English, Pidgin, Yoruba, Hausa, and Igbo.

Built by **Ridwan Oyeniyi [[fullstack_overlord](https://github.com/fullstack-overlord)]** for the **3MTT Knowledge Showcase**.

## 🚀 Live Demo
[[Get started with Sabi-Spend](https://huggingface.co/spaces/fullstack-overlord/Sabi-Spend)]

## ✨ Key Features
* **Multilingual Voice Support:** Talk to Sabi-Spend in English or your local dialect (Yoruba, Hausa, Igbo and Pidgin).
* **Automated Bookkeeping:** Converts natural speech or text into structured accounting data.
* **Cloud Persistence:** Data is synced to Hugging Face Datasets for 100% security and recovery.
* **Scalability:** Built with a "Multi-Tenant" architecture; the app dynamically creates separate ledger files for every unique Business Name, allowing it to serve thousands of users simultaneously.
* **Insightful Reports:** Uses Gemini 3.1 Flash-Lite to provide "Business Wisdom" and financial health analysis.

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
