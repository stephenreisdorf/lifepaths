<script setup>
import { computed, ref } from 'vue'
import StatsTable from './StatsTable.vue'
import StepHistoryLog from './StepHistoryLog.vue'

const props = defineProps({
  characterData: Object,
  history: Array,
  error: String,
  busy: Boolean,
})

const emit = defineEmits(['restart'])
const confirmingRestart = ref(false)

const skillEntries = computed(() => {
  return Object.entries(props.characterData?.skills || {}).map(([name, info]) => ({
    name,
    baseRank: info.base_rank,
    specialties: Object.entries(info.specialties || {}).map(([specialty, rank]) => ({
      name: specialty,
      rank,
    })),
  }))
})

const cashDisplay = computed(() => {
  const value = Number(props.characterData?.cash || 0)
  const amount = Math.abs(value).toLocaleString()
  return value < 0 ? `-Cr${amount}` : `Cr${amount}`
})

const associateTypeLabels = {
  contact: 'Contacts',
  ally: 'Allies',
  rival: 'Rivals',
  enemy: 'Enemies',
}

const associateGroups = computed(() => {
  const associates = props.characterData?.associates || []
  return Object.entries(associateTypeLabels)
    .map(([type, label]) => ({
      type,
      label,
      entries: associates.filter((associate) => associate.type === type),
    }))
    .filter((group) => group.entries.length)
})

function printSheet() {
  window.print()
}

function confirmRestart() {
  emit('restart')
}
</script>

