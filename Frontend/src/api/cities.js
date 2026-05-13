import { apiUrl } from '@/config/api.js'

/**
 * جلب قائمة المحافظات من الباكند.
 * @returns {Promise<Array<{ id: number, name: string, name_ar: string, name_en: string, lon: number, lat: number }>>}
 */
export async function fetchCities() {
  const response = await fetch(apiUrl('/api/cities'))
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const msg =
      typeof err.detail === 'string'
        ? err.detail
        : 'تعذر تحميل قائمة المحافظات'
    throw new Error(msg)
  }
  const data = await response.json()
  if (!Array.isArray(data)) {
    throw new Error('استجابة غير صالحة من الخادم')
  }
  return data
}
