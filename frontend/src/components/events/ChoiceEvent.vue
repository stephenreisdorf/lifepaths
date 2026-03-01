<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  event: Object,
  loading: Boolean,
  resolvedContext: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['choose'])

const selected = ref([])

function isOutcomeAvailable(outcome) {
  for (const [key, allowed] of Object.entries(outcome.requires_context ?? {})) {
    if (!allowed.includes(props.resolvedContext[key])) return false
  }
  return true
}

const availableOutcomes = computed(() => (props.event?.outcomes ?? []).filter(isOutcomeAvailable))

const canSubmit = computed(() => {
  const count = selected.value.length
  const min = props.event?.min_choices ?? 1
  const max = props.event?.max_choices ?? 1
  return count >= min && count <= max && !props.loading
})

function toggleChoice(key) {
  if ((props.event?.max_choices ?? 1) === 1) {
    selected.value = [key]
    return
  }
  const idx = selected.value.indexOf(key)
  if (idx >= 0) {
    selected.value.splice(idx, 1)
  } else if (selected.value.length < props.event.max_choices) {
    selected.value.push(key)
  }
}

function submit() {
  if (!canSubmit.value) return
  emit('choose', { eventId: props.event.id, choiceKeys: [...selected.value] })
  selected.value = []
}
</script>

<template>
  <div class="event-panel" v-if="event">
    <h3>{{ event.name }}</h3>
    <p>{{ event.description }}</p>

    <div class="choice-prompt" v-if="event.choice_prompt">{{ event.choice_prompt }}</div>

    <div class="choices">
      <button
        v-for="o in availableOutcomes"
        :key="o.choice_key"
        class="choice-card"
        :class="{ selected: selected.includes(o.choice_key) }"
        @click="toggleChoice(o.choice_key)"
        :disabled="loading"
      >
        <div class="choice-label">{{ o.label }}</div>
        <div class="choice-desc">{{ o.description }}</div>
        <div class="choice-mods" v-if="o.attribute_modifiers.length > 0">
          <span v-for="mod in o.attribute_modifiers" :key="mod.attribute" class="mod-chip">
            {{ mod.attribute.replace(/_/g, ' ') }} {{ mod.delta > 0 ? '+' : '' }}{{ mod.delta }}
          </span>
        </div>
      </button>
    </div>

    <button class="primary confirm-btn" :disabled="!canSubmit" @click="submit">
      {{ loading ? 'Resolving...' : 'Confirm' }}
    </button>
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
  margin-bottom: 0.75rem;
}

.choice-prompt {
  font-weight: 500;
  margin-bottom: 1rem;
}

.choices {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.choice-card {
  text-align: left;
  background: var(--color-surface-raised);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  width: 100%;
}

.choice-card:hover:not(:disabled) {
  border-color: var(--color-accent);
}

.choice-card.selected {
  border-color: var(--color-accent);
  background: #fff8f5;
}

.choice-label {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.choice-desc {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.choice-mods {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.mod-chip {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  font-size: 0.8rem;
  text-transform: capitalize;
}

.confirm-btn {
  width: 100%;
}
</style>
