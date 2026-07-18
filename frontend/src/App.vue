<script setup>
import { ref } from 'vue'
import WelcomeScreen from './components/WelcomeScreen.vue'
import CreationScreen from './components/CreationScreen.vue'
import CharacterSheet from './components/CharacterSheet.vue'

const currentScreen = ref('welcome')
const sessionId = ref(null)
const characterData = ref(null)
const stepHistory = ref([])
const currentPrompt = ref(null)
const pendingReview = ref(null)
const error = ref('')
const busy = ref(false)

const networkErrorMessage = "Couldn't reach the server. Try again."
const invalidResponseMessage = 'The server returned an unreadable response. Try again.'

async function readJson(res) {
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return null
  try {
    return await res.json()
  } catch {
    return null
  }
}

function responseErrorMessage(res, data) {
  if (data?.detail) return data.detail
  if (data?.message) return data.message
  return `Server returned ${res.status}. Try again.`
}

async function requestJson(url, options) {
  let res
  try {
    res = await fetch(url, options)
  } catch {
    throw new Error(networkErrorMessage)
  }

  const data = await readJson(res)
  if (!res.ok) {
    throw new Error(responseErrorMessage(res, data))
  }
  if (!data) {
    throw new Error(invalidResponseMessage)
  }
  return data
}

async function startCreation(anagathicsEnabled = false) {
  if (busy.value) return

  busy.value = true
  error.value = ''
  try {
    const data = await requestJson('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ anagathics_enabled: anagathicsEnabled }),
    })

    sessionId.value = data.session_id
    characterData.value = data.character
    stepHistory.value = [...data.resolved_steps]
    currentPrompt.value = data.next_prompt
    pendingReview.value = null
    currentScreen.value = data.next_prompt ? 'creation' : 'sheet'
  } catch (err) {
    error.value = err.message || networkErrorMessage
  } finally {
    busy.value = false
  }
}

async function submitChoice(selections) {
  const choiceEntry = currentPrompt.value
    ? {
        step_id: currentPrompt.value.step_id,
        step_type: 'choice',
        description: currentPrompt.value.description,
        data: { selected: selections },
        term_label: currentPrompt.value.term_label,
      }
    : null
  await submit({ selections }, choiceEntry)
}

async function submitAutomatic() {
  await submit(null, null)
}

async function submit(playerInput, choiceEntry) {
  if (busy.value) return

  busy.value = true
  error.value = ''
  let data

  try {
    data = await requestJson('/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        player_input: playerInput,
      }),
    })
  } catch (err) {
    error.value = err.message || networkErrorMessage
    return
  } finally {
    busy.value = false
  }

  characterData.value = data.character
  if (choiceEntry) stepHistory.value.push(choiceEntry)
  stepHistory.value.push(...data.resolved_steps)
  currentPrompt.value = data.next_prompt
  pendingReview.value = data.resolved_steps.length
    ? data.resolved_steps[data.resolved_steps.length - 1]
    : null

  if (!data.next_prompt && !pendingReview.value) {
    currentScreen.value = 'sheet'
  }
}

function dismissReview() {
  pendingReview.value = null
  if (!currentPrompt.value) {
    currentScreen.value = 'sheet'
  }
}
</script>

<template>
  <div
    class="container"
    :class="{ wide: currentScreen !== 'welcome' }"
    :aria-busy="busy"
  >
    <header class="app-header">
      <span class="wordmark">LIFEPATHS</span>
      <svg class="orbit" viewBox="0 0 60 34" aria-hidden="true">
        <ellipse cx="30" cy="17" rx="28" ry="9" />
        <circle cx="30" cy="17" r="4" />
      </svg>
      <span class="sub-brand">Character Creation</span>
    </header>
    <WelcomeScreen
      v-if="currentScreen === 'welcome'"
      :error="error"
      :busy="busy"
      @start="startCreation"
    />
    <CreationScreen
      v-else-if="currentScreen === 'creation'"
      :character-data="characterData"
      :prompt="currentPrompt"
      :pending-review="pendingReview"
      :history="stepHistory"
      :error="error"
      :busy="busy"
      @confirm="submitChoice"
      @advance="submitAutomatic"
      @continue="dismissReview"
    />
    <CharacterSheet
      v-else-if="currentScreen === 'sheet'"
      :character-data="characterData"
      :history="stepHistory"
      :error="error"
      :busy="busy"
      @restart="startCreation"
    />
  </div>
</template>

<style>
.container.wide { max-width: 1200px; }

.app-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding-bottom: 1.25rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-orange-dim);
}
.wordmark {
  font-family: var(--font-condensed);
  font-weight: 700;
  font-size: 1.9rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-imperial-red);
  background: linear-gradient(180deg, #e23a54 0%, var(--color-imperial-red) 55%, var(--color-imperial-red-dark) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}
.orbit {
  width: 60px;
  height: 34px;
  flex-shrink: 0;
}
.orbit ellipse {
  fill: none;
  stroke: #c9c9d2;
  stroke-width: 1.5;
}
.orbit circle {
  fill: var(--color-orange);
}
.sub-brand {
  margin-left: auto;
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.8rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #c9c9d2;
}
@media (max-width: 560px) {
  .sub-brand { display: none; }
}
</style>
