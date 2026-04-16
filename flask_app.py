# -*- coding: utf-8 -*-
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from google import genai
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app, origins=["*"])

# إعداد Gemini
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBnUf97bdEt_WlLdC79LNX1lqRak1d5s_Y")
client = genai.Client(api_key=API_KEY)

# المنفذ من متغيرات البيئة (لـ Render)
PORT = int(os.environ.get("PORT", 8000))

def get_working_model():
    print("\n" + "="*60)
    print("البحث عن موديل Gemini شغال".center(60))
    print("="*60)
    
    try:
        print("\nجلب الموديلات المتاحة...")
        available_models = []
        for m in client.models.list():
            if hasattr(m, 'supported_actions') and 'generateContent' in str(m.supported_actions):
                model_name = m.name.replace('models/', '')
                available_models.append(model_name)
                print(f"✅ متاح: {model_name}")
        
        if available_models:
            chosen_model = available_models[0]
            print(f"\n🎯 استخدام: {chosen_model}")
            return chosen_model
        
    except Exception as e:
        print(f"خطأ في جلب الموديلات: {e}")
    
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"\n---> تجربة: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello"
            )
            if response and response.text:
                print(f"✅ الموديل يعمل: {model_name}")
                return model_name
        except:
            continue
    
    return "gemini-2.0-flash"

print("\nبدء تحميل الموديل...")
model_name = get_working_model()
print(f"\n🎯 الموديل المستخدم: {model_name}")

chat_sessions = {}
LOG_FILE = "conversations.log"

def save_conversation(session_id, user_message, bot_reply):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"الوقت: {timestamp}\n")
            f.write(f"الجلسة: {session_id}\n")
            f.write(f"المستخدم: {user_message}\n")
            f.write(f"البوت: {bot_reply}\n")
            f.write(f"{'='*60}\n")
        return True
    except:
        return False

@app.route('/')
def home():
    return serve_html()

@app.route('/test')
def test():
    return jsonify({
        "status": "success",
        "message": "✅ السيرفر شغال على Render",
        "model": model_name,
        "time": datetime.now().isoformat(),
        "host": request.host
    })

@app.route('/models')
def list_models():
    try:
        models_list = []
        for m in client.models.list():
            models_list.append({
                "name": m.name,
                "actions": m.supported_actions if hasattr(m, 'supported_actions') else []
            })
        return jsonify({
            "status": "success",
            "available_models": models_list,
            "current_model": model_name
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({"reply": "الرجاء كتابة رسالة", "status": "error"})
        
        system_prompt = """
        أنت مساعد متخصص في **تاريخ العائلة والأنساب**، اسمك "مرشد العائلة". 
        تحدث بالعربية الفصحى البسيطة. اتبع القواعد التالية:

        1. **التخصص**: ركز فقط على مواضيع تاريخ العائلة، الأنساب، تتبع الأجداد، 
           الوثائق التاريخية، DNA العائلي، وشجرة العائلة.
        2. **المهنية**: كن دقيقًا ومحايدًا. إذا سألك المستخدم عن شيء خارج تخصصك، 
           قل له بلطف إن هذا خارج نطاق اختصاصك.
        3. **التشجيع**: شجع المستخدم على مشاركة قصص عائلته وقدم نصائح عملية للبحث.
        4. **المصادر**: انصح بالمصادر الموثوقة (مثل دار الوثائق، مواقع الأنساب).
        5. **الخصوصية**: ذكر المستخدم بأهمية احترام خصوصية أفراد العائلة الأحياء.
        6. **التعامل مع الأدوية**: إذا سألك المستخدم عن دواء معين، لا تقدم أي نصيحة طبية. 
           لكن إذا قال لك إنه تناول دواء معين وتعبت، يمكنك تقديم تعزية بسيطة وتوجيهه لاستشارة الطبيب فورًا. 

        مثال لردودك: "أهلاً بك في رحلة اكتشاف تاريخ عائلتك! كيف يمكنني مساعدتك اليوم؟"
        """
        
        full_message = f"{system_prompt}\n\nالمستخدم: {user_message}\n\nالرد:"
        
        print(f"إرسال: {user_message[:50]}...")
        
        response = client.models.generate_content(
            model=model_name,
            contents=full_message
        )
        bot_reply = response.text
        print(f"استلام: {bot_reply[:50]}...")
        
        save_conversation(session_id, user_message, bot_reply)
        
        return jsonify({
            "reply": bot_reply,
            "session_id": session_id,
            "status": "success"
        })
        
    except Exception as e:
        error_message = str(e)
        print(f"خطأ: {error_message}")
        return jsonify({
            "reply": f"حدث خطأ: {error_message[:100]}",
            "status": "error"
        })

@app.route('/logs')
def view_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()[-50:]
                return jsonify({"status": "success", "logs": lines})
        else:
            return jsonify({"status": "success", "logs": ["لا توجد محادثات بعد"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/helper.html')
def serve_html():
    try:
        return send_file('helper.html')
    except:
        return "<h1>خطأ في تحميل الصفحة</h1>"

@app.route('/api_info')
def api_info():
    return jsonify({
        "name": "Family History Chatbot API",
        "version": "2.0",
        "model": model_name,
        "hosted_on": "Render",
        "endpoints": {
            "/": "الواجهة الرئيسية",
            "/test": "اختبار الاتصال",
            "/models": "قائمة الموديلات",
            "/chat": "محادثة (POST)",
            "/logs": "سجل المحادثات",
            "/api_info": "معلومات API"
        }
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 تشغيل Family History Chatbot على Render".center(70))
    print("="*70)
    print(f"\n✅ الموديل: {model_name}")
    print(f"✅ المنفذ: {PORT}")
    print("\n" + "="*70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)