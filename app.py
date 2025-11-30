# app.py
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.message import EmailMessage

# --- Config ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Local development or Render
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/site.db'
else:
    DB_PATH = os.path.join(BASE_DIR, 'data', 'site.db')
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

# Correct static and template folders
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET') or 'dev-only-local-fallback-please-set-FLAKS_SECRET-in-prod'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(120))
    last = db.Column(db.String(120))
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(80))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(120))
    description = db.Column(db.Text)
    tags = db.Column(db.String(300))
    img = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(200))
    role = db.Column(db.String(200))
    text = db.Column(db.Text)
    rating = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Initialize DB + Seed Data ---
with app.app_context():
    db.create_all()

    # Seed only if tables are empty
    if Project.query.count() == 0:
        p = Project(
            title="Analytics Platform",
            category="Web Application",
            description="Real-time data visualization with AI insights.",
            tags="React,AI,Analytics",
            img="https://picsum.photos/seed/p1/1200/800"
        )
        db.session.add(p)

    if Testimonial.query.count() == 0:
        t = Testimonial(
            author="Sarah Johnson",
            role="CEO, TechVentures",
            text="InnovateTech transformed our digital presence completely.",
            rating=5
        )
        db.session.add(t)

    db.session.commit()

# --- Email Helper ---
def send_email_notification(subject: str, body: str, to_email: str):
    host = os.environ.get('SMTP_HOST')
    if not host:
        app.logger.debug("SMTP not configured; skipping email.")
        return False

    port = int(os.environ.get('SMTP_PORT', 587))
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    from_email = os.environ.get('FROM_EMAIL', user)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.exception("Email failed")
        return False

# --- Routes ---
@app.route('/')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).limit(6).all()
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).limit(6).all()
    return render_template('index.html', projects=projects, testimonials=testimonials)

@app.route('/contact', methods=['POST'])
def contact():
    # detect AJAX/fetch requests
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # Determine how data is sent
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form or {}

    # Extract fields
    first = (data.get('first') or '').strip()
    last = (data.get('last') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    message = (data.get('message') or '').strip()

    # Validate
    errors = []
    if not email:
        errors.append("Email is required.")
    if not message:
        errors.append("Message is required.")

    if errors:
        if is_ajax or request.is_json:
            return jsonify({"ok": False, "errors": errors}), 400
        flash(" ".join(errors), "error")
        return redirect(url_for('index') + "#contact")

    # Save to DB
    try:
        cm = ContactMessage(
            first=first,
            last=last,
            email=email,
            phone=phone,
            message=message
        )
        db.session.add(cm)
        db.session.commit()
    except Exception as e:
        app.logger.exception("DB save failed")
        if is_ajax:
            return jsonify({"ok": False, "errors": ["Server error saving message."]}), 500
        flash("Server error saving message.", "error")
        return redirect(url_for('index') + "#contact")

    # Send email but do NOT fail user if email fails
    try:
        subject = f"New contact: {first} {last}".strip()
        body = f"From: {first} {last}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"
        admin_email = os.environ.get('ADMIN_EMAIL') or os.environ.get('FROM_EMAIL')
        if admin_email:
            send_email_notification(subject, body, admin_email)
    except Exception:
        app.logger.exception("Email notification failed")

    # Final success response (JSON for AJAX)
    if is_ajax or request.is_json:
        return jsonify({"ok": True, "message": "Thanks — your message was received!"})

    flash("Thanks — your message was received!", "success")
    return redirect(url_for('index') + "#contact")
# --- API Endpoints ---
@app.route('/api/projects')
def api_projects():
    ps = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([{
        "id": p.id,
        "title": p.title,
        "category": p.category,
        "description": p.description,
        "tags": p.tags.split(",") if p.tags else [],
        "img": p.img
    } for p in ps])

@app.route('/api/testimonials')
def api_testimonials():
    ts = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return jsonify([{
        "id": t.id,
        "author": t.author,
        "role": t.role,
        "text": t.text,
        "rating": t.rating
    } for t in ts])

@app.route('/api/blogs')
def api_blogs():
    return jsonify([])  # Placeholder

# --- Run ---
if __name__ == '__main__':
    # Only for local dev
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))