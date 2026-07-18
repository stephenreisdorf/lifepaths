<script setup>
const props = defineProps({
  progress: Object,
})

const phases = [
  { id: 'childhood', label: 'Childhood' },
  { id: 'education', label: 'Education' },
  { id: 'career', label: 'Career' },
  { id: 'muster_out', label: 'Muster Out' },
]

function phaseState(index) {
  const current = props.progress?.phase_index || 1
  if (index + 1 === current) return 'current'
  return index + 1 < current ? 'past' : 'future'
}
</script>

<template>
  <nav class="lifepath-progress" aria-label="Lifepath progress">
    <ol>
      <li
        v-for="(phase, index) in phases"
        :key="phase.id"
        :class="phaseState(index)"
        :aria-current="phase.id === progress?.phase ? 'step' : undefined"
      >
        <span class="phase-marker" aria-hidden="true">{{ index + 1 }}</span>
        <span class="phase-label">{{ phase.label }}</span>
        <span
          v-if="phase.id === 'career' && progress?.career_term_number"
          class="term-count"
        >
          Term {{ progress.career_term_number }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.lifepath-progress {
  margin-bottom: 1.25rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-orange-dim);
  background: rgba(5, 5, 5, 0.72);
}
.lifepath-progress ol {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  list-style: none;
}
.lifepath-progress li {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  justify-items: center;
  align-items: center;
  gap: 0.4rem;
  color: #8f8f99;
  font-family: var(--font-condensed);
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.lifepath-progress li:not(:last-child)::after {
  content: '';
  position: absolute;
  left: calc(50% + 1rem);
  right: calc(-50% + 1rem);
  top: 0.78rem;
  height: 1px;
  background: var(--color-orange-dim);
}
.phase-marker {
  display: grid;
  place-items: center;
  width: 1.55rem;
  height: 1.55rem;
  border: 1px solid currentColor;
  border-radius: 50%;
  background: var(--color-space-black);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  z-index: 1;
}
.phase-label { text-align: center; }
.past { color: var(--color-orange) !important; }
.current { color: var(--color-parchment) !important; }
.current .phase-marker {
  border-color: var(--color-imperial-red);
  background: var(--color-imperial-red);
}
.term-count {
  color: var(--color-orange);
  font-size: 0.68rem;
  letter-spacing: 0.08em;
}

@media (max-width: 680px) {
  .lifepath-progress { padding-inline: 0.7rem; }
  .phase-label { font-size: 0.67rem; text-align: center; }
}
</style>
