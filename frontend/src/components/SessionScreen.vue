<script setup>
import { computed } from 'vue'
import StageHeader from './session/StageHeader.vue'
import EventPanel from './session/EventPanel.vue'
import OutcomePanel from './session/OutcomePanel.vue'
import RepeatPrompt from './session/RepeatPrompt.vue'
import StatsSidebar from './session/StatsSidebar.vue'

const props = defineProps({
  sessionState: Object,
  lifepathConfig: Object,
  lastOutcome: Object,
  loading: Boolean,
  characterName: String,
})

const emit = defineEmits(['roll', 'choose', 'skip', 'advance', 'outcome-dismissed'])

const currentStage = computed(() => {
  if (!props.sessionState || !props.lifepathConfig) return null
  const stageId = props.sessionState.current_stage_id
  if (!stageId) return null
  return props.lifepathConfig.stages[stageId] ?? null
})

const currentEvent = computed(() => {
  const state = props.sessionState
  const stage = currentStage.value
  if (!state || !stage) return null
  if (state.injected_event_ids.length > 0) {
    const id = state.injected_event_ids[0]
    return stage.events.find(e => e.id === id) ?? null
  }
  return stage.events[state.pending_event_index] ?? null
})

const awaitingRepeatDecision = computed(() => {
  const state = props.sessionState
  const stage = currentStage.value
  if (!state || !stage) return false
  const allDone =
    state.pending_event_index >= stage.events.length &&
    state.injected_event_ids.length === 0
  return allDone && stage.is_repeatable
})

const canRepeat = computed(() => {
  const visits = props.sessionState?.stage_visit_counts[currentStage.value?.id] ?? 0
  const max = currentStage.value?.max_repeats
  return max == null || visits < max
})

const visitCount = computed(() => {
  if (!props.sessionState || !currentStage.value) return 0
  return props.sessionState.stage_visit_counts[currentStage.value.id] ?? 0
})

const sessionComplete = computed(() => props.sessionState?.status === 'completed')
</script>

<template>
  <div class="session-layout">
    <StageHeader
      class="stage-header"
      :stage="currentStage"
      :visit-count="visitCount"
    />

    <main class="event-area">
      <RepeatPrompt
        v-if="awaitingRepeatDecision && !lastOutcome"
        :stage="currentStage"
        :can-repeat="canRepeat"
        :loading="loading"
        @advance="emit('advance', $event)"
      />
      <EventPanel
        v-else-if="currentEvent && !lastOutcome"
        :event="currentEvent"
        :loading="loading"
        @roll="emit('roll', $event)"
        @choose="emit('choose', $event)"
        @skip="emit('skip', $event)"
      />
    </main>

    <StatsSidebar
      class="sidebar"
      :session-state="sessionState"
      :character-name="characterName"
    />
  </div>

  <OutcomePanel
    v-if="lastOutcome"
    :outcome="lastOutcome"
    :session-complete="sessionComplete"
    @dismissed="emit('outcome-dismissed')"
  />
</template>

<style scoped>
.session-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 1100px;
  margin: 0 auto;
  align-content: start;
}

.stage-header {
  grid-column: 1 / -1;
}

.event-area {
  min-width: 0;
}

.sidebar {
  align-self: start;
  position: sticky;
  top: 1.5rem;
}
</style>
