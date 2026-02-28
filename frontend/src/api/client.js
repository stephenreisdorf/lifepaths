const BASE = 'http://localhost:8000'

async function handleResponse(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {}
    throw new Error(detail)
  }
  return res.json()
}

export async function fetchLifepaths() {
  return handleResponse(await fetch(`${BASE}/api/content/lifepaths`))
}

export async function fetchLifepath(configId) {
  return handleResponse(await fetch(`${BASE}/api/content/lifepaths/${configId}`))
}

export async function createSession(configId, playerName, characterName) {
  return handleResponse(
    await fetch(`${BASE}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lifepath_config_id: configId,
        player_name: playerName || null,
        character_name: characterName || null,
      }),
    })
  )
}

export async function getSession(sessionId) {
  return handleResponse(await fetch(`${BASE}/api/sessions/${sessionId}`))
}

export async function rollEvent(sessionId, eventId, rollResult) {
  return handleResponse(
    await fetch(`${BASE}/api/sessions/${sessionId}/events/${eventId}/roll`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roll_result: rollResult }),
    })
  )
}

export async function chooseEvent(sessionId, eventId, choiceKeys) {
  return handleResponse(
    await fetch(`${BASE}/api/sessions/${sessionId}/events/${eventId}/choose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice_keys: choiceKeys }),
    })
  )
}

export async function skipEvent(sessionId, eventId) {
  return handleResponse(
    await fetch(`${BASE}/api/sessions/${sessionId}/events/${eventId}/skip`, {
      method: 'POST',
    })
  )
}

export async function advanceSession(sessionId, repeatStage) {
  return handleResponse(
    await fetch(`${BASE}/api/sessions/${sessionId}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repeat_stage: repeatStage }),
    })
  )
}
