<script setup>
import { computed } from 'vue'

const props = defineProps({
  features: Array,
})

const grouped = computed(() => {
  const groups = {}
  for (const f of props.features ?? []) {
    const cat = f.category ?? 'other'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(f)
  }
  return groups
})
</script>

<template>
  <div class="feature-list">
    <div v-if="!features || features.length === 0" class="empty">
      No features gained.
    </div>
    <div v-else v-for="(items, cat) in grouped" :key="cat" class="feature-group">
      <div class="group-label">{{ cat }}</div>
      <div v-for="f in items" :key="f.id" class="feature-item">
        <div class="feature-name">{{ f.name }}</div>
        <div class="feature-desc">{{ f.description }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.empty {
  color: var(--color-text-muted);
  font-style: italic;
}

.group-label {
  font-size: 0.75rem;
  text-transform: capitalize;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.feature-item {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}

.feature-name {
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.feature-desc {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
</style>
