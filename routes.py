"""
routes.py – LearnMate Flask Routes & API Endpoints
====================================================
All URL handlers and JSON API endpoints are defined here.
"""

import json
import io
import os
from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, session,
    jsonify, redirect, url_for, send_file
)
from agent import chat_with_agent, generate_roadmap, assess_skills, AGENT_INSTRUCTIONS

main_bp = Blueprint("main", __name__)

# ── Skill-assessment question bank ───────────────────────────────────────────
QUESTION_BANK = {
    "Frontend Development": [
        {"q": "What does CSS stand for?", "options": ["Cascading Style Sheets", "Computer Style Sheets", "Creative Style System", "Colorful Style Sheets"], "answer": 0},
        {"q": "Which HTML tag is used for the largest heading?", "options": ["<h6>", "<heading>", "<h1>", "<head>"], "answer": 2},
        {"q": "What is the correct CSS syntax to change font color?", "options": ["font-color: red", "color: red", "text-color: red", "font: red"], "answer": 1},
        {"q": "Which JS method selects an element by ID?", "options": ["querySelector()", "getElementById()", "getElement()", "selectId()"], "answer": 1},
        {"q": "What does 'responsive design' primarily rely on?", "options": ["JavaScript animations", "Media queries", "Server-side rendering", "WebSockets"], "answer": 1},
    ],
    "Backend Development": [
        {"q": "What is REST?", "options": ["A database type", "An architectural style for APIs", "A programming language", "A web server"], "answer": 1},
        {"q": "Which HTTP method is used to update a resource?", "options": ["GET", "POST", "PUT", "DELETE"], "answer": 2},
        {"q": "What does ORM stand for?", "options": ["Object Relational Mapping", "Online Resource Manager", "Open Runtime Module", "Object Request Method"], "answer": 0},
        {"q": "Which of these is NOT a relational database?", "options": ["PostgreSQL", "MySQL", "MongoDB", "SQLite"], "answer": 2},
        {"q": "What is middleware in web development?", "options": ["A type of database", "Software between OS and applications", "Functions that handle request/response", "A CSS framework"], "answer": 2},
    ],
    "Data Science": [
        {"q": "Which Python library is primarily used for data manipulation?", "options": ["NumPy", "Pandas", "Matplotlib", "Scikit-learn"], "answer": 1},
        {"q": "What is a DataFrame?", "options": ["A database table", "A 2D labeled data structure", "A type of neural network", "A file format"], "answer": 1},
        {"q": "What does EDA stand for?", "options": ["Exploratory Data Analysis", "Extended Data Algorithm", "External Data Access", "Error Detection Algorithm"], "answer": 0},
        {"q": "Which algorithm is used for classification and regression?", "options": ["K-Means", "PCA", "Random Forest", "DBSCAN"], "answer": 2},
        {"q": "What is overfitting?", "options": ["Model performs well on training but poorly on test data", "Model has too few parameters", "Model underfits the training data", "Model uses too little data"], "answer": 0},
    ],
    "Cybersecurity": [
        {"q": "What does SQL injection exploit?", "options": ["Weak passwords", "Unsanitised user input in SQL queries", "Network vulnerabilities", "OS kernel bugs"], "answer": 1},
        {"q": "What is a firewall?", "options": ["Antivirus software", "A network security system monitoring traffic", "An encryption algorithm", "A VPN protocol"], "answer": 1},
        {"q": "What does HTTPS provide over HTTP?", "options": ["Faster speeds", "Encrypted communication", "Better caching", "More headers"], "answer": 1},
        {"q": "What is phishing?", "options": ["Port scanning technique", "Fraudulent attempt to obtain credentials", "A type of encryption", "A network protocol"], "answer": 1},
        {"q": "What is two-factor authentication (2FA)?", "options": ["Logging in twice", "Using two passwords", "Requiring two verification methods", "Two-step encryption"], "answer": 2},
    ],
    "Artificial Intelligence": [
        {"q": "What is a neural network inspired by?", "options": ["Computer circuits", "The human brain", "Decision trees", "Linear algebra"], "answer": 1},
        {"q": "What does NLP stand for?", "options": ["Neural Learning Process", "Natural Language Processing", "Network Layer Protocol", "None of the above"], "answer": 1},
        {"q": "What is supervised learning?", "options": ["Learning without labels", "Learning from labelled training data", "Reinforcement from rewards", "Unsupervised clustering"], "answer": 1},
        {"q": "What is a transformer model?", "options": ["An electrical component", "An attention-based deep learning model", "A type of CNN", "A decision tree variant"], "answer": 1},
        {"q": "What is transfer learning?", "options": ["Transferring data between models", "Using a pre-trained model on a new task", "Moving ML code to production", "Training on GPU"], "answer": 1},
    ],
    "Cloud Computing": [
        {"q": "What does IaaS stand for?", "options": ["Internet as a Service", "Infrastructure as a Service", "Integration as a Service", "Intelligence as a Service"], "answer": 1},
        {"q": "Which is a major cloud provider?", "options": ["Oracle DB", "AWS", "GitHub", "Docker"], "answer": 1},
        {"q": "What is serverless computing?", "options": ["Running code without any server", "Cloud provider manages the server infrastructure", "Using only local machines", "Edge computing only"], "answer": 1},
        {"q": "What is a container in cloud computing?", "options": ["A database", "A lightweight isolated runtime environment", "A virtual machine", "A network switch"], "answer": 1},
        {"q": "What is auto-scaling?", "options": ["Manually adjusting server capacity", "Automatically adjusting resources based on demand", "Scaling database records", "Compressing files automatically"], "answer": 1},
    ],
    "Full Stack Development": [
        {"q": "What does 'full stack' mean?", "options": ["Only frontend", "Only backend", "Frontend + Backend development", "Database only"], "answer": 2},
        {"q": "Which of these is a JavaScript runtime?", "options": ["Django", "Node.js", "Laravel", "Flask"], "answer": 1},
        {"q": "What is an API?", "options": ["A programming language", "Application Programming Interface", "A database system", "An operating system"], "answer": 1},
        {"q": "Which database is document-oriented?", "options": ["PostgreSQL", "MySQL", "MongoDB", "SQLite"], "answer": 2},
        {"q": "What is version control?", "options": ["OS version management", "Tracking code changes over time", "Software licensing", "App versioning"], "answer": 1},
    ],
    "DevOps": [
        {"q": "What is CI/CD?", "options": ["Cloud Infrastructure / Continuous Deployment", "Continuous Integration / Continuous Delivery", "Code Integration / Code Delivery", "None of the above"], "answer": 1},
        {"q": "Which tool is commonly used for containerisation?", "options": ["Jenkins", "Docker", "Ansible", "Terraform"], "answer": 1},
        {"q": "What is infrastructure as code?", "options": ["Writing software documentation", "Managing infrastructure through config files", "Coding inside a VM", "None"], "answer": 1},
        {"q": "What is a Kubernetes pod?", "options": ["A container registry", "The smallest deployable unit in Kubernetes", "A load balancer", "A storage class"], "answer": 1},
        {"q": "What is blue-green deployment?", "options": ["Two-branch git strategy", "Running two production environments for zero-downtime deploys", "A CSS animation technique", "A database backup strategy"], "answer": 1},
    ],
}

