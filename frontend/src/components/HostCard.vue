<template>
  <div class="host-card" :class="statusClass">
    <div class="host-header">
      <h3>{{ result.host_name }}</h3>
      <span class="status-badge" :class="statusClass">{{ statusText }}</span>
    </div>
    <div class="host-address">{{ result.host_address }}</div>
    <div class="host-metrics">
      <div class="metric">
        <span class="label">Success Rate</span>
        <span class="value">{{ result.success_rate.toFixed(1) }}%</span>
      </div>
      <div class="metric" v-if="result.avg_latency">
        <span class="label">Avg Latency</span>
        <span class="value">{{ result.avg_latency.toFixed(1) }}ms</span>
      </div>
      <div class="metric" v-if="result.min_latency">
        <span class="label">Min / Max</span>
        <span class="value">{{ result.min_latency.toFixed(1) }} / {{ result.max_latency.toFixed(1) }}ms</span>
      </div>
      <div class="metric">
        <span class="label">Last Check</span>
        <span class="value">{{ formatTime(result.timestamp) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'HostCard',
  props: {
    result: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const statusClass = computed(() => {
      if (props.result.success_rate >= 95) return 'status-healthy'
      if (props.result.success_rate >= 80) return 'status-degraded'
      return 'status-down'
    })

    const statusText = computed(() => {
      if (props.result.success_rate >= 95) return '● Healthy'
      if (props.result.success_rate >= 80) return '● Degraded'
      return '● Down'
    })

    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    }

    return {
      statusClass,
      statusText,
      formatTime
    }
  }
}
</script>

<style scoped>
.host-card {
  background: white;
  border: 2px solid var(--ace-gray-200);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.host-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--ace-gray-300);
  transition: all 0.3s ease;
}

.host-card:hover {
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
  transform: translateY(-4px);
  border-color: var(--ace-lime);
}

.host-card.status-healthy::before {
  background: var(--ace-success);
}

.host-card.status-degraded::before {
  background: var(--ace-warning);
}

.host-card.status-down::before {
  background: var(--ace-danger);
}

.host-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.host-header h3 {
  font-size: 1.1rem;
  color: var(--ace-gray-900);
  font-weight: 600;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.status-badge.status-healthy {
  background: rgba(16, 185, 129, 0.1);
  color: var(--ace-success);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.status-degraded {
  background: rgba(245, 158, 11, 0.1);
  color: var(--ace-warning);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-badge.status-down {
  background: rgba(239, 68, 68, 0.1);
  color: var(--ace-danger);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.host-address {
  color: var(--ace-gray-600);
  font-size: 0.9rem;
  margin-bottom: 1rem;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Courier New', monospace;
}

.host-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  padding: 0.25rem 0;
}

.metric .label {
  color: var(--ace-gray-600);
  font-weight: 500;
}

.metric .value {
  font-weight: 600;
  color: var(--ace-gray-900);
}
</style>
