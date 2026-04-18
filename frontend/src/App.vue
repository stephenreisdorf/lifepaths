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

async function startCreation() {
  error.value = ''
  const res = await fetch('/api/start', { method: 'POST' })
  const data = await res.json()

  sessionId.value = data.session_id
  characterData.value = data.character
  stepHistory.value = [...data.resolved_steps]
  currentPrompt.value = data.next_prompt
  pendingReview.value = null
  currentScreen.value = data.next_prompt ? 'creation' : 'sheet'
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
  error.value = ''

  const res = await fetch('/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId.value,
      player_input: playerInput,
    }),
  })

  if (!res.ok) {
    const err = await res.json()
    error.value = err.detail
    return
  }

  const data = await res.json()
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
  <div class="container" :class="{ wide: currentScreen !== 'welcome' }">
    <WelcomeScreen
      v-if="currentScreen === 'welcome'"
      @start="startCreation"
    />
    <CreationScreen
      v-else-if="currentScreen === 'creation'"
      :character-data="characterData"
      :prompt="currentPrompt"
      :pending-review="pendingReview"
      :history="stepHistory"
      :error="error"
      @confirm="submitChoice"
      @advance="submitAutomatic"
      @continue="dismissReview"
    />
    <CharacterSheet
      v-else-if="currentScreen === 'sheet'"
      :character-data="characterData"
      :history="stepHistory"
      @restart="startCreation"
    />
  </div>
</template>

<style>
.container.wide { max-width: 1200px; }
</style>
