"""
agent.py – LearnMate AI Agent Core
===================================
Calls the IBM watsonx.ai REST API directly using `requests`.
This approach is compatible with Python 3.8+ and does not depend
on any specific version of the IBM SDK.

Edit the AGENT_INSTRUCTIONS dict below to fully customise the
agent's personality, strategy, domains, and safety rules without
touching any other file.
"""

import os
import json
import re
import requests

# ─────────────────────────────────────────────────────────────────────────────
#  AGENT INSTRUCTIONS  ← customise everything here
# ─────────────────────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {
    # ── Identity ──────────────────────────────────────────────────────────────
    "name": "LearnMate",
    "role": "Agentic AI Learning Companion & Career Coach",
    "tagline": "Your personalised guide from curious beginner to confident professional.",

    # ── Communication Style ───────────────────────────────────────────────────
    "communication_style": (
        "Warm, encouraging, and conversational. "
        "Use simple language; avoid unnecessary jargon. "
        "When technical terms are unavoidable, briefly define them. "
        "Ask one clarifying question at a time - never overwhelm the student. "
        "Celebrate milestones with genuine enthusiasm."
    ),

    # ── Recommendation Strategy ───────────────────────────────────────────────
    "recommendation_strategy": (
        "1. Assess the student's current knowledge before recommending resources. "
        "2. Always recommend free resources first, then paid alternatives. "
        "3. Prioritise project-based learning - hands-on beats reading alone. "
        "4. Sequence topics logically: foundations -> core skills -> advanced topics. "
        "5. Include estimated hours per resource so students can plan realistically. "
        "6. Revisit and refine recommendations after each completed milestone. "
        "7. Tailor difficulty to the student's stated experience level."
    ),

    # ── Learning Style Preferences ────────────────────────────────────────────
    "learning_styles": [
        "Visual (videos, diagrams, mind-maps)",
        "Reading/Writing (docs, tutorials, note-taking)",
        "Kinesthetic (projects, coding challenges, labs)",
        "Auditory (podcasts, lectures, study groups)",
    ],

    # ── Supported Domains ────────────────────────────────────────────────────
    "supported_domains": [
        "Frontend Development",
        "Backend Development",
        "Full Stack Development",
        "Cybersecurity",
        "Artificial Intelligence",
        "Machine Learning",
        "Data Science",
        "Cloud Computing",
        "UI/UX Design",
        "DevOps",
        "Mobile App Development",
        "Blockchain Development",
        "Game Development",
        "Embedded Systems & IoT",
        "Database Engineering",
        "Site Reliability Engineering",
    ],

    # ── Career Focus ──────────────────────────────────────────────────────────
    "career_focus": (
        "Help students map skills to real job titles, salary ranges, and growth paths. "
        "Highlight which certifications are most valued by employers. "
        "Suggest portfolio project ideas that impress hiring managers. "
        "Mention in-demand tools and frameworks for each role in 2024-2025."
    ),

    # ── Roadmap Structure ─────────────────────────────────────────────────────
    "roadmap_phases": {
        "beginner":     "Weeks 1-4  - Foundations & core concepts",
        "intermediate": "Weeks 5-12 - Applied skills & first projects",
        "advanced":     "Weeks 13-24 - Specialisation, certifications & portfolio",
    },

    # ── Safety & Ethical Guidelines ───────────────────────────────────────────
    "safety_guidelines": (
        "Never share, store, or request personal identifying information. "
        "Do not recommend pirated or illegal course materials. "
        "Acknowledge AI limitations - always suggest consulting human mentors for "
        "career-critical decisions. "
        "Keep responses factual; clearly label estimates as estimates. "
        "Refuse requests unrelated to learning, career, or technology topics."
    ),

    # ── Adaptive Learning Rules ───────────────────────────────────────────────
    "adaptive_rules": (
        "If a student reports confusion, step back to prerequisite topics. "
        "If a student completes tasks faster than expected, accelerate the timeline. "
        "Track completed milestones and never repeat already-learned content unless "
        "the student asks for a refresher. "
        "Adjust weekly study hours based on the student's available time."
    ),

    # ── Output Format ─────────────────────────────────────────────────────────
    "output_format": (
        "Structure longer responses with clear headings (##). "
        "Use bullet points for lists of resources or steps. "
        "When generating a roadmap, output valid JSON wrapped in ```json ... ```. "
        "Keep chat replies under 300 words unless a full roadmap is requested."
    ),
}
# ─────────────────────────────────────────────────────────────────────────────
#  END OF AGENT_INSTRUCTIONS
# ─────────────────────────────────────────────────────────────────────────────


# ── IBM IAM token cache (in-process, reset on restart) ───────────────────────
_iam_token_cache = {"token": None, "expires_at": 0}


