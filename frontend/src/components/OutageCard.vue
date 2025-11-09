<template>
  <div class="outage-card" :class="{ active: active }">
    <div class="outage-header">
      <div>
        <span class="status-icon">{{ active ? '🔴' : '🟢' }}</span>
        <strong>{{ outage.host_name }}</strong>
        <span class="host-address">({{ outage.host_address }})</span>
      </div>
      <span class="status-text">{{ active ? 'ACTIVE' : 'RESOLVED' }}</span>
    </div>
    <div class="outage-details">
      <div class="detail-row">
        <span class="label">Started:</span>
        <span class="value">{{ formatDateTime(outage.start_time) }}</span>
      </div>
      <div class="detail-row" v-if="outage.end_time">
        <span class="label">Ended:</span>
        <span class="value">{{ formatDateTime(outage.end_time) }}</span>
      </div>
      <div class="detail-row">
        <span class="label">Duration:</span>
        <span class="value">{{ formatDuration(outage) }}</span>
      </div>
      <div class="detail-row">
        <span class="label">Failed Checks:</span>
        <span class="value">{{ outage.checks_failed }} / {{ outage.checks_during_outage }}</span>
      </div>
      <div class="detail-row" v-if="outage.recovery_success_rate">
        <span class="label">Recovery Rate:</span>
        <span class="value">{{ outage.recovery_success_rate.toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OutageCard',
  props: {
    outage: {
      type: Object,
      required: true
    },
    active: {
      type: Boolean,
      default: false
    }
  },
  setup() {
    const formatDateTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    const formatDuration = (outage) => {
      if (!outage.duration_seconds) {
        const now = new Date()
        const start = new Date(outage.start_time)
        const seconds = Math.floor((now - start) / 1000)
        return formatSeconds(seconds) + ' (ongoing)'
      }
      return formatSeconds(outage.duration_seconds)
    }

    const formatSeconds = (seconds) => {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60

      if (hours > 0) {
        return `${hours}h ${minutes}m`
      } else if (minutes > 0) {
        return `${minutes}m ${secs}s`
      } else {
        return `${secs}s`
      }
    }

    return {
      formatDateTime,
      formatDuration
    }
  }
}
</script>

<style scoped>
.outage-card {
  background: white;
  border: 2px solid var(--ace-gray-200);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.outage-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--ace-success);
  transition: all 0.3s ease;
}

.outage-card.active {
  border-color: var(--ace-danger);
  background: rgba(239, 68, 68, 0.02);
}

.outage-card.active::before {
  background: var(--ace-danger);
}

.outage-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.outage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--ace-gray-200);
}

.status-icon {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.host-address {
  color: var(--ace-gray-600);
  font-size: 0.9rem;
  margin-left: 0.5rem;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Courier New', monospace;
}

.status-text {
  font-weight: 600;
  font-size: 0.85rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  letter-spacing: 0.3px;
}

.outage-card.active .status-text {
  background: rgba(239, 68, 68, 0.1);
  color: var(--ace-danger);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.outage-card:not(.active) .status-text {
  background: rgba(16, 185, 129, 0.1);
  color: var(--ace-success);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.outage-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  padding: 0.25rem 0;
}

.detail-row .label {
  color: var(--ace-gray-600);
  font-weight: 500;
}

.detail-row .value {
  font-weight: 600;
  color: var(--ace-gray-900);
}
</style>
