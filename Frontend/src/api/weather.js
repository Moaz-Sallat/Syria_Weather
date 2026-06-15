import { apiUrl } from '@/config/api.js'

function parseApiError(data, fallbackMessage) {
  const detail = data?.detail

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || String(item)).join('، ')
  }

  if (typeof detail === 'string') {
    return detail
  }

  return fallbackMessage
}

export async function fetchWeeklyForecast(cityId) {
  const response = await fetch(apiUrl(`/api/forecast/${cityId}`))
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(parseApiError(data, 'تعذر تحميل توقعات الطقس'))
  }

  if (!Array.isArray(data.data)) {
    throw new Error('استجابة التوقعات غير صالحة من الخادم')
  }

  return data.data
}