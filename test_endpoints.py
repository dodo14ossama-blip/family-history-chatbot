import requests
import json
import os

# استخدم الرابط من متغيرات البيئة أو اسأل المستخدم
BASE_URL = os.environ.get("API_URL")

if not BASE_URL:
    BASE_URL = input("🔗 أدخل رابط السيرفر (مثال: https://your-app.onrender.com): ").strip()
    if not BASE_URL:
        BASE_URL = "http://127.0.0.1:8000"
        print(f"⚠️ استخدام الرابط المحلي: {BASE_URL}")

def test_all_endpoints():
    print("=" * 50)
    print(f"🧪 اختبار الـ endpoints على: {BASE_URL}")
    print("=" * 50)
    
    # 1. اختبار الصفحة الرئيسية
    print("\n1️⃣ اختبار GET /")
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"   ✅ النجاح: {r.status_code}")
    except Exception as e:
        print(f"   ❌ الفشل: {e}")
    
    # 2. اختبار test endpoint
    print("\n2️⃣ اختبار GET /test")
    try:
        r = requests.get(f"{BASE_URL}/test")
        print(f"   ✅ النجاح: {r.status_code}")
        data = r.json()
        print(f"   📦 البيانات: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ الفشل: {e}")
    
    # 3. اختبار chat
    print("\n3️⃣ اختبار POST /chat")
    try:
        r = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "مرحباً، كيف حالك؟"}
        )
        print(f"   ✅ النجاح: {r.status_code}")
        data = r.json()
        print(f"   💬 الرد: {data.get('reply', '')[:100]}...")
    except Exception as e:
        print(f"   ❌ الفشل: {e}")
    
    # 4. اختبار api_info
    print("\n4️⃣ اختبار GET /api_info")
    try:
        r = requests.get(f"{BASE_URL}/api_info")
        print(f"   ✅ النجاح: {r.status_code}")
        data = r.json()
        print(f"   📊 المعلومات: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ الفشل: {e}")
    
    print("\n" + "=" * 50)
    print("✅ انتهى الاختبار")
    print("=" * 50)

if __name__ == "__main__":
    test_all_endpoints()