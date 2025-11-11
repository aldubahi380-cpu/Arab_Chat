// تربط هذا الملف بجذر النطاق حتى يحصل Service Worker على نطاق كامل (scope="/")
// يقوم بتحميل الكود الحقيقي من داخل مجلد static/pwa/sw.js
const versionTag = 'v3';
try {
  importScripts(`/static/pwa/sw.js?v=${versionTag}`);
} catch (error) {
  console.error('[SW] Failed to import main service worker script', error);
}

