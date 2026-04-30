import google.generativeai as genai
import os

# استخدام المفتاح من متغيرات البيئة (لـ Render) أو المفتاح المباشر
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAFRc9rkX6vB-UtDDvl7xgL1SJF8kBaAdk")
genai.configure(api_key=API_KEY)

print("="*60)
print("🔍 اختبار موديلات Gemini")
print("="*60)

# قائمة الموديلات المحدثة (حسب المتاح حالياً)
models_to_test = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-flash-latest",
    "gemini-pro-latest"
]

working_model = None

print("\n🔄 جاري تجربة الموديلات...")
print("-"*40)

for model_name in models_to_test:
    print(f"\n🔄 تجربة: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("قل مرحبا بالعربية")
        print(f"✅ نجاح: {response.text.strip()}")
        working_model = model_name
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ الموديل غير موجود")
        elif "permission" in error_msg.lower():
            print(f"❌ ليس لديك صلاحية")
        else:
            print(f"❌ فشل: {error_msg[:80]}...")

print("\n" + "="*60)

if working_model:
    print(f"🎉 الموديل الشغال: {working_model}")
    print("✅ يمكنك استخدام هذا الموديل في تطبيقك")
else:
    print("❌ لا يوجد موديل شغال")
    print("💡 تأكد من صلاحية مفتاح API")

print("\n" + "="*60)
print("📋 جميع الموديلات المتاحة في حسابك:")
print("="*60)

try:
    available_count = 0
    for m in genai.list_models():
        if 'generateContent' in str(m.supported_generation_methods):
            available_count += 1
            print(f"\n✅ {m.name}")
            if hasattr(m, 'supported_generation_methods'):
                print(f"   📌 يدعم: {', '.join(m.supported_generation_methods)}")
            if hasattr(m, 'description'):
                desc = m.description[:80] + "..." if len(m.description) > 80 else m.description
                print(f"   📝 {desc}")
    
    print(f"\n📊 إجمالي الموديلات المتاحة للدردشة: {available_count}")
    
except Exception as e:
    print(f"❌ خطأ في جلب الموديلات: {e}")

print("\n" + "="*60)
print("✨ تم الانتهاء من الاختبار")
print("="*60)
