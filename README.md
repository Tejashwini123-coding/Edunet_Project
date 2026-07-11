# 🎓 LearnMate – Agentic AI for Personalised Course Pathways

> **AI-powered learning companion** built with Python Flask + IBM watsonx.ai (Granite models) that understands your goals, assesses your skills, and generates a fully personalised technology learning roadmap.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat Coach** | Real-time conversations powered by IBM Granite via watsonx.ai |
| 🗺️ **Dynamic Roadmaps** | Personalised beginner → intermediate → advanced learning paths |
| 📊 **Skill Assessment** | Domain-specific quizzes with AI-powered gap analysis |
| 📈 **Progress Tracker** | Completion %, streaks, milestones & learning charts |
| 🏆 **Achievement Badges** | Gamified badges to motivate consistent learning |
| 📅 **Weekly Planner** | Auto-generated 7-day study schedules |
| 📑 **PDF Export** | Download your full roadmap as a formatted PDF |
| 🔖 **Bookmarks** | Save courses and resources for later |
| 🌗 **Dark / Light Mode** | Glassmorphism UI with full theme toggle |
| 📱 **Responsive Design** | Mobile-first Bootstrap 5 layout |

---

## 🏗️ Project Structure

```
learnmate/
├── app.py               # Flask app factory & entry point
├── routes.py            # All URL routes & API endpoints
├── agent.py             # IBM watsonx.ai / Granite model logic
│                        #   └── AGENT_INSTRUCTIONS (customise here!)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Your secrets (git-ignored)
│
├── templates/
│   ├── base.html        # Shared layout (sidebar, navbar)
│   ├── dashboard.html   # Home dashboard with stats & charts
│   ├── chat.html        # AI chat interface
│   ├── roadmap.html     # Course roadmap visualisation
│   ├── assessment.html  # Skill assessment quiz
│   └── profile.html     # Student profile management
│
└── static/
    ├── css/style.css    # All custom styles
    └── js/
        ├── main.js      # Global JS (theme, sidebar, helpers)
        ├── chat.js      # Chat page logic & markdown rendering
        └── roadmap.js   # Roadmap generation & milestone tracking
```

---

## 🚀 Quick Start

### 1. Clone or download the project

```bash
cd learnmate
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
IBM_API_KEY=3A6r1aLOmf22Rqs19ybY5aBROrUyh9g_2dsU5hyPpOXs
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
FLASK_SECRET_KEY=your_random_secret_key
```

### 5. Run the application

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000/**

---

## 🔑 Getting IBM Credentials

### IBM Cloud API Key
1. Go to [https://cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)
2. Click **Create an IBM Cloud API key**
3. Copy the key into `.env`

### watsonx.ai Project ID
1. Go to [https://dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Create or open a **watsonx.ai** project
3. Go to **Manage → General** and copy the **Project ID**
4. Paste into `.env`

---

## 🤖 Customising the AI Agent

All agent behaviour is controlled by the `AGENT_INSTRUCTIONS` dictionary at the top of [`agent.py`](agent.py). You can change:

| Section | What to customise |
|---|---|
| `name` / `role` | Agent identity |
| `communication_style` | Tone, verbosity, formality |
| `recommendation_strategy` | How courses are sequenced and prioritised |
| `learning_styles` | Supported learning modalities |
| `supported_domains` | Technology domains the agent knows about |
| `career_focus` | Job titles, salary info, portfolio advice |
| `roadmap_phases` | Phase names, week ranges, descriptions |
| `safety_guidelines` | What the agent will and won't do |
| `adaptive_rules` | How it adjusts to student progress |
| `output_format` | Response structure, length, JSON format |

**No other file needs to be changed for behavioural customisation.**

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Send a chat message → AI reply |
| POST | `/api/clear-chat` | Clear conversation history |
| POST | `/api/generate-roadmap` | Generate a personalised roadmap |
| POST | `/api/assess` | Submit assessment answers |
| POST | `/api/update-profile` | Save student profile |
| POST | `/api/bookmark` | Toggle a bookmarked course |
| POST | `/api/complete-course` | Mark a course as completed |
| GET  | `/api/progress` | Get current progress data |
| GET  | `/api/download-roadmap` | Download roadmap as PDF |

---

## 🌐 Deployment

### Production with Gunicorn (Linux / macOS)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t learnmate .
docker run -p 5000:5000 --env-file .env learnmate
```

### IBM Code Engine / Cloud Foundry

```bash
# IBM Cloud CLI
ibmcloud login
ibmcloud target --cf
ibmcloud cf push learnmate -m 512M
```

---

## 🔒 Security

- Credentials are loaded exclusively from `.env` — never hardcoded
- `.env` is **git-ignored** by default — ensure it stays that way
- Session data is stored server-side (filesystem) — switch to Redis for production
- All user inputs are validated and length-limited
- Markdown is rendered client-side with `marked.js`

---

## 🧩 Supported Technology Domains

Frontend Development · Backend Development · Full Stack Development · Cybersecurity · Artificial Intelligence · Machine Learning · Data Science · Cloud Computing · UI/UX Design · DevOps · Mobile App Development · Blockchain Development · Game Development · Embedded Systems & IoT · Database Engineering · Site Reliability Engineering

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `Flask` | Web framework |
| `Flask-Session` | Server-side sessions |
| `python-dotenv` | `.env` file loading |
| `ibm-watsonx-ai` | IBM Granite model inference |
| `fpdf2` | PDF roadmap generation |
| `gunicorn` | Production WSGI server |

---

## 🗺️ Roadmap

- [ ] OAuth login (Google / GitHub)
- [ ] Real-time progress sync across devices
- [ ] Peer study group matching
- [ ] GitHub repo analysis for skill assessment
- [ ] Spaced-repetition flashcard generator
- [ ] Email / SMS study reminders

---

## 📄 License

MIT License – free for personal and commercial use.

---

> Built with ❤️ using IBM watsonx.ai Granite · Flask · Bootstrap 5
