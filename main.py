# =======================================================================
# 👑 JSM AI
# 🚀 Fixed Packages + 1-Min Daily 2 Free Videos + Download-Based Deduction
# =======================================================================
from flask import Flask, request, jsonify
import os, jwt, datetime
from functools import wraps

app = Flask(__name__)

# کیز رینڈر کے ڈیش بورڈ سے آئیں گی، یہاں لکھنے کی ضرورت نہیں
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "motha_boss_secret_2026")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JAZZCASH_NUMBER = "03199084360"
EASYPAISA_NUMBER = "03199084360" 

PACKAGES = {
    "Starter": {"minutes": 300, "price": 3000},
    "Pro": {"minutes": 500, "price": 5000}, 
    "Master": {"minutes": 850, "price": 8000}
}

PENDING_DEDUCTIONS = {}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            token_clean = token.replace("Bearer ", "")
            data = jwt.decode(token_clean, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['email']
        except:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def shorten_script_to_1min(script):
    words = script.split()
    if len(words) <= 130: return script
    return " ".join(words[:130])

def generate_youtube_seo(script):
    words = script.split()
    title_seed = " ".join(words[:5]) if len(words) > 5 else "Financial Insights"
    title = f"👑 {title_seed.title()} | Global Trends Explained"
    description = f"This automated video breaks down key global dynamics.\n\n📜 Transcript Preview:\n{ ' '.join(words[:30]) }...\n\n🔔 Subscribe to JSM AI!"
    hashtags = "#finance #globaltrends #jsmai"
    return {"title": title, "description": description, "hashtags": hashtags}

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").lower()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400
        
    token = jwt.encode({
        'email': email,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({"token": token, "message": "Login OK"})

@app.route("/generate", methods=["POST"])
@token_required
def generate_video(current_user):
    data = request.get_json() or {}
    script = data.get("script", "")
    if not script:
        return jsonify({"error": "Script text is required"}), 400
        
    user = get_user_from_db(current_user)
    
    if user['plan'] == "Free Trial" and user['videos_today'] >= 2:
        return jsonify({
            "status": "payment_required",
            "message": "جانی! روزانہ کی 2 فری ویڈیوز کا کوٹہ مکمل ہو چکا ہے ✅",
            "payment_info": f"JazzCash/Easypaisa: {JAZZCASH_NUMBER}\nپیسے بھیج کر اسکرین شاٹ واٹس ایپ کریں، پیکیج 5 منٹ میں ایکٹیو ہو جائے گا۔"
        }), 402
    
    if user['plan'] == "Free Trial":
        script = shorten_script_to_1min(script)
        target_minutes = 1.0
    else:
        target_minutes = round(len(script.split()) / 130, 2)
    
    if user['minutes_left'] < target_minutes and user['plan'] != "Free Trial":
        return jsonify({
            "status": "no_minutes",
            "message": f"بھائی منٹ ختم! آپ کے پاس {user['minutes_left']} منٹ بچے ہیں۔ مطلوبہ: {target_minutes} منٹ۔"
        }), 402
    
    generated_video_link = "https://gofile.io/temp-jsm-video-file.mp4"
    seo_metadata = generate_youtube_seo(script)
    
    job_id = os.urandom(6).hex()
    PENDING_DEDUCTIONS[job_id] = {
        "email": current_user,
        "minutes": target_minutes,
        "is_free": user['plan'] == "Free Trial"
    }
    
    return jsonify({
        "status": "success", 
        "job_id": job_id,
        "video_url": generated_video_link,
        "minutes_to_be_deducted": target_minutes,
        "youtube_seo": seo_metadata,
        "msg": "ویڈیو تیار ہے جانی! منٹ تبھی کٹیں گے جب ڈاؤن لوڈ کرو گے۔"
    })

@app.route("/claim-video", methods=["POST"])
@token_required
def claim_video(current_user):
    data = request.get_json() or {}
    job_id = data.get("job_id")
    if not job_id or job_id not in PENDING_DEDUCTIONS:
        return jsonify({"error": "Invalid or expired session"}), 400
        
    session = PENDING_DEDUCTIONS[job_id]
    if session["email"] != current_user:
        return jsonify({"error": "Unauthorized"}), 403
        
    if not session["is_free"]:
        deduct_minutes(current_user, session["minutes"])
    else:
        add_video_count(current_user)
        
    del PENDING_DEDUCTIONS[job_id]
    return jsonify({"status": "claimed", "message": "Minutes deducted successfully upon download!"})

def get_user_from_db(email):
    return {"plan": "Free Trial", "minutes_left": 0.0, "videos_today": 0}

def deduct_minutes(email, minutes):
    pass

def add_video_count(email):
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
  
