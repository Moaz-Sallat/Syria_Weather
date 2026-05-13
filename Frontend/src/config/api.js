/**
 * عنوان الباكند للطلبات من المتصفح.
 * - في التطوير: اترك VITE_API_BASE_URL فارغاً لاستخدام المسارات النسبية مع بروكسي Vite.
 * - في الإنتاج: عرّف VITE_API_BASE_URL إن كان الفرونت والباكند على نطاقين مختلفين.
 */
export function getApiBaseUrl() {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') {
    return ''
  }
  return String(raw).trim().replace(/\/$/, '')
}

export function apiUrl(path) {
  const base = getApiBaseUrl()
  const p = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${p}` : p
}
