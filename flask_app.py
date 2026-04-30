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

# إعداد Gemini - المفتاح الجديد
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAFRc9rkX6vB-UtDDvl7xgL1SJF8kBaAdk")
genai.configure(api_key=API_KEY)

# ========== System Prompt ==========
SYSTEM_PROMPT = """
أنت مساعد متخصص في **تاريخ العائلة والأنساب**، اسمك "مرشد العائلة". 
تحدث بالعربية الفصحى البسيطة. اتبع القواعد التالية:

1. **التخصص**: ركز فقط على مواضيع تاريخ العائلة، الأنساب، تتبع الأجداد، 
   الوثائق التاريخية، DNA العائلي، وشجرة العائلة.
2. **المهنية**: كن دقيقًا ومحايدًا.
3. **التشجيع**: شجع المستخدم على مشاركة قصص عائلته.
4. **الخصوصية**: ذكر المستخدم بأهمية احترام خصوصية أفراد العائلة.
5. **الإيجاز**: ردودك تكون مختصرة (2-4 جمل).

رد دائماً باللغة العربية.
"""

# ========== Get Working Model ==========
def get_working_model():
    """جلب أول موديل شغال من القائمة المتاحة"""
    
    print("\n🔍 جلب الموديلات المتاحة من Gemini API...")
    print("-" * 50)
    
    available_models = []
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_name = m.name.replace('models/', '')
                available_models.append(model_name)
                print(f"   ✅ متاح: {model_name}")
        
        print("-" * 50)
        
        if available_models:
            preferred_order = [
                "gemini-2.0-flash-exp",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
                "gemini-1.5-pro",
            ]
            
            for preferred in preferred_order:
                if preferred in available_models:
                    print(f"🎯 تم اختيار الموديل: {preferred}")
                    return preferred
            
            chosen = available_models[0]
            print(f"🎯 تم اختيار أول موديل متاح: {chosen}")
            return chosen
            
    except Exception as e:
        print(f"❌ خطأ في جلب الموديلات: {e}")
        return "gemini-1.5-flash"
    
    return "gemini-1.5-flash"

print("\n" + "="*60)
print("🚀 بدء تشغيل Family History Chatbot".center(60))
print("="*60)

MODEL_NAME = get_working_model()

print(f"\n✅ الموديل المستخدم: {MODEL_NAME}")
print("="*60)

# ========== Session Management ==========
chat_sessions = {}
chat_histories = {}

def get_or_create_chat(session_id):
    if session_id not in chat_sessions:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            chat = model.start_chat(history=[])
            chat.send_message(SYSTEM_PROMPT)
            chat_sessions[session_id] = chat
            chat_histories[session_id] = []
            print(f"✅ جلسة جديدة: {session_id[:8]}...")
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجلسة: {e}")
            raise
    return chat_sessions[session_id]

# ========== ENDPOINTS ==========

@app.route('/')
def home():
    try:
        return send_file('helper.html')
    except:
        return jsonify({
            "name": "Family History Chatbot API",
            "version": "3.0.0",
            "status": "online",
            "model": MODEL_NAME
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
            "/chat": "محادثة (POST)",
            "/mobile/chat/send": "محادثة للموبايل (POST)",
            "/mobile/session/create": "إنشاء جلسة (POST)",
            "/api_info": "معلومات API"
        }
    })

@app.route('/models')
def list_models():
    try:
        models_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_name = m.name.replace('models/', '')
                models_list.append(model_name)
        return jsonify({
            "status": "success",
            "current_model": MODEL_NAME,
            "available_models": models_list,
            "total": len(models_list)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ========== MAIN CHAT ==========
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({"reply": "الرجاء كتابة رسالة", "status": "error"})
        
        chat_session = get_or_create_chat(session_id)
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
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
        error_msg = str(e)
        print(f"❌ خطأ: {error_msg}")
        return jsonify({
            "reply": f"حدث خطأ: {error_msg[:150]}",
            "status": "error"
        }), 500

# ========== MOBILE ENDPOINTS ==========

@app.route('/mobile/session/create', methods=['POST', 'GET'])
def mobile_create_session():
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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mobile/chat/send', methods=['POST'])
def mobile_chat_send():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({"success": False, "reply": "الرجاء كتابة رسالة"})
        
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            model = genai.GenerativeModel(MODEL_NAME)
            chat = model.start_chat(history=[])
            chat.send_message(SYSTEM_PROMPT)
            chat_sessions[session_id] = chat
            chat_histories[session_id] = []
        
        chat_session = chat_sessions[session_id]
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
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
        return jsonify({"success": False, "reply": f"خطأ: {str(e)[:150]}"}), 500

@app.route('/mobile/chat/history/<session_id>', methods=['GET'])
def mobile_get_history(session_id):
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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mobile/session/<session_id>', methods=['DELETE'])
def mobile_delete_session(session_id):
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        if session_id in chat_histories:
            del chat_histories[session_id]
        return jsonify({"success": True, "message": "Session deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mobile/status', methods=['GET'])
def mobile_status():
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

# ========== Run ==========
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
    print("\n" + "="*70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
