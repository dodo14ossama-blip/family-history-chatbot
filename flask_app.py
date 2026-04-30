# -*- coding: utf-8 -*-
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from google import genai
from datetime import datetime
import uuid
import json

app = Flask(__name__)
CORS(app, origins=["*"])

# ========== إعداد Gemini ==========
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAFRc9rkX6vB-UtDDvl7xgL1SJF8kBaAdk")
client = genai.Client(api_key=API_KEY)

PORT = int(os.environ.get("PORT", 8000))

# ========== System Prompt (نفس البرومبت بتاعك) ==========
SYSTEM_PROMPT = """
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

# ========== إعداد Swagger UI ==========
SWAGGER_URL = '/swagger'
API_SPEC_URL = '/swagger.json'

@app.route('/swagger.json')
def swagger_json():
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Family History Chatbot API",
            "description": SYSTEM_PROMPT,
            "version": "2.0.0",
            "contact": {
                "name": "Family History Support"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Current Server"
            }
        ],
        "paths": {
            "/test": {
                "get": {
                    "summary": "اختبار الاتصال",
                    "description": "فحص ما إذا كان السيرفر يعمل بشكل صحيح",
                    "responses": {
                        "200": {
                            "description": "السيرفر يعمل",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "success",
                                        "message": "✅ السيرفر شغال",
                                        "model": "gemini-2.0-flash"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/chat": {
                "post": {
                    "summary": "إرسال رسالة إلى المساعد",
                    "description": "أرسل رسالة واحصل على رد من المساعد المتخصص في تاريخ العائلة",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {
                                            "type": "string",
                                            "example": "كيف أبدأ في تتبع تاريخ عائلتي؟"
                                        },
                                        "session_id": {
                                            "type": "string",
                                            "example": "session_123"
                                        }
                                    },
                                    "required": ["message"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "الرد من المساعد",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "reply": "أهلاً بك! للبدء...",
                                        "session_id": "session_123",
                                        "status": "success"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/mobile/status": {
                "get": {
                    "summary": "فحص الاتصال (للموبايل)",
                    "description": "Endpoint مخصص للتطبيقات المحمولة لفحص حالة السيرفر",
                    "responses": {
                        "200": {
                            "description": "حالة السيرفر",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "success": True,
                                        "status": "online",
                                        "version": "2.0.0"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/mobile/session/create": {
                "post": {
                    "summary": "إنشاء جلسة جديدة (للموبايل)",
                    "description": "إنشاء جلسة محادثة جديدة من التطبيق",
                    "responses": {
                        "200": {
                            "description": "تم إنشاء الجلسة بنجاح"
                        }
                    }
                }
            },
            "/mobile/chat/send": {
                "post": {
                    "summary": "إرسال رسالة (للموبايل)",
                    "description": "إرسال رسالة والحصول على رد - مخصص للتطبيقات المحمولة",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "session_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "الرد من المساعد"
                        }
                    }
                }
            },
            "/mobile/chat/history/{session_id}": {
                "get": {
                    "summary": "تاريخ المحادثة (للموبايل)",
                    "description": "جلب تاريخ رسائل جلسة معينة",
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "تاريخ المحادثة"
                        }
                    }
                }
            }
        }
    })

# Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_SPEC_URL,
    config={'app_name': "Family History Chatbot API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# ========== إيجاد الموديل الشغال ==========
def get_working_model():
    print("\n" + "="*60)
    print("البحث عن موديل Gemini شغال".center(60))
    print("="*60)
    
    # الموديلات الجديدة حسب التوثيق
    models_to_try = [
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-001", 
        "gemini-1.5-pro",
        "gemini-1.5-pro-001",
    ]
    
    for model_name in models_to_try:
        try:
            print(f"\n---> تجربة: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents="قل مرحبا"
            )
            if response and response.text:
                print(f"✅ الموديل يعمل: {model_name}")
                return model_name
        except Exception as e:
            error = str(e)
            if "404" in error:
                print(f"   ❌ غير موجود")
            elif "quota" in error.lower():
                print(f"   ❌ حصة منتهية")
            else:
                print(f"   ❌ {error[:50]}")
            continue
    
    print("\n⚠️ جاري البحث عن أي موديل متاح...")
    try:
        for m in client.models.list():
            if hasattr(m, 'supported_actions') and 'generateContent' in str(m.supported_actions):
                model_name = m.name.replace('models/', '')
                print(f"✅ تم العثور على: {model_name}")
                return model_name
    except:
        pass
    
    return "gemini-2.0-flash"

print("\nبدء تحميل الموديل...")
model_name = get_working_model()
print(f"\n🎯 الموديل المستخدم: {model_name}")

# ========== إدارة الجلسات ==========
chat_sessions = {}
chat_histories = {}
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

def get_or_create_chat(session_id):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = client.chats.create(model=model_name)
        # إرسال system prompt كأول رسالة
        chat_sessions[session_id].send_message(SYSTEM_PROMPT)
        chat_histories[session_id] = []
    return chat_sessions[session_id]

# ========== ENDPOINTS ==========

@app.route('/')
def home():
    return serve_html()

@app.route('/test')
def test():
    return jsonify({
        "status": "success",
        "message": "✅ السيرفر شغال",
        "model": model_name,
        "time": datetime.now().isoformat(),
        "host": request.host,
        "swagger": "/swagger"
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

# ========== MAIN CHAT (نفس البرومبت بتاعك) ==========
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({"reply": "الرجاء كتابة رسالة", "status": "error"})
        
        # نفس الـ system prompt بتاعك
        full_message = f"{SYSTEM_PROMPT}\n\nالمستخدم: {user_message}\n\nالرد:"
        
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

# ========== MOBILE ENDPOINTS (لربط التطبيق) ==========

@app.route('/mobile/status', methods=['GET'])
def mobile_status():
    """فحص الاتصال - يستخدمه التطبيق أول ما يفتح"""
    return jsonify({
        "success": True,
        "status": "online",
        "version": "2.0.0",
        "model": model_name,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/mobile/session/create', methods=['POST', 'GET'])
def mobile_create_session():
    """إنشاء جلسة جديدة - يستخدمه التطبيق عند بدء محادثة جديدة"""
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        
        session_id = str(uuid.uuid4())
        
        # إنشاء جلسة جديدة في نظامك
        chat_sessions[session_id] = client.chats.create(model=model_name)
        chat_sessions[session_id].send_message(SYSTEM_PROMPT)
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
    """إرسال رسالة من التطبيق"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({"success": False, "reply": "الرجاء كتابة رسالة"})
        
        # إنشاء جلسة جديدة إذا لم تكن موجودة
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = client.chats.create(model=model_name)
            chat_sessions[session_id].send_message(SYSTEM_PROMPT)
            chat_histories[session_id] = []
        
        # إرسال الرسالة
        full_message = f"{SYSTEM_PROMPT}\n\nالمستخدم: {user_message}\n\nالرد:"
        response = client.models.generate_content(
            model=model_name,
            contents=full_message
        )
        bot_reply = response.text
        
        # حفظ في التاريخ
        message_id = str(uuid.uuid4())
        chat_histories[session_id].append({
            "id": message_id,
            "user": user_message,
            "bot": bot_reply,
            "timestamp": datetime.now().isoformat()
        })
        
        save_conversation(session_id, user_message, bot_reply)
        
        return jsonify({
            "success": True,
            "reply": bot_reply,
            "session_id": session_id,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        error_message = str(e)
        print(f"خطأ: {error_message}")
        return jsonify({"success": False, "reply": f"خطأ: {error_message[:100]}"}), 500

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
        return jsonify({"success": False, "error": str(e)}), 500

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
        return jsonify({"success": False, "error": str(e)}), 500

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
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head><title>Family History Helper</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🌿 Family History Helper</h1>
            <p>الـ API شغال!</p>
            <p>📖 <a href="/swagger">Swagger UI</a> للتوثيق</p>
            <p>📱 <a href="/mobile/status">حالة السيرفر</a></p>
        </body>
        </html>
        """

@app.route('/api_info')
def api_info():
    return jsonify({
        "name": "Family History Chatbot API",
        "version": "2.0",
        "model": model_name,
        "hosted_on": "Vercel/Render",
        "swagger": "/swagger",
        "endpoints": {
            "/": "الواجهة الرئيسية",
            "/swagger": "توثيق Swagger UI (مهم!)",
            "/test": "اختبار الاتصال",
            "/models": "قائمة الموديلات",
            "/chat": "محادثة (POST)",
            "/mobile/status": "حالة السيرفر للموبايل",
            "/mobile/session/create": "إنشاء جلسة (POST)",
            "/mobile/chat/send": "إرسال رسالة (POST)",
            "/mobile/chat/history/<id>": "تاريخ المحادثة (GET)",
            "/logs": "سجل المحادثات",
            "/api_info": "معلومات API"
        }
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 تشغيل Family History Chatbot".center(70))
    print("="*70)
    print(f"\n✅ الموديل: {model_name}")
    print(f"✅ Swagger UI: http://localhost:{PORT}/swagger")
    print(f"✅ المنفذ: {PORT}")
    print("\n📱 Mobile Endpoints:")
    print("   GET    /mobile/status")
    print("   POST   /mobile/session/create")
    print("   POST   /mobile/chat/send")
    print("   GET    /mobile/chat/history/<id>")
    print("   DELETE /mobile/session/<id>")
    print("\n" + "="*70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
