<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: Array,
})

// Group consecutive entries that share the same term_label.
const groups = computed(() => {
  const out = []
  for (const entry of props.history || []) {
    const label = entry.term_label || 'Unknown'
    const last = out[out.length - 1]
    if (last && last.label === label) {
      last.entries.push(entry)
    } else {
      out.push({ label, entries: [entry] })
    }
  }
  return out
})

function entryKey(entry, i) {
  return `${i}-${entry.step_id || 'choice'}`
}

function dataEntries(data) {
  if (!data) return []
  return Object.entries(data)
}

function formatValue(v) {
  if (Array.isArray(v)) return v.join(', ')
  if (v !== null && typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
</script>

<template>
  <div v-if="groups.length" class="history-log">
    <section v-for="(group, gi) in groups" :key="`${gi}-${group.label}`" class="history-group">
      <h3 class="group-label">{{ group.label }}</h3>
      <div class="group-entries">
        <details
          v-for="(entry, i) in group.entries"
          :key="entryKey(entry, i)"
          class="history-entry"
        >
          <summary>
            <span class="entry-kind" :class="entry.step_type">{{ entry.step_type }}</span>
            <span class="entry-desc">{{ entry.description }}</span>
          </summary>
          <dl v-if="dataEntries(entry.data).length" class="entry-data">
            <template v-for="[k, v] in dataEntries(entry.data)" :key="k">
              <dt>{{ k }}</dt>
              <dd>{{ formatValue(v) }}</dd>
            </template>
          </dl>
        </details>
      </div>
    </section>
  </div>
  <p v-else class="history-empty">No steps completed yet.</p>
</template>

<style scoped>
.history-log {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.history-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.group-label {
  margin: 0 0 0.15rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #c4a35a;
  border-bottom: 1px solid #3a3a5e;
  padding-bottom: 0.2rem;
}
.group-entries {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.history-entry {
  background: #2a2a3e;
  border: 1px solid #3a3a5e;
  border-radius: 3px;
  padding: 0.35rem 0.55rem;
  font-size: 0.85rem;
}
.history-entry summary {
  cursor: pointer;
  list-style: none;
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
}
.history-entry summary::-webkit-details-marker { display: none; }
.history-entry summary::before {
  content: '▸';
  color: #c4a35a;
  font-size: 0.7rem;
  transition: transform 0.15s;
  display: inline-block;
}
.history-entry[open] summary::before { transform: rotate(90deg); }
.entry-kind {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.1rem 0.35rem;
  border-radius: 2px;
  background: #3a3a5e;
  color: #c4a35a;
  flex-shrink: 0;
}
.entry-kind.choice { background: #c4a35a; color: #1a1a2e; }
.entry-desc { flex: 1; }
.entry-data {
  margin-top: 0.4rem;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.15rem 0.75rem;
  font-size: 0.8rem;
  padding-left: 1rem;
}
.entry-data dt {
  color: #c4a35a;
  font-weight: 600;
}
.entry-data dd {
  color: #e0e0e0;
  font-family: monospace;
  word-break: break-word;
}
.history-empty {
  color: #808090;
  font-style: italic;
  font-size: 0.9rem;
}
</style>
