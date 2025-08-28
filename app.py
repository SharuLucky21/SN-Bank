import os
import random
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# --------------------------------
# App + DB setup
# --------------------------------
def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///bank.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_demo_data()

    # --------------------------------
    # Auth helpers
    # --------------------------------
    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = User.query.get(user_id) if user_id else None

    def login_required(view):
        from functools import wraps
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Please login to continue.", "warning")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    # --------------------------------
    # Register
        # --------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"].lower()
            password = request.form["password"]
            dob_str = request.form["dob"]

            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                age = datetime.now().year - dob.year
                if age <= 0:
                    flash("Account not created. Invalid Date of Birth.", "danger")
                    return redirect(url_for("register"))
            except Exception:
                flash("Invalid Date of Birth format.", "danger")
                return redirect(url_for("register"))

            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "danger")
                return redirect(url_for("register"))

            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                account_number=str(random.randint(1002003000, 1002003999)),
                dob=dob,
                balance=0.00
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")
    
    # --------------------------------
    # Forgot Password
    # --------------------------------
    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            email = request.form["email"].strip().lower()
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("No account found with that email.", "danger")
                return redirect(url_for("forgot_password"))

            # Store the email temporarily in session (in real app, use token via email)
            session["reset_email"] = email
            flash("Account found. Please set a new password.", "info")
            return redirect(url_for("reset_password"))
        return render_template("forgot_password.html")


    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        email = session.get("reset_email")
        if not email:
            flash("Session expired. Please try again.", "warning")
            return redirect(url_for("forgot_password"))

        if request.method == "POST":
            new_password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("reset_password"))
            user = User.query.filter_by(email=email).first()
            if user:
                user.password_hash = generate_password_hash(new_password)              
                db.session.commit()
                session.pop("reset_email", None)
                flash("Password reset successful. Please login.", "success")
                return redirect(url_for("login"))
            else:
                flash("Error: User not found.", "danger")
                return redirect(url_for("forgot_password"))

        return render_template("reset_password.html")



    # --------------------------------
    # Login / Logout
    # --------------------------------
    @app.get("/")
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        return render_template("home.html")

    @app.post("/login")
    def do_login():
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))
        session["user_id"] = user.id
        flash(f"Welcome back, {user.name.split()[0]}!", "success")
        return redirect(url_for("dashboard"))

    @app.get("/logout")
    def logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("login"))

    # --------------------------------
    # Dashboard
    # --------------------------------
    @app.get("/dashboard")
    @login_required
    def dashboard():
        recent_txns = (
            Transaction.query
            .filter_by(user_id=g.user.id)
            .order_by(Transaction.timestamp.desc())
            .limit(5)
            .all()
        )
        return render_template("dashboard.html", recent_txns=recent_txns)

    # --------------------------------
    # Balance
    # --------------------------------
    @app.get("/balance")
    @login_required
    def balance():
        user = User.query.get(g.user.id)
        return render_template("balance.html", user=user)

    # --------------------------------
    # Transactions
    # --------------------------------
    @app.get("/transactions")
    @login_required
    def transactions():
        txns = (
            Transaction.query
            .filter_by(user_id=g.user.id)
            .order_by(Transaction.timestamp.desc())
            .all()
        )
        return render_template("transactions.html", txns=txns)

    # --------------------------------
    # Transfer (typed account or phone)
    # --------------------------------
    @app.get("/transfer")
    @login_required
    def transfer_form():
        return render_template("transfer.html")

    @app.post("/transfer")
    @login_required
    def do_transfer():
        from_account = User.query.get(g.user.id)
        to_input = request.form.get("to_account_or_phone").strip()
        amount_str = request.form.get("amount", "0").strip()
        note = request.form.get("note", "").strip()

        # validate amount
        try:
            amount = Decimal(amount_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("transfer_form"))

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return redirect(url_for("transfer_form"))
        if from_account.balance < amount:
            flash("Insufficient balance.", "danger")
            return redirect(url_for("transfer_form"))

        # find recipient by account_number OR phone
        to_account = User.query.filter(
            (User.account_number == to_input) | (User.phone == to_input)
        ).first()

        if not to_account:
            flash("Recipient not found.", "danger")
            return redirect(url_for("transfer_form"))

        if to_account.id == from_account.id:
            flash("You cannot transfer to yourself.", "danger")
            return redirect(url_for("transfer_form"))

        # Perform transfer
        from_account.balance = (Decimal(from_account.balance) - amount).quantize(Decimal("0.01"))
        to_account.balance = (Decimal(to_account.balance) + amount).quantize(Decimal("0.01"))

        # Record transactions
        t_out = Transaction(
            user_id=from_account.id, type="debit", amount=amount,
            description=note or f"Transfer to {to_account.account_number}",
            counterparty=str(to_account.account_number),
            balance_after=from_account.balance
        )
        t_in = Transaction(
            user_id=to_account.id, type="credit", amount=amount,
            description=note or f"Transfer from {from_account.account_number}",
            counterparty=str(from_account.account_number),
            balance_after=to_account.balance
        )
        db.session.add_all([t_out, t_in])
        db.session.commit()

        flash(f"₹{amount} sent to {to_account.name} ({to_account.account_number}).", "success")
        return redirect(url_for("transactions"))

    return app

# --------------------------------
# DB
# --------------------------------
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    dob = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15), unique=True)  # NEW field
    balance = db.Column(db.Numeric(12, 2), default=0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    type = db.Column(db.String(10), nullable=False)  # "credit" or "debit"
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), default="")
    counterparty = db.Column(db.String(30), default="")  # other account number
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

def seed_demo_data():
    if User.query.count() > 0:
        return

    user1 = User(
        name="Sharanya Lakshmi",
        email="user1@example.com",
        password_hash=generate_password_hash("password123"),
        account_number="1002003001",
        dob=datetime.strptime("2000-01-01", "%Y-%m-%d").date(),   # 👈 added DOB
        phone="9876543210",
        balance=10000.00
    )
    user2 = User(
        name="Demo User",
        email="user2@example.com",
        password_hash=generate_password_hash("password123"),
        account_number="1002003002",
        dob=datetime.strptime("1998-05-15", "%Y-%m-%d").date(),   # 👈 added DOB
        phone="1234567890",
        balance=5000.00
    )

    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
