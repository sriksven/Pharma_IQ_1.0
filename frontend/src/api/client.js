const BASE = 'http://localhost:8000'

export async function sendMessage(sessionId, question) {
  const res = await fetch(`${BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, question }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function rateMessage(messageId, score) {
  const res = await fetch(`${BASE}/api/v1/messages/${messageId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score }),
  })
  if (!res.ok) throw new Error('Failed to submit feedback')
  return res.json()
}

export async function getSessions() {
  const res = await fetch(`${BASE}/api/v1/sessions`)
  if (!res.ok) throw new Error('Failed to fetch sessions')
  return res.json()
}

export async function getSession(sessionId) {
  const res = await fetch(`${BASE}/api/v1/sessions/${sessionId}`)
  if (!res.ok) throw new Error('Session not found')
  return res.json()
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE}/api/v1/sessions/${sessionId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Failed to delete session')
  return res.json()
}

export async function getTables() {
  const res = await fetch(`${BASE}/api/v1/tables`)
  if (!res.ok) throw new Error('Failed to fetch tables')
  return res.json()
}

export async function getMetricsSummary() {
  const res = await fetch(`${BASE}/api/v1/metrics/summary`)
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

export async function getMetricsQueries(limit = 20) {
  const res = await fetch(`${BASE}/api/v1/metrics/queries?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch query metrics')
  return res.json()
}

export async function getLiveKitToken(sessionId = null) {
  const res = await fetch(`${BASE}/api/v1/voice/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to get voice token')
  }
  return res.json()
}

export async function getMetricsEvals(limit = 50) {
  const res = await fetch(`${BASE}/api/v1/metrics/evals?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch eval metrics')
  return res.json()
}
