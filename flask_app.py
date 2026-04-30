# -*- coding: utf-8 -*-
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import uuid
import google.generativeai as genai

app = Flask(__name__)
CORS(app, origins=["*"])

# إعداد Gemini
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAFRc9rkX6vB-UtDDvl7xgL1SJF8kBaAdk")
genai.configure(api_key=API_KEY)

# ========== System Prompt ==========
SYSTEM_PROMPT = """
أنت مساعد متخصص في **تاريخ العائلة والأنساب**، اسمك "مرشد العائلة". 
تحدث بالعربية الفصحى البسيطة. اتبع القواعد التالية:

1. **التخصص**: ركز فقط على مواضيع تاريخ العائلة، الأنساب، تتبع الأجداد، 
   الوثائق التاريخية، DNA العائلي، وشجرة العائلة.
2. **المهنية**: كن دقيقًا ومحايدًا. إذا سألك المستخدم عن شيء خارج تخصصك، 
   قل له بلطف إن هذا خارج نطاق اختصاصك.
3. **التشجيع**: شجع المستخدم على مشاركة قصص عائلته وقدم نصائح عملية للبحث.
4. **المصادر**: انصح بالمصادر الموثوقة في مصر.
5. **الخصوصية**: ذكر المستخدم بأهمية احترام خصوصية أفراد العائلة الأحياء.
6. **الإيجاز**: ردودك تكون مختصرة (2-4 جمل) مناسبة للعرض على الجوال.

رد باللغة العربية او الانجليزيه علي حسب لغه المتكلم.
"""

# ========== Get Working Model ==========
def get_working_model():
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            model.generate_content("test")
            print(f"✅ Using model: {model_name}")
            return model_name
        except:
            continue
    
    return "gemini-1.5-flash"

print("\n🚀 Starting Family History Chatbot on Vercel...")
MODEL_NAME = get_working_model()
print(f"📊 Model: {MODEL_NAME}")

# ========== Session Management ==========
chat_sessions = {}
chat_histories = {}

def get_or_create_chat(session_id):
    if session_id not in chat_sessions:
        model = genai.GenerativeModel(MODEL_NAME)
        chat = model.start_chat(history=[])
        chat.send_message(SYSTEM_PROMPT)
        chat_sessions[session_id] = chat
        chat_histories[session_id] = []
    return chat_sessions[session_id]

# ========== ENDPOINTS (نفس الأسماء) ==========

@app.route('/')
def home():
    try:
        return send_file('helper.html')
    except:
        return jsonify({
            "name": "Family History Chatbot API",
            "version": "3.0.0",
            "status": "online",
            "endpoints": ["/test", "/chat", "/api_info", "/mobile/chat/send"]
        })

@app.route('/test')
def test():
    return jsonify({
        "status": "success",
        "message": "✅ السيرفر شغال على Vercel",
        "model": MODEL_NAME,
        "time": datetime.now().isoformat()
    })

@app.route('/api_info')
def api_info():
    return jsonify({
        "name": "Family History Chatbot API",
        "version": "3.0.0",
        "model": MODEL_NAME,
        "hosted_on": "Vercel",
        "endpoints": {
            "/": "الواجهة الرئيسية",
            "/test": "اختبار الاتصال",
            "/chat": "محادثة (POST) - للتطبيق والويب",
            "/mobile/chat/send": "محادثة (POST) - مخصص للموبايل",
            "/mobile/session/create": "إنشاء جلسة جديدة (POST)",
            "/mobile/chat/history/<session_id>": "تاريخ المحادثة (GET)",
            "/api_info": "معلومات API"
        }
    })

# ========== MAIN CHAT (نفس الاسم والطريقة) ==========
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({"reply": "الرجاء كتابة رسالة", "status": "error"})
        
        # Get or create chat session
        chat_session = get_or_create_chat(session_id)
        
        # Send message
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
        # Save to history
        if session_id in chat_histories:
            chat_histories[session_id].append({
                "user": user_message,
                "bot": bot_reply,
                "time": datetime.now().isoformat()
            })
        
        return jsonify({
            "reply": bot_reply,
            "session_id": session_id,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "reply": f"حدث خطأ: {str(e)[:100]}",
            "status": "error"
        })

