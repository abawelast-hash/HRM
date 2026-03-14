@echo off
chcp 65001 >nul
cls

echo ════════════════════════════════════════════════════════════
echo   🏛️ ShamIn - نظام التنبؤ الذكي بسعر الصرف
echo ════════════════════════════════════════════════════════════
echo.
echo اختر ما تريد تشغيله:
echo.
echo   [1] 📊 لوحة التحكم (Dashboard) - مراقبة مباشرة
echo   [2] 🚀 API Server - للتحكم البرمجي
echo   [3] 🔄 تشغيل جمع RSS مباشرة
echo   [4] 💰 تشغيل جمع الأسعار مباشرة
echo   [5] 🎯 تشغيل جميع المحركات معاً
echo   [0] ❌ خروج
echo.
echo ════════════════════════════════════════════════════════════
echo.

set /p choice="اختيارك: "

if "%choice%"=="1" goto dashboard
if "%choice%"=="2" goto api
if "%choice%"=="3" goto rss
if "%choice%"=="4" goto prices
if "%choice%"=="5" goto all
if "%choice%"=="0" goto end

echo خيار غير صحيح!
pause
goto end

:dashboard
cls
echo 📊 تشغيل لوحة التحكم...
echo.
echo سيفتح في المتصفح على: http://localhost:8501
echo.
cd ShamIn
python run_dashboard.py
goto end

:api
cls
echo 🚀 تشغيل API Server...
echo.
echo سيعمل على: http://localhost:8000
echo التوثيق: http://localhost:8000/docs
echo.
cd ShamIn
python run_api.py
goto end

:rss
cls
echo 📰 تشغيل جمع RSS...
echo.
cd ShamIn
python -c "from src.ingestion.scheduler import collect_rss; import json; print(json.dumps(collect_rss(), indent=2, ensure_ascii=False))"
echo.
echo ════════════════════════════════════════════════════════════
echo ✅ اكتمل الجمع!
echo ════════════════════════════════════════════════════════════
pause
goto end

:prices
cls
echo 💰 تشغيل جمع الأسعار...
echo.
cd ShamIn
python -c "from src.ingestion.scheduler import collect_web_prices; import json; print(json.dumps(collect_web_prices(), indent=2, ensure_ascii=False))"
echo.
echo ════════════════════════════════════════════════════════════
echo ✅ اكتمل الجمع!
echo ════════════════════════════════════════════════════════════
pause
goto end

:all
cls
echo 🎯 تشغيل جميع المحركات...
echo.
cd ShamIn
python -c "from src.ingestion.scheduler import collect_rss, collect_web_prices; print('RSS:'); import json; print(json.dumps(collect_rss(), indent=2, ensure_ascii=False)); print('\nWeb Prices:'); print(json.dumps(collect_web_prices(), indent=2, ensure_ascii=False))"
echo.
echo ════════════════════════════════════════════════════════════
echo ✅ اكتمل تشغيل جميع المحركات!
echo ════════════════════════════════════════════════════════════
pause
goto end

:end
cls
echo.
echo 👋 شكراً لاستخدام ShamIn!
echo.
timeout /t 2 >nul