# Default questions for any domain not in the bank
DEFAULT_QUESTIONS = QUESTION_BANK["Full Stack Development"]


def _get_profile() -> dict:
    """Return the student profile stored in the session (create defaults if absent)."""
    if "profile" not in session:
        session["profile"] = {
            "name": "Learner",
            "email": "",
            "domain": "Full Stack Development",
            "experience_level": "Beginner",
            "learning_style": "Visual",
            "weekly_hours": 10,
            "career_goal": "Software Developer",
            "background": "",
            "avatar_color": "#3b82d4",
            "joined": date.today().isoformat(),
            "streak": 0,
            "last_active": date.today().isoformat(),
            "completed_courses": [],
            "bookmarks": [],
            "badges": [],
            "progress": {},
        }
    return session["profile"]


def _update_streak(profile: dict) -> dict:
    """Increment learning streak if the student is active today."""
    today = date.today().isoformat()
    last = profile.get("last_active", today)
    if last != today:
        from datetime import timedelta
        last_date = date.fromisoformat(last)
        if (date.today() - last_date).days == 1:
            profile["streak"] = profile.get("streak", 0) + 1
        elif (date.today() - last_date).days > 1:
            profile["streak"] = 1
        profile["last_active"] = today
        session.modified = True
    return profile


# ── Page routes ───────────────────────────────────────────────────────────────

@main_bp.route("/")
def index():
    profile = _get_profile()
    _update_streak(profile)
    return render_template("dashboard.html",
                           profile=profile,
                           domains=AGENT_INSTRUCTIONS["supported_domains"],
                           agent_name=AGENT_INSTRUCTIONS["name"])


