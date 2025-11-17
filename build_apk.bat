@echo off
echo Building Arab Chat APK...
echo.

REM تحديث API URL إذا لزم الأمر
echo Checking API URL in build.gradle...
echo.

REM بناء APK Release
echo Building Release APK...
call gradlew.bat assembleRelease

if %ERRORLEVEL% EQU 0 (
    echo.
    echo APK built successfully!
    echo.
    
    REM نسخ APK إلى مجلد apk
    echo Copying APK to apk folder...
    if exist "app\build\outputs\apk\release\*.apk" (
        copy /Y "app\build\outputs\apk\release\*.apk" "apk\"
        echo.
        echo APK copied to apk folder!
        echo.
        echo APK Location: apk\
        dir /B apk\*.apk
    ) else (
        echo APK file not found in app\build\outputs\apk\release\
    )
) else (
    echo.
    echo Build failed! Check errors above.
    exit /B 1
)

echo.
echo Done!
pause

