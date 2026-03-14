"""
تشغيل لوحة التحكم - ShamIn Dashboard

الاستخدام:
    python run_dashboard.py

أو:
    streamlit run src/presentation/dashboard/app.py
"""

import subprocess
import sys
import os

def main():
    print("🏛️ تشغيل لوحة تحكم شامِن...")
    print("=" * 60)
    print()
    
    # التأكد من وجود ملف Dashboard
    dashboard_path = "src/presentation/dashboard/app.py"
    
    if not os.path.exists(dashboard_path):
        print(f"❌ خطأ: لم يتم العثور على {dashboard_path}")
        sys.exit(1)
    
    # تشغيل Streamlit
    try:
        subprocess.run([
            "streamlit", "run", dashboard_path,
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--theme.base", "dark",
            "--theme.primaryColor", "#3b82f6",
        ], check=True)
    except FileNotFoundError:
        print("❌ Streamlit غير مثبت!")
        print("قم بتثبيته باستخدام: pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 تم إيقاف لوحة التحكم")
        sys.exit(0)

if __name__ == "__main__":
    main()
