<script setup>
import { ref } from 'vue'
import WelcomeScreen from './components/WelcomeScreen.vue'
import CreationScreen from './components/CreationScreen.vue'
import CharacterSheet from './components/CharacterSheet.vue'

const currentScreen = ref('welcome')
const characteristics = ref({})
const skillOptions = ref([])
const requiredSkillCount = ref(0)
const characterData = ref(null)
const error = ref('')
const sessionId = ref(null)

async function startCreation() {
  error.value = ''
  const res = await fetch('/api/start', { method: 'POST' })
  const data = await res.json()

  sessionId.value = data.session_id
  characteristics.value = data.character.characteristics
  skillOptions.value = data.next_prompt.options
  requiredSkillCount.value = data.next_prompt.required_count
  characterData.value = null
  currentScreen.value = 'creation'
}

async function confirmSkills(selections) {
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
  currentScreen.value = 'sheet'
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
      :characteristics="characteristics"
      :skill-options="skillOptions"
      :required-skill-count="requiredSkillCount"
      :error="error"
      @confirm="confirmSkills"
    />
    <CharacterSheet
      v-else-if="currentScreen === 'sheet'"
      :characteristics="characterData.characteristics"
      :skills="characterData.skills"
      @restart="startCreation"
    />
  </div>
</template>
