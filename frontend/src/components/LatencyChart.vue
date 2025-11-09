<template>
  <div class="chart-container">
    <canvas ref="chartCanvas"></canvas>
    <div v-if="loading" class="chart-loading">Loading chart data...</div>
    <div v-if="error" class="chart-error">{{ error }}</div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import api from '../services/api'

Chart.register(...registerables)

export default {
  name: 'LatencyChart',
  props: {
    hostAddress: {
      type: String,
      required: true
    },
    hours: {
      type: Number,
      default: 24
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    const loading = ref(true)
    const error = ref(null)
    let chartInstance = null

    const loadChartData = async () => {
      try {
        loading.value = true
        error.value = null

        const results = await api.getPingResults(props.hostAddress, props.hours, 500)

        if (!results || results.length === 0) {
          error.value = 'No data available for selected time range'
          return
        }

        // Sort by timestamp
        results.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

        const labels = results.map(r => new Date(r.timestamp).toLocaleTimeString())
        const avgLatencies = results.map(r => r.avg_latency || null)
        const minLatencies = results.map(r => r.min_latency || null)
        const maxLatencies = results.map(r => r.max_latency || null)
        const successRates = results.map(r => r.success_rate)

        // Destroy existing chart
        if (chartInstance) {
          chartInstance.destroy()
        }

        // Create new chart
        const ctx = chartCanvas.value.getContext('2d')
        chartInstance = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: [
              {
                label: 'Avg Latency (ms)',
                data: avgLatencies,
                borderColor: '#c0d201',
                backgroundColor: 'rgba(192, 210, 1, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                yAxisID: 'y',
                fill: true
              },
              {
                label: 'Min Latency (ms)',
                data: minLatencies,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                borderWidth: 1,
                borderDash: [5, 5],
                tension: 0.4,
                yAxisID: 'y'
              },
              {
                label: 'Max Latency (ms)',
                data: maxLatencies,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.05)',
                borderWidth: 1,
                borderDash: [5, 5],
                tension: 0.4,
                yAxisID: 'y'
              },
              {
                label: 'Success Rate (%)',
                data: successRates,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                yAxisID: 'y1',
                fill: true
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            interaction: {
              mode: 'index',
              intersect: false
            },
            plugins: {
              legend: {
                position: 'top',
                labels: {
                  usePointStyle: true,
                  padding: 15,
                  font: {
                    size: 12,
                    weight: '500'
                  }
                }
              },
              tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(26, 26, 26, 0.9)',
                titleColor: '#c0d201',
                bodyColor: '#ffffff',
                borderColor: '#c0d201',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8
              }
            },
            scales: {
              x: {
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)',
                  drawBorder: false
                },
                ticks: {
                  font: {
                    size: 11
                  },
                  color: '#666666'
                }
              },
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                  display: true,
                  text: 'Latency (ms)',
                  font: {
                    size: 12,
                    weight: '600'
                  },
                  color: '#1a1a1a'
                },
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)',
                  drawBorder: false
                },
                ticks: {
                  font: {
                    size: 11
                  },
                  color: '#666666'
                }
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                  display: true,
                  text: 'Success Rate (%)',
                  font: {
                    size: 12,
                    weight: '600'
                  },
                  color: '#1a1a1a'
                },
                min: 0,
                max: 100,
                grid: {
                  drawOnChartArea: false
                },
                ticks: {
                  font: {
                    size: 11
                  },
                  color: '#666666'
                }
              }
            }
          }
        })
      } catch (err) {
        error.value = 'Failed to load chart data: ' + err.message
        console.error('Chart error:', err)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadChartData()
    })

    watch(() => [props.hostAddress, props.hours], () => {
      loadChartData()
    })

    return {
      chartCanvas,
      loading,
      error
    }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  min-height: 300px;
  padding: 1rem;
  background: white;
  border-radius: 8px;
}

.chart-loading, .chart-error {
  text-align: center;
  padding: 2rem;
  color: var(--ace-gray-600);
  font-weight: 500;
}

.chart-error {
  color: var(--ace-danger);
}
</style>
