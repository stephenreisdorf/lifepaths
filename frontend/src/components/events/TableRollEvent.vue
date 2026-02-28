<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  event: Object,
  loading: Boolean,
})

const emit = defineEmits(['roll'])

const rollValue = ref('')

const diceRange = computed(() => {
  if (!props.event?.dice_expression) return { min: 1, max: 6 }
  const [n, m] = props.event.dice_expression.split('d').map(Number)
  return { min: n, max: n * m }
})

const isValid = computed(() => {
  const v = Number(rollValue.value)
  return Number.isInteger(v) && v >= diceRange.value.min && v <= diceRange.value.max
})

function submit() {
  if (!isValid.value || props.loading) return
  emit('roll', { eventId: props.event.id, rollResult: Number(rollValue.value) })
  rollValue.value = ''
}
</script>

<template>
  <div class="event-panel" v-if="event">
    <h3>{{ event.name }}</h3>
    <p>{{ event.description }}</p>

    <div class="dice-area">
      <div class="dice-label">Roll <strong>{{ event.dice_expression }}</strong></div>
      <div class="dice-hint">Enter a value from {{ diceRange.min }} to {{ diceRange.max }}</div>
      <div class="dice-input-row">
        <input
          type="number"
          v-model="rollValue"
          :min="diceRange.min"
          :max="diceRange.max"
          placeholder="Result"
          @keyup.enter="submit"
        />
        <button class="primary" @click="submit" :disabled="!isValid || loading">
          {{ loading ? 'Resolving...' : 'Resolve' }}
        </button>
      </div>
    </div>

    <div class="outcomes-preview">
      <div class="outcomes-label">Possible outcomes</div>
      <div class="outcome-row" v-for="o in event.outcomes" :key="o.id">
        <span class="outcome-range">{{ o.roll_min }}–{{ o.roll_max }}</span>
        <span class="outcome-label">{{ o.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

h3 {
  font-size: 1.15rem;
  margin-bottom: 0.35rem;
}

p {
  color: var(--color-text-muted);
  margin-bottom: 1.25rem;
}

.dice-area {
  margin-bottom: 1.5rem;
}

.dice-label {
  font-size: 1rem;
  margin-bottom: 0.2rem;
}

.dice-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: 0.6rem;
}

.dice-input-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.dice-input-row input {
  width: 100px;
  flex-shrink: 0;
}

.outcomes-preview {
  border-top: 1px solid var(--color-border);
  padding-top: 1rem;
}

.outcomes-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.outcome-row {
  display: flex;
  gap: 0.75rem;
  font-size: 0.9rem;
  padding: 0.2rem 0;
}

.outcome-range {
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
  min-width: 3rem;
}
</style>
