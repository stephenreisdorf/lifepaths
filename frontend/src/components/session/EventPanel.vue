<script setup>
import TableRollEvent from '../events/TableRollEvent.vue'
import ChoiceEvent from '../events/ChoiceEvent.vue'
import AutomaticEvent from '../events/AutomaticEvent.vue'

const props = defineProps({
  event: Object,
  loading: Boolean,
})

const emit = defineEmits(['roll', 'choose', 'skip'])
</script>

<template>
  <div>
    <TableRollEvent
      v-if="event?.event_type === 'table_roll'"
      :event="event"
      :loading="loading"
      @roll="emit('roll', $event)"
    />
    <ChoiceEvent
      v-else-if="event?.event_type === 'choice'"
      :event="event"
      :loading="loading"
      @choose="emit('choose', $event)"
    />
    <AutomaticEvent
      v-else-if="event?.event_type === 'automatic'"
      :event="event"
      :loading="loading"
      @choose="emit('choose', $event)"
    />

    <div v-if="event?.is_optional" class="skip-row">
      <button
        class="secondary"
        @click="emit('skip', { eventId: event.id })"
        :disabled="loading"
      >
        Skip (optional)
      </button>
    </div>
  </div>
</template>

<style scoped>
.skip-row {
  margin-top: 0.75rem;
}
</style>
