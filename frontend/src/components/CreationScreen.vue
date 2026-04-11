<script setup>
import { reactive, computed, watch } from 'vue'
import StatsTable from './StatsTable.vue'
import SkillGrid from './SkillGrid.vue'

const props = defineProps({
  characteristics: Object,
  prompt: Object,
  resolvedSteps: Array,
  error: String,
})

const emit = defineEmits(['confirm'])

const selected = reactive(new Set())

watch(() => props.prompt, () => {
  selected.clear()
})

function toggleOption(option) {
  if (selected.has(option)) {
    selected.delete(option)
  } else {
    selected.add(option)
  }
}

const canConfirm = computed(() => {
  if (!props.prompt?.required_count) return selected.size > 0
  return selected.size === props.prompt.required_count
})

function confirm() {
  emit('confirm', [...selected])
}
</script>

<template>
  <div>
    <h2>Characteristics</h2>
    <StatsTable :characteristics="characteristics" />

    <div v-if="resolvedSteps?.length" class="resolved-steps">
      <div v-for="step in resolvedSteps" :key="step.step_id" class="resolved-step">
        <p><strong>{{ step.description }}</strong></p>
        <pre v-if="step.data">{{ JSON.stringify(step.data, null, 2) }}</pre>
      </div>
    </div>

    <div v-if="prompt">
      <h2>{{ prompt.description }}</h2>
      <p v-if="prompt.required_count" class="skill-counter">
        Select <span>{{ prompt.required_count }}</span>:
      </p>
      <SkillGrid
        v-if="prompt.options"
        :skills="prompt.options"
        :selected="selected"
        @toggle="toggleOption"
      />
      <p v-if="prompt.required_count" class="skill-counter">
        <span>{{ selected.size }}</span> / <span>{{ prompt.required_count }}</span> selected
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <button :disabled="!canConfirm" @click="confirm">Confirm</button>
    </div>
  </div>
</template>
