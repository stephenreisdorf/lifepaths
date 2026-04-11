<script setup>
import { ref } from 'vue'
import WelcomeScreen from './components/WelcomeScreen.vue'
import CreationScreen from './components/CreationScreen.vue'
import CharacterSheet from './components/CharacterSheet.vue'

const currentScreen = ref('welcome')
const sessionId = ref(null)
const characterData = ref(null)
const resolvedSteps = ref([])
const currentPrompt = ref(null)
const error = ref('')

async function startCreation() {
  error.value = ''
  const res = await fetch('/api/start', { method: 'POST' })
  const data = await res.json()

  sessionId.value = data.session_id
  characterData.value = data.character
  resolvedSteps.value = data.resolved_steps
  currentPrompt.value = data.next_prompt
  currentScreen.value = data.next_prompt ? 'creation' : 'sheet'
}

async function submitInput(selections) {
  error.value = ''
  const res = await fetch('/api/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId.value,
      player_input: { selections },
    }),
  })

  if (!res.ok) {
    const err = await res.json()
    error.value = err.detail
    return
  }

  const data = await res.json()
  characterData.value = data.character
  resolvedSteps.value = data.resolved_steps
  currentPrompt.value = data.next_prompt

  if (!data.next_prompt) {
    currentScreen.value = 'sheet'
  }
}
</script>

<template>
  <div class="container">
    <WelcomeScreen
      v-if="currentScreen === 'welcome'"
      @start="startCreation"
    />
    <CreationScreen
      v-else-if="currentScreen === 'creation'"
      :characteristics="characterData?.characteristics"
      :prompt="currentPrompt"
      :resolved-steps="resolvedSteps"
      :error="error"
      @confirm="submitInput"
    />
    <CharacterSheet
      v-else-if="currentScreen === 'sheet'"
      :characteristics="characterData.characteristics"
      :skills="characterData.skills"
      @restart="startCreation"
    />
  </div>
</template>
