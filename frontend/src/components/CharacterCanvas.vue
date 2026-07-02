<script setup>
import { ref, computed } from 'vue'
import StatsTable from './StatsTable.vue'
import StepHistoryLog from './StepHistoryLog.vue'

const props = defineProps({
  age: Number,
  characteristics: Object,
  skills: Object,
  history: Array,
})

const showJson = ref(false)

const skillEntries = computed(() => {
  if (!props.skills) return []
  return Object.entries(props.skills).map(([name, info]) => ({
    name,
    baseRank: info.base_rank,
    specialties: Object.entries(info.specialties || {}).map(([spName, rank]) => ({
      name: spName,
      rank,
    })),
  }))
})

const rawState = computed(() => ({
  characteristics: props.characteristics,
  skills: props.skills,
  history: props.history,
}))
</script>

<template>
  <aside class="canvas chamfer">
    <div class="canvas-inner">
    <div class="canvas-header">
      <h2>Character<span v-if="age" class="age-badge"> — Age {{ age }}</span></h2>
      <button class="json-toggle" @click="showJson = !showJson">
        {{ showJson ? 'Formatted' : 'Raw JSON' }}
      </button>
    </div>

    <pre v-if="showJson" class="json-dump">{{ JSON.stringify(rawState, null, 2) }}</pre>

    <template v-else>
      <section class="canvas-section">
        <h3>Characteristics</h3>
        <StatsTable v-if="characteristics" :characteristics="characteristics" />
        <p v-else class="empty">Not yet rolled.</p>
      </section>

      <section class="canvas-section">
        <h3>Skills</h3>
        <ul v-if="skillEntries.length" class="skill-list-canvas">
          <li v-for="skill in skillEntries" :key="skill.name">
            <div class="skill-row">
              <span class="skill-name">{{ skill.name }}</span>
              <span class="skill-rank">{{ skill.baseRank }}</span>
            </div>
            <ul v-if="skill.specialties.length" class="specialty-list">
              <li v-for="sp in skill.specialties" :key="sp.name">
                <span class="specialty-name">{{ sp.name }}</span>
                <span class="skill-rank">{{ sp.rank }}</span>
              </li>
            </ul>
          </li>
        </ul>
        <p v-else class="empty">No skills yet.</p>
      </section>

      <section class="canvas-section">
        <h3>Step History</h3>
        <StepHistoryLog :history="history" />
      </section>
    </template>
    </div>
  </aside>
</template>

<style scoped>
.canvas {
  padding: 18px;
}
.canvas-inner {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: calc(100vh - 8rem);
  overflow-y: auto;
}
.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.canvas-header h2 {
  margin: 0;
  font-size: 1.1rem;
}
.age-badge {
  color: var(--color-graphite-soft);
  font-weight: 400;
  font-size: 0.9rem;
}
.json-toggle {
  font-size: 0.7rem;
  padding: 0.3rem 0.7rem;
}
.canvas-section h3 {
  color: var(--color-orange);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-orange-dim);
  padding-bottom: 0.25rem;
}
.canvas-section :deep(table) { margin-bottom: 0; }
.canvas-section :deep(th),
.canvas-section :deep(td) { padding: 0.3rem 0.5rem; font-size: 0.85rem; }
.canvas-section :deep(.mono) { font-size: 0.95rem; }

.skill-list-canvas {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.skill-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  background: var(--color-parchment);
  border: 1px solid var(--color-orange-dim);
  padding: 0.3rem 0.6rem;
  font-size: 0.9rem;
}
.skill-name { color: var(--color-graphite); }
.skill-rank {
  font-family: var(--font-mono);
  color: var(--color-imperial-red);
  font-weight: 700;
}
.specialty-list {
  list-style: none;
  margin-top: 0.25rem;
  margin-left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.specialty-list li {
  display: flex;
  justify-content: space-between;
  background: var(--color-tan-shade);
  border-left: 2px solid var(--color-orange);
  padding: 0.2rem 0.5rem;
  font-size: 0.82rem;
}
.specialty-name { color: var(--color-graphite-soft); }

.json-dump {
  background: var(--color-space-black);
  border: 1px solid var(--color-orange-dim);
  padding: 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--color-tan);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.empty {
  color: var(--color-graphite-soft);
  font-style: italic;
  font-size: 0.85rem;
  margin: 0;
}
</style>
