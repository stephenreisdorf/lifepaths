<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  lifepaths: Array,
  loading: Boolean,
})

const emit = defineEmits(['start'])

const selectedConfigId = ref('')
const playerName = ref('')
const characterName = ref('')

const canStart = computed(() => selectedConfigId.value !== '' && !props.loading)

function handleSubmit() {
  if (!canStart.value) return
  emit('start', {
    configId: selectedConfigId.value,
    playerName: playerName.value.trim() || null,
    characterName: characterName.value.trim() || null,
  })
}
</script>

<template>
  <div class="landing">
    <div class="landing-card">
      <h1>Lifepaths</h1>
      <p class="subtitle">A life-path character creation system.</p>

      <form @submit.prevent="handleSubmit" class="landing-form">
        <div class="field">
          <label for="lifepath-select">Life Path</label>
          <select id="lifepath-select" v-model="selectedConfigId">
            <option value="" disabled>Select a life path...</option>
            <option v-for="lp in lifepaths" :key="lp.id" :value="lp.id">
              {{ lp.name }}
            </option>
          </select>
        </div>

        <div class="field">
          <label for="character-name">Character Name</label>
          <input id="character-name" type="text" v-model="characterName" placeholder="Optional" />
        </div>

        <div class="field">
          <label for="player-name">Player Name</label>
          <input id="player-name" type="text" v-model="playerName" placeholder="Optional" />
        </div>

        <button type="submit" class="primary begin-btn" :disabled="!canStart">
          {{ loading ? 'Starting...' : 'Begin' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.landing-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 2.5rem;
  width: 100%;
  max-width: 440px;
}

h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
}

.subtitle {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

.landing-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
}

.begin-btn {
  margin-top: 0.5rem;
  width: 100%;
  padding: 0.65rem;
}
</style>
