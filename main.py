from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector, re
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------------ DB Connection ------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3307",
    database="chatbot"
)
cursor = db.cursor(dictionary=True)

# ------------------ Models ------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

# ------------------ User Sessions ------------------
USER_SESSIONS = {}

def get_session(session_id: str):
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = {
            "country": None,
            "category": None,
            "profile": None,
            "quality": [],
            "status": None,
            "rate": None
        }
    return USER_SESSIONS[session_id]

def reset_session(session_id: str):
    USER_SESSIONS[session_id] = {
        "country": None,
        "category": None,
        "profile": None,
        "quality": [],
        "status": None,
        "rate": None
    }

# ------------------ Helpers ------------------
def detect_country(msg: str) -> Optional[str]:
    msg = msg.lower()
    cursor.execute("SELECT DISTINCT country FROM ccrate")
    for r in cursor.fetchall():
        if r["country"].lower() in msg:
            return r["country"]
    return None

def detect_rate(msg: str) -> Optional[float]:
    m = re.findall(r"\d+\.\d+|\.\d+|\d+", msg)
    if m:
        try:
            return float(m[0])
        except:
            return None
    return None

def detect_category(msg: str) -> Optional[str]:
    if "cc" in msg.lower():
        return "CC"
    elif "cli" in msg.lower():
        return "CLI"
    return None

def detect_profile(msg: str) -> Optional[str]:
    if "ivr" in msg.lower():
        return "IVR"
    elif "outbound" in msg.lower():
        return "Outbound"
    return None

def detect_quality(msg: str):
    quality_keywords = ["local", "international", "random", "correct", "mobile", "fix"]
    found = []
    for q in quality_keywords:
        if q in msg.lower():
            found.append(q.capitalize())
    return found

def detect_status(msg: str):
    if "active" in msg.lower():
        return "Active"
    elif "inactive" in msg.lower():
        return "Inactive"
    return None

# ------------------ Main Bot Logic ------------------
def answer_rate_query(msg: str, session_id: str) -> str:
    state = get_session(session_id)
    msg = msg.lower().strip()
    print("msg",msg)
    # Detect all info from user message
    state["country"] = state["country"] or detect_country(msg)
    state["category"] = state["category"] or detect_category(msg)
    state["profile"] = state["profile"] or detect_profile(msg)
    state["quality"] = state["quality"] or detect_quality(msg)
    state["status"] = state["status"] or detect_status(msg)
    state["rate"] = state["rate"] or detect_rate(msg)

    # If country missing, ask
    if not state["country"]:
        return "Please specify the destination country."
    # If category missing, ask
    if not state["category"]:
        return f"Share which quality of {state['country']}? (CC or CLI)"
    # If profile missing, ask
    if not state["profile"]:
        return "Specify your profile (IVR or Outbound)."
    # If quality missing, ask
    if not state["quality"]:
        return "Do you want Local or International, Random or Correct, Mobile, or Fix?"

    # ✅ Build SQL query dynamically
    conditions = ["country=%s", "category=%s", "profile LIKE %s"]
    params = [state["country"], state["category"], f"%{state['profile']}%"]

    for q in state["quality"]:
        conditions.append("qualityDescription LIKE %s")
        params.append(f"%{q}%")

    if state["rate"]:
        conditions.append("rate=%s")
        params.append(state["rate"])

    if state["status"]:
        conditions.append("status=%s")
        params.append(state["status"])

    query = f"SELECT * FROM ccrate WHERE {' AND '.join(conditions)} ORDER BY addedTime DESC"
    cursor.execute(query, tuple(params))
    records = cursor.fetchall()

    if not records:
        reset_session(session_id)
        return f"No records found for {state['country']} with given filters."

    # Format output
    header = f"{'Country':<10} | {'Category':<10} | {'QualityDescription':<50} | {'Profile':<10} | {'BillingCycle':<12} | {'Rate':<6} | {'Status':<7}"
    lines = [header, "-" * len(header)]
    for r in records:
        lines.append(
            f"{r.get('country',''):<10} | {r.get('category',''):<10} | {r.get('qualityDescription',''):<50} | "
            f"{r.get('profile',''):<10} | {r.get('billingCycle',''):<12} | {r.get('rate',''):<6} | {r.get('status',''):<7}"
        )

    result = "\n".join(lines)
    reset_session(session_id)
    return result

# ------------------ Bot Response ------------------
def get_bot_response(message: str, session_id: str) -> str:
    return answer_rate_query(message, session_id)

# ------------------ Chat Endpoint ------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    return {"reply": get_bot_response(request.message, request.session_id)}