@main_bp.route("/chat")
def chat():
    profile = _get_profile()
    if "chat_history" not in session:
        session["chat_history"] = []
    # Inject a welcome message on first visit
    if not session["chat_history"]:
        welcome = (
            f"👋 Hi {profile['name']}! I'm **{AGENT_INSTRUCTIONS['name']}**, "
            f"{AGENT_INSTRUCTIONS['tagline']}\n\n"
            f"I'm here to help you master **{profile['domain']}** and reach your goal "
            f"of becoming a **{profile['career_goal']}**.\n\n"
            "Tell me about your experience level, how many hours you can study per week, "
            "and what you'd like to achieve – and I'll build your personalised learning path! 🚀"
        )
        session["chat_history"] = [{"role": "assistant", "content": welcome}]
        session.modified = True
    return render_template("chat.html",
                           profile=profile,
                           history=session["chat_history"],
                           agent_name=AGENT_INSTRUCTIONS["name"])


@main_bp.route("/roadmap")
def roadmap():
    profile = _get_profile()
    roadmap_data = session.get("roadmap")
    return render_template("roadmap.html",
                           profile=profile,
                           roadmap=roadmap_data,
                           domains=AGENT_INSTRUCTIONS["supported_domains"])


@main_bp.route("/assessment")
def assessment():
    profile = _get_profile()
    # Allow ?domain= query param to switch domain without changing profile
    domain = request.args.get("domain") or profile.get("domain", "Full Stack Development")
    questions = QUESTION_BANK.get(domain, DEFAULT_QUESTIONS)
    return render_template("assessment.html",
                           profile=profile,
                           questions=questions,
                           domain=domain,
                           domains=list(QUESTION_BANK.keys()))


@main_bp.route("/profile")
def profile_page():
    profile = _get_profile()
    return render_template("profile.html",
                           profile=profile,
                           domains=AGENT_INSTRUCTIONS["supported_domains"],
                           learning_styles=AGENT_INSTRUCTIONS["learning_styles"])


# ── API endpoints ─────────────────────────────────────────────────────────────

@main_bp.route("/api/chat", methods=["POST"])
def api_chat():
    """Handle a chat message and return the AI reply."""
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    if len(user_message) > 2000:
        return jsonify({"error": "Message too long (max 2000 chars)"}), 400

    history = session.get("chat_history", [])
    reply = chat_with_agent(user_message, history)

    # Persist conversation
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["chat_history"] = history[-40:]  # Keep last 40 messages
    session.modified = True

    return jsonify({"reply": reply, "timestamp": datetime.now().strftime("%H:%M")})


@main_bp.route("/api/clear-chat", methods=["POST"])
def api_clear_chat():
    """Clear conversation history."""
    session.pop("chat_history", None)
    return jsonify({"status": "cleared"})


@main_bp.route("/api/generate-roadmap", methods=["POST"])
def api_generate_roadmap():
    """Generate a personalised roadmap for the current profile."""
    profile = _get_profile()
    data = request.get_json(silent=True) or {}
    # Allow one-off overrides from the request body
    merged = {**profile, **{k: v for k, v in data.items() if v}}
    roadmap_data = generate_roadmap(merged)
    session["roadmap"] = roadmap_data
    session.modified = True
    return jsonify(roadmap_data)


@main_bp.route("/api/assess", methods=["POST"])
def api_assess():
    """Evaluate skill-assessment answers."""
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", _get_profile().get("domain", "Full Stack Development"))
    answers = data.get("answers", [])
    if not answers:
        return jsonify({"error": "No answers provided"}), 400
    result = assess_skills(domain, answers)
    # Save score to profile progress
    profile = _get_profile()
    profile.setdefault("progress", {})[domain] = result.get("percentage", 0)
    session.modified = True
    return jsonify(result)


@main_bp.route("/api/update-profile", methods=["POST"])
def api_update_profile():
    """Save student profile changes."""
    data = request.get_json(silent=True) or {}
    allowed = {
        "name", "email", "domain", "experience_level",
        "learning_style", "weekly_hours", "career_goal",
        "background", "avatar_color"
    }
    profile = _get_profile()
    for key in allowed:
        if key in data and data[key] is not None:
            profile[key] = data[key]
    session.modified = True
    return jsonify({"status": "updated", "profile": profile})


@main_bp.route("/api/bookmark", methods=["POST"])
def api_bookmark():
    """Toggle a bookmarked course."""
    data = request.get_json(silent=True) or {}
    course = data.get("course")
    if not course:
        return jsonify({"error": "No course provided"}), 400
    profile = _get_profile()
    bookmarks = profile.setdefault("bookmarks", [])
    if course in bookmarks:
        bookmarks.remove(course)
        action = "removed"
    else:
        bookmarks.append(course)
        action = "added"
    session.modified = True
    return jsonify({"action": action, "bookmarks": bookmarks})