def _get_iam_token():
    """Fetch a short-lived IAM bearer token from IBM Cloud, cached for 50 min."""
    import time
    if _iam_token_cache["token"] and time.time() < _iam_token_cache["expires_at"]:
        return _iam_token_cache["token"]

    api_key = os.getenv("IBM_API_KEY", "")
    if not api_key:
        raise ValueError(
            "IBM_API_KEY is not set. Add it to your .env file."
        )

    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type":  "urn:ibm:params:oauth:grant-type:apikey",
            "apikey":      api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _iam_token_cache["token"] = data["access_token"]
    _iam_token_cache["expires_at"] = time.time() + 3000  # ~50 min
    return _iam_token_cache["token"]


def _call_granite(prompt, max_new_tokens=1200):
    """
    Call the watsonx.ai text-generation REST endpoint directly.

    Parameters
    ----------
    prompt : str
        Full prompt string in Granite instruct format.
    max_new_tokens : int
        Maximum tokens to generate.

    Returns
    -------
    str
        The generated text, or an error message prefixed with "ERROR:".
    """
    base_url   = os.getenv("WATSONX_URL",      "https://us-south.ml.cloud.ibm.com")
    model_id   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")

    if not project_id:
        return (
            "ERROR: WATSONX_PROJECT_ID is not set. "
            "Add it to your .env file (watsonx.ai project -> Manage -> Project ID)."
        )

    endpoint = "{}/ml/v1/text/generation?version=2023-05-29".format(base_url)
    try:
        token = _get_iam_token()
    except Exception as exc:
        return "ERROR: Could not obtain IAM token: {}".format(exc)

    payload = {
        "model_id":   model_id,
        "project_id": project_id,
        "input":      prompt,
        "parameters": {
            "max_new_tokens":     max_new_tokens,
            "temperature":        0.7,
            "top_p":              0.9,
            "repetition_penalty": 1.1,
        },
    }

    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": "Bearer {}".format(token),
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        # watsonx.ai response structure:
        # {"results": [{"generated_text": "..."}]}
        generated = result.get("results", [{}])[0].get("generated_text", "")
        return generated.strip()
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json()
        except Exception:
            detail = str(exc)
        return "ERROR: watsonx.ai HTTP error: {}".format(detail)
    except Exception as exc:
        return "ERROR: {}".format(exc)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_system_prompt():
    """Compile AGENT_INSTRUCTIONS into the system prompt string."""
    ai = AGENT_INSTRUCTIONS
    domains_list = "\n".join("  - {}".format(d) for d in ai["supported_domains"])
    phases = "\n".join("  {}: {}".format(k, v) for k, v in ai["roadmap_phases"].items())
    styles = "\n".join("  - {}".format(s) for s in ai["learning_styles"])

    return (
        "You are {name}, {role}.\n"
        "Tagline: {tagline}\n\n"
        "COMMUNICATION STYLE:\n{comm}\n\n"
        "RECOMMENDATION STRATEGY:\n{rec}\n\n"
        "LEARNING STYLES YOU SUPPORT:\n{styles}\n\n"
        "SUPPORTED TECHNOLOGY DOMAINS:\n{domains}\n\n"
        "CAREER FOCUS:\n{career}\n\n"
        "ROADMAP PHASES:\n{phases}\n\n"
        "ADAPTIVE LEARNING:\n{adaptive}\n\n"
        "OUTPUT FORMAT:\n{fmt}\n\n"
        "SAFETY GUIDELINES:\n{safety}\n"
    ).format(
        name=ai["name"],
        role=ai["role"],
        tagline=ai["tagline"],
        comm=ai["communication_style"],
        rec=ai["recommendation_strategy"],
        styles=styles,
        domains=domains_list,
        career=ai["career_focus"],
        phases=phases,
        adaptive=ai["adaptive_rules"],
        fmt=ai["output_format"],
        safety=ai["safety_guidelines"],
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_agent(user_message, history):
    """
    Send a student message to Granite and return the reply.

    Parameters
    ----------
    user_message : str
    history : list[dict]  – [{"role": "user"|"assistant", "content": str}, ...]

    Returns
    -------
    str
    """
    system_prompt = _build_system_prompt()

    # Granite instruct format: <|system|> ... <|user|> ... <|assistant|>
    conversation = "<|system|>\n{}\n".format(system_prompt)
    for turn in history[-10:]:
        role_tag = "<|user|>" if turn["role"] == "user" else "<|assistant|>"
        conversation += "{}\n{}\n".format(role_tag, turn["content"])
    conversation += "<|user|>\n{}\n<|assistant|>\n".format(user_message)

    reply = _call_granite(conversation, max_new_tokens=800)

    if reply.startswith("ERROR:"):
        return (
            "I encountered an issue connecting to the AI service.\n\n"
            "**Details:** {}\n\n"
            "Please check your `.env` file credentials and try again."
        ).format(reply[6:].strip())

    return reply or "I'm sorry, I couldn't generate a response. Please try again."


def generate_roadmap(profile):
    """
    Generate a structured JSON learning roadmap for the given student profile.

    Parameters
    ----------
    profile : dict
        Keys: name, domain, experience_level, learning_style,
              weekly_hours, career_goal, background

    Returns
    -------
    dict  (roadmap JSON or fallback)
    """
    system_prompt = _build_system_prompt()

    prompt = (
        "<|system|>\n{system}\n"
        "<|user|>\n"
        "Generate a detailed personalised learning roadmap as valid JSON for:\n\n"
        "Name: {name}\n"
        "Target Domain: {domain}\n"
        "Experience Level: {level}\n"
        "Learning Style: {style}\n"
        "Weekly Study Hours: {hours}\n"
        "Career Goal: {goal}\n"
        "Background: {bg}\n\n"
        "Output ONLY this JSON structure (no extra text):\n"
        "{{\n"
        '  "student": "{name}",\n'
        '  "domain": "{domain}",\n'
        '  "career_goal": "{goal}",\n'
        '  "total_weeks": 24,\n'
        '  "phases": [\n'
        "    {{\n"
        '      "phase": "Beginner", "weeks": "1-4",\n'
        '      "goal": "Phase goal",\n'
        '      "topics": ["topic1", "topic2"],\n'
        '      "resources": [{{"title":"Resource","type":"Course","platform":"Site",'
        '"url":"https://example.com","hours":20,"free":true}}],\n'
        '      "milestones": ["milestone1"],\n'
        '      "projects": ["project1"]\n'
        "    }},\n"
        "    {{\n"
        '      "phase": "Intermediate", "weeks": "5-12",\n'
        '      "goal": "Phase goal",\n'
        '      "topics": ["topic1"],\n'
        '      "resources": [{{"title":"Resource","type":"Course","platform":"Site",'
        '"url":"https://example.com","hours":40,"free":true}}],\n'
        '      "milestones": ["milestone1"],\n'
        '      "projects": ["project1"]\n'
        "    }},\n"
        "    {{\n"
        '      "phase": "Advanced", "weeks": "13-24",\n'
        '      "goal": "Phase goal",\n'
        '      "topics": ["topic1"],\n'
        '      "resources": [{{"title":"Resource","type":"Course","platform":"Site",'
        '"url":"https://example.com","hours":60,"free":false}}],\n'
        '      "milestones": ["milestone1"],\n'
        '      "projects": ["project1"]\n'
        "    }}\n"
        "  ],\n"
        '  "certifications": [{{"name":"Cert","provider":"Provider","level":"Beginner"}}],\n'
        '  "weekly_plan": {{"monday":"Study","tuesday":"Practice","wednesday":"Project",'
        '"thursday":"Review","friday":"Project","saturday":"Explore","sunday":"Rest"}},\n'
        '  "skill_gaps": ["skill1"],\n'
        '  "estimated_completion": "6 months"\n'
        "}}\n"
        "<|assistant|>\n"
    ).format(
        system=system_prompt,
        name=profile.get("name", "Student"),
        domain=profile.get("domain", "Full Stack Development"),
        level=profile.get("experience_level", "Beginner"),
        style=profile.get("learning_style", "Visual"),
        hours=profile.get("weekly_hours", 10),
        goal=profile.get("career_goal", "Software Engineer"),
        bg=profile.get("background", "None"),
    )

    raw = _call_granite(prompt, max_new_tokens=2000)

    if raw.startswith("ERROR:"):
        return _fallback_roadmap(profile)

    # Try to parse JSON from the response
    try:
        json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
        json_str = json_match.group(1) if json_match else raw.strip()
        return json.loads(json_str)
    except (ValueError, KeyError):
        return _fallback_roadmap(profile)


def assess_skills(domain, answers):
    """
    Analyse quiz answers and return an AI skill assessment report.

    Parameters
    ----------
    domain : str
    answers : list[dict]  – [{"question":str,"answer":str,"correct":bool}, ...]

    Returns
    -------
    dict  {score, level, strengths, skill_gaps, next_steps, ...}
    """
    system_prompt = _build_system_prompt()
    score = sum(1 for a in answers if a.get("correct", False))
    total = len(answers)
    percentage = round((score / total) * 100) if total else 0

    prompt = (
        "<|system|>\n{system}\n"
        "<|user|>\n"
        "A student completed a {domain} skill assessment.\n"
        "Score: {score}/{total} ({pct}%)\n\n"
        "Questions and answers:\n{answers}\n\n"
        "Return ONLY this JSON (no extra text):\n"
        "{{\n"
        '  "score": {score},\n'
        '  "total": {total},\n'
        '  "percentage": {pct},\n'
        '  "level": "Beginner",\n'
        '  "strengths": ["area1", "area2"],\n'
        '  "skill_gaps": ["gap1", "gap2"],\n'
        '  "next_steps": ["step1", "step2"],\n'
        '  "recommended_resources": ["resource1"],\n'
        '  "encouragement": "A short motivational message."\n'
        "}}\n"
        "<|assistant|>\n"
    ).format(
        system=system_prompt,
        domain=domain,
        score=score,
        total=total,
        pct=percentage,
        answers=json.dumps(answers, indent=2),
    )

    raw = _call_granite(prompt, max_new_tokens=600)

    if not raw.startswith("ERROR:"):
        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
            json_str = json_match.group(1) if json_match else raw.strip()
            return json.loads(json_str)
        except Exception:
            pass  # fall through to static fallback

    level = (
        "Beginner" if percentage < 40
        else ("Intermediate" if percentage < 75 else "Advanced")
    )
    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "level": level,
        "strengths": [],
        "skill_gaps": [],
        "next_steps": [
            "Review foundational concepts",
            "Practice daily coding challenges",
        ],
        "recommended_resources": [],
        "encouragement": "Every expert was once a beginner. Keep going!",
    }


