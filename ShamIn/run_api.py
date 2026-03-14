"""
تشغيل API - ShamIn FastAPI Server

الاستخدام:
    python run_api.py

أو:
    uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
"""

import subprocess
import sys
import os

def main():
    print("🚀 تشغيل ShamIn API Server...")
    print("=" * 60)
    print()
    
    # التأكد من وجود ملف API
    api_path = "src/presentation/api/main.py"
    
    if not os.path.exists(api_path):
        print(f"❌ خطأ: لم يتم العثور على {api_path}")
        sys.exit(1)
    
    # تشغيل Uvicorn
    try:
        subprocess.run([
            "uvicorn",
            "src.presentation.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ], check=True)
    except FileNotFoundError:
        print("❌ Uvicorn غير مثبت!")
        print("قم بتثبيته باستخدام: pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف API Server")
        sys.exit(0)

if __name__ == "__main__":
    main()