<template>
  <div class="sheet-layout">
    <div class="sheet-actions" aria-label="Character sheet actions">
      <button class="print-btn" @click="printSheet">Print Character</button>
      <button
        v-if="!confirmingRestart"
        class="secondary-btn"
        :disabled="busy"
        @click="confirmingRestart = true"
      >
        Start Over
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <section class="character-sheet" aria-labelledby="character-sheet-title">
      <header class="sheet-header">
        <div>
          <p class="sheet-kicker">Completed Traveller</p>
          <h1 id="character-sheet-title">Character Dossier</h1>
        </div>
        <div class="age-block">
          <span>Age</span>
          <strong>{{ characterData?.age ?? '—' }}</strong>
        </div>
      </header>

      <div class="sheet-grid sheet-grid-top">
        <section class="sheet-panel characteristics-panel">
          <h2>Characteristics</h2>
          <StatsTable
            v-if="characterData?.characteristics && Object.keys(characterData.characteristics).length"
            :characteristics="characterData.characteristics"
          />
          <p v-else class="empty">No characteristics recorded.</p>
        </section>

        <section class="sheet-panel resources-panel">
          <h2>Resources</h2>
          <dl class="cash-total">
            <dt>Available cash</dt>
            <dd>{{ cashDisplay }}</dd>
          </dl>
          <h3>Possessions</h3>
          <ul v-if="characterData?.possessions?.length" class="possession-list">
            <li v-for="item in characterData.possessions" :key="item">{{ item }}</li>
          </ul>
          <p v-else class="empty">No possessions recorded.</p>
        </section>
      </div>

      <section class="sheet-panel skills-panel">
        <h2>Skills</h2>
        <ul v-if="skillEntries.length" class="skill-list">
          <li v-for="skill in skillEntries" :key="skill.name" class="skill-card">
            <div class="skill-heading">
              <strong>{{ skill.name }}</strong>
              <span class="rank" :aria-label="`Rank ${skill.baseRank}`">{{ skill.baseRank }}</span>
            </div>
            <ul v-if="skill.specialties.length" class="specialty-list">
              <li v-for="specialty in skill.specialties" :key="specialty.name">
                <span>{{ specialty.name }}</span>
                <span class="rank" :aria-label="`Rank ${specialty.rank}`">{{ specialty.rank }}</span>
              </li>
            </ul>
          </li>
        </ul>
        <p v-else class="empty">No skills recorded.</p>
      </section>

      <section class="sheet-panel associates-panel">
        <h2>Associates</h2>
        <div v-if="associateGroups.length" class="associate-grid">
          <section v-for="group in associateGroups" :key="group.type" class="associate-group">
            <h3>{{ group.label }}</h3>
            <ul>
              <li
                v-for="associate in group.entries"
                :key="`${group.type}-${associate.name}-${associate.source_event || ''}`"
              >
                <strong>{{ associate.name }}</strong>
                <p v-if="associate.description">{{ associate.description }}</p>
                <small v-if="associate.source_event">{{ associate.source_event }}</small>
              </li>
            </ul>
          </section>
        </div>
        <p v-else class="empty">No associates recorded.</p>
      </section>

      <details class="sheet-panel history-panel">
        <summary>Complete Lifepath Record</summary>
        <StepHistoryLog :history="history" />
      </details>
    </section>

    <div v-if="confirmingRestart" class="restart-confirmation" role="alert">
      <p>Start over and discard this completed character?</p>
      <div class="restart-actions">
        <button class="secondary-btn" :disabled="busy" @click="confirmingRestart = false">
          Keep Character
        </button>
        <button :disabled="busy" @click="confirmRestart">
          {{ busy ? 'Starting…' : 'Discard & Start Over' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sheet-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.sheet-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
.print-btn::before {
  content: '▣';
  margin-right: 0.45rem;
}
.secondary-btn {
  background: var(--color-graphite-soft);
}
.secondary-btn:hover {
  background: var(--color-graphite);
}
.character-sheet {
  overflow: hidden;
  border: 1px solid var(--color-orange);
  background: var(--color-tan);
  color: var(--color-graphite);
  box-shadow: 0 1.1rem 2.5rem rgba(0, 0, 0, 0.3);
}
.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  padding: 2rem 2.25rem;
  border-bottom: 4px solid var(--color-imperial-red);
  background: var(--color-space-black);
}
.sheet-header h1 {
  margin: 0;
  color: var(--color-parchment);
  font-size: clamp(1.8rem, 4vw, 3rem);
}
.sheet-kicker {
  margin-bottom: 0.25rem;
  color: var(--color-orange);
  font-family: var(--font-condensed);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
.age-block {
  min-width: 6rem;
  padding-left: 1.5rem;
  border-left: 1px solid var(--color-orange-dim);
  text-align: center;
}
.age-block span {
  display: block;
  color: var(--color-orange);
  font-family: var(--font-condensed);
  font-size: 0.75rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.age-block strong {
  color: var(--color-parchment);
  font-family: var(--font-mono);
  font-size: 2rem;
}
.sheet-grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(16rem, 2fr);
}
.sheet-panel {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--color-orange-dim);
}
.sheet-panel h2,
.history-panel summary {
  margin-bottom: 1rem;
  color: var(--color-imperial-red);
  font-family: var(--font-condensed);
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.sheet-panel h2::after {
  content: '';
  display: block;
  width: 2.5rem;
  margin-top: 0.35rem;
  border-bottom: 2px solid var(--color-orange);
}
.characteristics-panel {
  border-right: 1px solid var(--color-orange-dim);
}
.characteristics-panel :deep(table) {
  margin: 0;
}
.resources-panel h3,
.associate-group h3 {
  margin: 1rem 0 0.5rem;
  color: var(--color-graphite-soft);
  font-size: 0.8rem;
}
.cash-total {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.75rem;
  border-left: 3px solid var(--color-imperial-red);
  background: var(--color-parchment);
}
.cash-total dt {
  color: var(--color-graphite-soft);
  font-size: 0.85rem;
}
.cash-total dd {
  color: var(--color-imperial-red);
  font-family: var(--font-mono);
  font-size: 1.1rem;
  font-weight: 700;
}
.possession-list,
.skill-list,
.specialty-list,
.associate-group ul {
  list-style: none;
}
.possession-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.possession-list li {
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--color-orange-dim);
  background: var(--color-parchment);
  font-size: 0.85rem;
}
.skill-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr));
  gap: 0.75rem;
}
.skill-card {
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--color-orange-dim);
  background: var(--color-parchment);
}
.skill-heading,
.specialty-list li {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.75rem;
}
.skill-heading strong {
  font-size: 0.9rem;
}
.rank {
  color: var(--color-imperial-red);
  font-family: var(--font-mono);
  font-weight: 700;
}
.specialty-list {
  margin-top: 0.45rem;
  padding-top: 0.4rem;
  border-top: 1px solid var(--color-orange-dim);
}
.specialty-list li {
  color: var(--color-graphite-soft);
  font-size: 0.78rem;
}
.associate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
}
.associate-group h3 {
  margin-top: 0;
}
.associate-group ul {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.associate-group li {
  padding: 0.65rem 0.75rem;
  border-left: 3px solid var(--color-orange);
  background: var(--color-parchment);
}
.associate-group p {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
}
.associate-group small {
  display: block;
  margin-top: 0.35rem;
  color: var(--color-graphite-soft);
  font-size: 0.72rem;
}
.history-panel {
  border-bottom: 0;
}
.history-panel summary {
  margin-bottom: 0;
  cursor: pointer;
}
.history-panel[open] summary {
  margin-bottom: 1rem;
}
.empty {
  margin: 0;
  color: var(--color-graphite-soft);
  font-style: italic;
}
.restart-confirmation {
  align-self: flex-end;
  padding: 1rem;
  border: 1px solid var(--color-orange);
  background: var(--color-tan);
  color: var(--color-graphite);
}
.restart-confirmation p {
  margin-bottom: 0.75rem;
  font-weight: 600;
}
.restart-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

@media (max-width: 720px) {
  .sheet-actions {
    justify-content: stretch;
  }
  .sheet-actions button {
    flex: 1;
  }
  .sheet-header,
  .sheet-panel {
    padding: 1.25rem;
  }
  .sheet-grid {
    grid-template-columns: 1fr;
  }
  .characteristics-panel {
    border-right: 0;
  }
}

@media print {
  :global(body) {
    background: white;
  }
  :global(.container) {
    max-width: none;
    padding: 0;
  }
  :global(.app-header),
  .sheet-actions,
  .restart-confirmation,
  .error {
    display: none;
  }
  .character-sheet {
    border: 1px solid #777;
    box-shadow: none;
  }
  .sheet-header {
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
  .sheet-panel {
    break-inside: avoid;
  }
}
</style>