def _fallback_roadmap(profile):
    """Return a minimal static roadmap when the AI call fails or credentials are missing."""
    domain = profile.get("domain", "Full Stack Development")
    return {
        "student":      profile.get("name", "Student"),
        "domain":       domain,
        "career_goal":  profile.get("career_goal", "Software Developer"),
        "total_weeks":  24,
        "phases": [
            {
                "phase":  "Beginner",
                "weeks":  "1-4",
                "goal":   "Build foundational knowledge in {}".format(domain),
                "topics": ["Core concepts", "Development environment setup",
                           "Hello World projects", "Basic syntax"],
                "resources": [
                    {"title": "freeCodeCamp", "type": "Course",
                     "platform": "freeCodeCamp",
                     "url": "https://www.freecodecamp.org",
                     "hours": 20, "free": True},
                    {"title": "W3Schools", "type": "Documentation",
                     "platform": "W3Schools",
                     "url": "https://www.w3schools.com",
                     "hours": 10, "free": True},
                ],
                "milestones": ["Complete first project", "Understand core syntax"],
                "projects":   ["Personal portfolio page", "Simple calculator app"],
            },
            {
                "phase":  "Intermediate",
                "weeks":  "5-12",
                "goal":   "Apply skills through real projects",
                "topics": ["Frameworks & libraries", "APIs & databases",
                           "Version control with Git", "Testing basics"],
                "resources": [
                    {"title": "The Odin Project", "type": "Course",
                     "platform": "The Odin Project",
                     "url": "https://www.theodinproject.com",
                     "hours": 40, "free": True},
                    {"title": "Codecademy", "type": "Course",
                     "platform": "Codecademy",
                     "url": "https://www.codecademy.com",
                     "hours": 30, "free": False},
                ],
                "milestones": ["Build a full CRUD app", "Deploy a project online"],
                "projects":   ["Blog platform", "Todo app with backend"],
            },
            {
                "phase":  "Advanced",
                "weeks":  "13-24",
                "goal":   "Specialise, get certified, and build a portfolio",
                "topics": ["System design", "Testing & CI/CD",
                           "Performance optimisation", "Interview prep"],
                "resources": [
                    {"title": "Coursera Professional Certificates",
                     "type": "Course", "platform": "Coursera",
                     "url": "https://www.coursera.org",
                     "hours": 60, "free": False},
                    {"title": "LeetCode", "type": "Challenge",
                     "platform": "LeetCode",
                     "url": "https://www.leetcode.com",
                     "hours": 40, "free": True},
                ],
                "milestones": ["Earn a professional certification",
                               "Complete a capstone project"],
                "projects":   ["Capstone portfolio project",
                               "Open-source contribution"],
            },
        ],
        "certifications": [
            {"name": "Relevant Professional Certificate",
             "provider": "Coursera / edX / Google",
             "level": "Professional"},
        ],
        "weekly_plan": {
            "monday":    "New topic study (1-2 hrs)",
            "tuesday":   "Video tutorials & notes (1-2 hrs)",
            "wednesday": "Project work (2 hrs)",
            "thursday":  "Review & coding exercises (1 hr)",
            "friday":    "Project work (2 hrs)",
            "saturday":  "Side project or exploration (2-3 hrs)",
            "sunday":    "Rest / light review",
        },
        "skill_gaps":            ["Determined after completing your assessment"],
        "estimated_completion":  "6 months",
    }
