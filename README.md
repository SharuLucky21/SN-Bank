
# 🏦 SN Bank – Mock Online Banking Application

## 📖 Description  
SN Bank is a **Flask-based full-stack banking web application** that simulates real-world banking operations like **account creation, login, balance tracking, fund transfers, and transaction history**.  
It is designed with a **modern banking UI** inspired by SBI/KVB and ensures a smooth user experience.  

---

## 🛠️ Tech Stack  
- **Frontend:** HTML5, CSS3, JavaScript  
- **Backend:** Flask (Python)  
- **Database:** SQLite (SQLAlchemy ORM)  
- **Authentication:** Flask-Login + Password Hashing  
- **UI Theme:** Banking-style (SBI/KVB-inspired)  

---

## ✨ Features  
✔️ User Registration with DOB check (age validation)  
✔️ Secure Login & Logout  
✔️ Forgot Password (email/phone-based recovery option)  
✔️ Dashboard with colorful banking cards  
✔️ Credit/Debit reflected in transaction history  
✔️ Money transfer by account number or phone number  
✔️ Profile section with account details  
✔️ Flash messages for actions (success/error notifications)  

---

## 📸 Screenshots  
(Add your app screenshots here – login page, dashboard, transfer page, etc.)  

---

## 🚀 How to Run Locally  

```bash
# 1. Clone the repository
git clone https://github.com/your-username/sn-bank.git
cd sn-bank

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
