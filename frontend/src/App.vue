<script setup>
import { ref, onMounted } from 'vue'
import * as api from './api/client.js'
import LandingScreen from './components/LandingScreen.vue'
import SessionScreen from './components/SessionScreen.vue'
import CompleteScreen from './components/CompleteScreen.vue'

const screen = ref('landing')
const lifepaths = ref([])
const sessionId = ref(null)
const sessionState = ref(null)
const lifepathConfig = ref(null)
const characterSheet = ref(null)
const characterName = ref(null)
const lastOutcome = ref(null)
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  try {
    lifepaths.value = await api.fetchLifepaths()
  } catch (err) {
    error.value = err.message
  }
})

async function handleStart({ configId, playerName, characterName: cname }) {
  loading.value = true
  error.value = null
  try {
    const [sessionResp, config] = await Promise.all([
      api.createSession(configId, playerName, cname),
      api.fetchLifepath(configId),
    ])
    sessionId.value = sessionResp.session_id
    sessionState.value = sessionResp.state
    lifepathConfig.value = config
    characterName.value = cname || null
    screen.value = 'session'
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function findEventDef(eventId) {
  if (!lifepathConfig.value || !sessionState.value) return null
  const stageId = sessionState.value.current_stage_id
  const stage = lifepathConfig.value.stages[stageId]
  if (!stage) return null
  return stage.events.find(e => e.id === eventId) ?? null
}

function handleResolutionResponse(resp, outcomeFromEvent) {
  sessionState.value = resp.state
  if (resp.character_sheet) {
    characterSheet.value = resp.character_sheet
  }
  lastOutcome.value = outcomeFromEvent ?? null
  // If session completed with no outcome to display, go directly to complete
  if (resp.character_sheet && !outcomeFromEvent) {
    screen.value = 'complete'
  }
}

async function handleRoll({ eventId, rollResult }) {
  const eventDef = findEventDef(eventId)
  loading.value = true
  error.value = null
  try {
    const resp = await api.rollEvent(sessionId.value, eventId, rollResult)
    const outcome =
      eventDef?.outcomes.find(
        o => o.roll_min <= rollResult && rollResult <= o.roll_max
      ) ?? null
    handleResolutionResponse(resp, outcome)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleChoose({ eventId, choiceKeys }) {
  const eventDef = findEventDef(eventId)
  loading.value = true
  error.value = null
  try {
    const resp = await api.chooseEvent(sessionId.value, eventId, choiceKeys)
    const outcome =
      choiceKeys.length === 1
        ? (eventDef?.outcomes.find(o => o.choice_key === choiceKeys[0]) ?? null)
        : null
    handleResolutionResponse(resp, outcome)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleSkip({ eventId }) {
  loading.value = true
  error.value = null
  try {
    const resp = await api.skipEvent(sessionId.value, eventId)
    handleResolutionResponse(resp, null)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleAdvance({ repeatStage }) {
  loading.value = true
  error.value = null
  try {
    const resp = await api.advanceSession(sessionId.value, repeatStage)
    handleResolutionResponse(resp, null)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function handleOutcomeDismissed() {
  lastOutcome.value = null
  if (characterSheet.value) {
    screen.value = 'complete'
  }
}
</script>

<template>
  <div class="error-message" v-if="error">{{ error }}</div>

  <LandingScreen
    v-if="screen === 'landing'"
    :lifepaths="lifepaths"
    :loading="loading"
    @start="handleStart"
  />

  <SessionScreen
    v-else-if="screen === 'session'"
    :session-state="sessionState"
    :lifepath-config="lifepathConfig"
    :last-outcome="lastOutcome"
    :loading="loading"
    :character-name="characterName"
    @roll="handleRoll"
    @choose="handleChoose"
    @skip="handleSkip"
    @advance="handleAdvance"
    @outcome-dismissed="handleOutcomeDismissed"
  />

  <CompleteScreen
    v-else-if="screen === 'complete'"
    :character-sheet="characterSheet"
    :lifepath-config="lifepathConfig"
  />
</template>
