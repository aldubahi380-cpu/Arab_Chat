#!/bin/bash

echo "Building Arab Chat APK..."
echo ""

# تحديث API URL إذا لزم الأمر
echo "Checking API URL in build.gradle..."
echo ""

# بناء APK Release
echo "Building Release APK..."
./gradlew assembleRelease

if [ $? -eq 0 ]; then
    echo ""
    echo "APK built successfully!"
    echo ""
    
    # نسخ APK إلى مجلد apk
    echo "Copying APK to apk folder..."
    if [ -f app/build/outputs/apk/release/*.apk ]; then
        cp app/build/outputs/apk/release/*.apk apk/
        echo ""
        echo "APK copied to apk folder!"
        echo ""
        echo "APK Location: apk/"
        ls -lh apk/*.apk
    else
        echo "APK file not found in app/build/outputs/apk/release/"
    fi
else
    echo ""
    echo "Build failed! Check errors above."
    exit 1
fi

echo ""
echo "Done!"