@main_bp.route("/api/complete-course", methods=["POST"])
def api_complete_course():
    """Mark a course as completed and award badges."""
    data = request.get_json(silent=True) or {}
    course = data.get("course")
    if not course:
        return jsonify({"error": "No course provided"}), 400
    profile = _get_profile()
    completed = profile.setdefault("completed_courses", [])
    if course not in completed:
        completed.append(course)
    # Award badges based on count
    count = len(completed)
    badges = profile.setdefault("badges", [])
    badge_map = {1: "🌱 First Step", 5: "🔥 On Fire", 10: "⭐ Star Learner",
                 25: "🏆 Champion", 50: "💎 Diamond Achiever"}
    for threshold, badge in badge_map.items():
        if count >= threshold and badge not in badges:
            badges.append(badge)
    session.modified = True
    return jsonify({"completed": count, "badges": badges})


@main_bp.route("/api/progress", methods=["GET"])
def api_progress():
    """Return the current student's progress data."""
    profile = _get_profile()
    return jsonify({
        "streak": profile.get("streak", 0),
        "completed_courses": len(profile.get("completed_courses", [])),
        "badges": profile.get("badges", []),
        "progress": profile.get("progress", {}),
        "bookmarks": profile.get("bookmarks", []),
    })


@main_bp.route("/api/download-roadmap", methods=["GET"])
def api_download_roadmap():
    """Generate and stream a PDF of the saved roadmap."""
    try:
        from fpdf import FPDF  # lazy import – only needed for PDF generation
    except ImportError:
        return jsonify({"error": "fpdf2 not installed. Run: pip install fpdf2"}), 500

    roadmap_data = session.get("roadmap")
    if not roadmap_data:
        return jsonify({"error": "No roadmap found. Generate one first."}), 404

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(59, 130, 212)
    pdf.cell(0, 12, "LearnMate – Personalised Learning Roadmap", ln=True, align="C")
    pdf.ln(4)

    # Meta
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(31, 35, 40)
    pdf.cell(0, 8, f"Student: {roadmap_data.get('student', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Domain: {roadmap_data.get('domain', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Career Goal: {roadmap_data.get('career_goal', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Estimated Completion: {roadmap_data.get('estimated_completion', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(6)

    # Phases
    for phase in roadmap_data.get("phases", []):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(59, 130, 212)
        pdf.cell(0, 10, f"{phase['phase']} Phase – Weeks {phase.get('weeks', '')}", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(31, 35, 40)
        pdf.multi_cell(0, 7, f"Goal: {phase.get('goal', '')}")
        pdf.ln(2)

        # Topics
        if phase.get("topics"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Topics:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for t in phase["topics"]:
                pdf.cell(0, 7, f"  - {t}", ln=True)

        # Resources
        if phase.get("resources"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Resources:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for r in phase["resources"]:
                free_tag = "[Free]" if r.get("free") else "[Paid]"
                line = f"  {free_tag} {r.get('title', '')} – {r.get('platform', '')} ({r.get('hours', '?')}h)"
                pdf.cell(0, 7, line[:95], ln=True)

        # Milestones
        if phase.get("milestones"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "Milestones:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for m in phase["milestones"]:
                pdf.cell(0, 7, f"  ✓ {m}", ln=True)
        pdf.ln(4)

    # Certifications
    certs = roadmap_data.get("certifications", [])
    if certs:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(59, 130, 212)
        pdf.cell(0, 10, "Recommended Certifications", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(31, 35, 40)
        for c in certs:
            pdf.cell(0, 7, f"  • {c.get('name', '')} – {c.get('provider', '')} ({c.get('level', '')})", ln=True)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    filename = f"LearnMate_Roadmap_{roadmap_data.get('student', 'Student')}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


# ── Error handlers ────────────────────────────────────────────────────────────

@main_bp.app_errorhandler(404)
def not_found(_):
    return render_template("dashboard.html",
                           profile=_get_profile(),
                           domains=AGENT_INSTRUCTIONS["supported_domains"],
                           agent_name=AGENT_INSTRUCTIONS["name"],
                           error="Page not found."), 404


@main_bp.app_errorhandler(500)
def server_error(_):
    return render_template("dashboard.html",
                           profile=_get_profile(),
                           domains=AGENT_INSTRUCTIONS["supported_domains"],
                           agent_name=AGENT_INSTRUCTIONS["name"],
                           error="Internal server error. Please try again."), 500
