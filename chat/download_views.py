"""
Views لتحميل APK
"""
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from pathlib import Path
from django.conf import settings


@require_http_methods(["GET"])
def download_apk_page(request):
    """صفحة تحميل APK"""
    return HttpResponse("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="تحميل تطبيق Arab Chat للأندرويد">
    <title>تحميل Arab Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .logo {
            width: 120px;
            height: 120px;
            background: #075E54;
            border-radius: 25px;
            margin: 0 auto 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            color: white;
            font-weight: bold;
        }
        
        h1 {
            color: #075E54;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #667781;
            margin-bottom: 40px;
            font-size: 16px;
        }
        
        .download-btn {
            background: #25D366;
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 30px;
            cursor: pointer;
            width: 100%;
            margin-bottom: 20px;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .download-btn:hover {
            background: #20BA5A;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
        }
        
        .download-btn:active {
            transform: translateY(0);
        }
        
        .info {
            background: #F0F2F5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
            text-align: right;
        }
        
        .info h3 {
            color: #075E54;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .info ul {
            list-style: none;
            color: #667781;
            line-height: 2;
        }
        
        .info li:before {
            content: "✓ ";
            color: #25D366;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .warning {
            background: #FFF3CD;
            border-right: 4px solid #FFC107;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            color: #856404;
            font-size: 14px;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 30px 20px;
            }
            
            h1 {
                font-size: 24px;
            }
            
            .logo {
                width: 100px;
                height: 100px;
                font-size: 40px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">AC</div>
        <h1>Arab Chat</h1>
        <p class="subtitle">تطبيق دردشة فورية آمن</p>
        
        <a href="/download/apk/" class="download-btn" download>
            📥 تحميل التطبيق (APK)
        </a>
        
        <div class="info">
            <h3>تعليمات التثبيت:</h3>
            <ul>
                <li>بعد التحميل، افتح ملف APK</li>
                <li>اسمح بالتثبيت من مصادر غير معروفة</li>
                <li>اتبع التعليمات على الشاشة</li>
                <li>استمتع بالتطبيق!</li>
            </ul>
        </div>
        
        <div class="warning">
            ⚠️ تأكد من تفعيل "التثبيت من مصادر غير معروفة" في إعدادات الأمان
        </div>
    </div>
</body>
</html>
    """, content_type="text/html; charset=utf-8")


@require_http_methods(["GET"])
def download_apk_file(request):
    """تحميل ملف APK"""
    # البحث عن APK في مجلد apk/
    apk_dir = Path(settings.BASE_DIR) / "apk"
    
    if not apk_dir.exists():
        return HttpResponse("APK file not found", status=404)
    
    # البحث عن أحدث APK
    apk_files = list(apk_dir.glob("*.apk"))
    
    if not apk_files:
        return HttpResponse("No APK files found", status=404)
    
    # الحصول على أحدث ملف
    latest_apk = max(apk_files, key=lambda p: p.stat().st_mtime)
    
    # إرجاع الملف للتحميل
    response = FileResponse(
        open(latest_apk, 'rb'),
        content_type='application/vnd.android.package-archive'
    )
    response['Content-Disposition'] = f'attachment; filename="{latest_apk.name}"'
    response['Content-Length'] = latest_apk.stat().st_size
    
    return response

