<template>
  <div id="app">
    <header class="header">
      <h1>🌐 ACE Connection Logger</h1>
      <div class="header-info">
        <span v-if="systemStatus">{{ systemStatus.total_hosts }} hosts monitored</span>
        <span v-if="systemStatus"> | Interval: {{ systemStatus.monitoring_interval }}s</span>
        <button @click="refreshData" class="refresh-btn">🔄 Refresh</button>
      </div>
    </header>

    <main class="container">
      <!-- Current Status Section -->
      <section class="section">
        <h2>Current Host Status</h2>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else class="host-grid">
          <HostCard
            v-for="result in latestResults"
            :key="result.host_address"
            :result="result"
          />
        </div>
      </section>

      <!-- Active Outages Section -->
      <section v-if="activeOutages.length > 0" class="section alert">
        <h2>🔴 Active Outages</h2>
        <div class="outage-list">
          <OutageCard
            v-for="outage in activeOutages"
            :key="outage.id"
            :outage="outage"
            :active="true"
          />
        </div>
      </section>

      <!-- Charts Section -->
      <section class="section">
        <h2>Performance Trends</h2>
        <div class="chart-controls">
          <label>
            Host:
            <select v-model="selectedHost">
              <option v-for="host in hosts" :key="host.address" :value="host.address">
                {{ host.name }} ({{ host.address }})
              </option>
            </select>
          </label>
          <label>
            Time Range:
            <select v-model="timeRange">
              <option :value="1">Last Hour</option>
              <option :value="6">Last 6 Hours</option>
              <option :value="24">Last 24 Hours</option>
              <option :value="168">Last 7 Days</option>
            </select>
          </label>
        </div>
        <LatencyChart
          v-if="selectedHost"
          :host-address="selectedHost"
          :hours="timeRange"
        />
      </section>

      <!-- Recent Outages Section -->
      <section class="section">
        <h2>Recent Outage Events</h2>
        <div class="outage-list">
          <OutageCard
            v-for="outage in recentOutages"
            :key="outage.id"
            :outage="outage"
            :active="false"
          />
          <div v-if="recentOutages.length === 0" class="no-data">
            No outage events in selected time range
          </div>
        </div>
      </section>
    </main>

    <footer class="footer">
      <p>ACE Connection Logger v0.2.0 | FastAPI + Vue.js</p>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import api from './services/api'
import HostCard from './components/HostCard.vue'
import OutageCard from './components/OutageCard.vue'
import LatencyChart from './components/LatencyChart.vue'

export default {
  name: 'App',
  components: {
    HostCard,
    OutageCard,
    LatencyChart
  },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const systemStatus = ref(null)
    const latestResults = ref([])
    const activeOutages = ref([])
    const recentOutages = ref([])
    const hosts = ref([])
    const selectedHost = ref(null)
    const timeRange = ref(24)
    let refreshInterval = null

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null

        // Load all data in parallel
        const [status, latest, active, recent, hostList] = await Promise.all([
          api.getStatus(),
          api.getLatestResults(),
          api.getActiveOutages(),
          api.getOutageEvents(null, false, 7, 20),
          api.getHosts()
        ])

        systemStatus.value = status
        latestResults.value = latest
        activeOutages.value = active
        recentOutages.value = recent
        hosts.value = hostList

        // Set default selected host
        if (!selectedHost.value && hostList.length > 0) {
          selectedHost.value = hostList[0].address
        }
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
        console.error('Error loading data:', err)
      } finally {
        loading.value = false
      }
    }

    const refreshData = () => {
      loadData()
    }

    onMounted(() => {
      loadData()
      // Auto-refresh every 30 seconds
      refreshInterval = setInterval(loadData, 30000)
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      loading,
      error,
      systemStatus,
      latestResults,
      activeOutages,
      recentOutages,
      hosts,
      selectedHost,
      timeRange,
      refreshData
    }
  }
}
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--ace-gray-900);
  color: white;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--ace-lime);
}

.header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.9rem;
  color: var(--ace-gray-300);
}

.refresh-btn {
  background: var(--ace-lime);
  border: none;
  color: var(--ace-gray-900);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  background: var(--ace-lime-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(192, 210, 1, 0.3);
}

.container {
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: 1px solid var(--ace-gray-200);
  transition: box-shadow 0.2s ease;
}

.section:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.section.alert {
  border-left: 4px solid var(--ace-danger);
  background: #fef2f2;
}

.section h2 {
  margin-bottom: 1.5rem;
  color: var(--ace-gray-900);
  font-weight: 600;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.host-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.chart-controls {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.chart-controls label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-controls select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--ace-gray-300);
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
  color: var(--ace-gray-900);
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-controls select:hover {
  border-color: var(--ace-lime);
}

.chart-controls select:focus {
  outline: none;
  border-color: var(--ace-lime);
  box-shadow: 0 0 0 3px rgba(192, 210, 1, 0.1);
}

.outage-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.loading, .error, .no-data {
  text-align: center;
  padding: 2rem;
  color: var(--ace-gray-600);
}

.error {
  color: var(--ace-danger);
}

.footer {
  background: var(--ace-gray-900);
  color: var(--ace-gray-300);
  text-align: center;
  padding: 1rem;
  font-size: 0.9rem;
  border-top: 4px solid var(--ace-lime);
}
</style>