# ========== MOBILE OPTIMIZED ENDPOINTS (جديدة للربط مع التطبيق) ==========

@app.route('/mobile/session/create', methods=['POST', 'GET'])
def mobile_create_session():
    """إنشاء جلسة جديدة - للتطبيق"""
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        
        session_id = str(uuid.uuid4())
        model = genai.GenerativeModel(MODEL_NAME)
        chat = model.start_chat(history=[])
        chat.send_message(SYSTEM_PROMPT)
        
        chat_sessions[session_id] = chat
        chat_histories[session_id] = []
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mobile/chat/send', methods=['POST'])
def mobile_chat_send():
    """إرسال رسالة من التطبيق - Endpoint مخصص للموبايل"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        
        if not user_message:
            return jsonify({
                "success": False,
                "reply": "الرجاء كتابة رسالة"
            })
        
        # Create session if not exists
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            model = genai.GenerativeModel(MODEL_NAME)
            chat = model.start_chat(history=[])
            chat.send_message(SYSTEM_PROMPT)
            chat_sessions[session_id] = chat
            chat_histories[session_id] = []
        
        # Send message
        chat_session = chat_sessions[session_id]
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
        # Save to history
        message_id = str(uuid.uuid4())
        chat_histories[session_id].append({
            "id": message_id,
            "user": user_message,
            "bot": bot_reply,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "reply": bot_reply,
            "session_id": session_id,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Mobile chat error: {str(e)}")
        return jsonify({
            "success": False,
            "reply": f"خطأ: {str(e)[:100]}"
        }), 500

@app.route('/mobile/chat/history/<session_id>', methods=['GET'])
def mobile_get_history(session_id):
    """جلب تاريخ المحادثة - للتطبيق"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if session_id not in chat_histories:
            return jsonify({
                "success": True,
                "session_id": session_id,
                "messages": [],
                "total": 0,
                "has_more": False
            })
        
        messages = chat_histories[session_id]
        total = len(messages)
        paginated = messages[offset:offset + limit]
        has_more = (offset + limit) < total
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "messages": paginated,
            "total": total,
            "has_more": has_more
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mobile/session/<session_id>', methods=['DELETE'])
def mobile_delete_session(session_id):
    """حذف جلسة - للتطبيق"""
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        if session_id in chat_histories:
            del chat_histories[session_id]
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Session deleted"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mobile/status', methods=['GET'])
def mobile_status():
    """فحص الاتصال - للتطبيق"""
    return jsonify({
        "success": True,
        "status": "online",
        "version": "3.0.0",
        "model": MODEL_NAME,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/helper.html')
def serve_html():
    try:
        return send_file('helper.html')
    except:
        return jsonify({"error": "helper.html not found"}), 404

@app.route('/models')
def list_models():
    try:
        models_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_list.append(m.name)
        return jsonify({
            "status": "success",
            "available_models": models_list[:10],
            "current_model": MODEL_NAME
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ========== Run (for local testing) ==========
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 8000))
    print("\n" + "="*70)
    print("🚀 Family History Chatbot on Vercel".center(70))
    print("="*70)
    print(f"\n✅ Model: {MODEL_NAME}")
    print(f"✅ Port: {PORT}")
    print("\n📱 Mobile Endpoints:")
    print("   POST   /mobile/session/create")
    print("   POST   /mobile/chat/send")
    print("   GET    /mobile/chat/history/<id>")
    print("   DELETE /mobile/session/<id>")
    print("   GET    /mobile/status")
    print("\n💬 Main Endpoints:")
    print("   POST   /chat")
    print("   GET    /test")
    print("   GET    /api_info")
    print("\n" + "="*70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
