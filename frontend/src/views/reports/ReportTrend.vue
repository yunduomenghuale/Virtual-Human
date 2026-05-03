<template>
  <div class="page" v-loading="loading">
    <el-page-header @back="$router.back()" :content="`「${labName}」 趋势分析`" style="margin-bottom: 14px;" />

    <div class="card-row" style="margin-bottom: 14px;">
      <div class="metric-card hoverable" :style="{ '--accent': '#3b82f6' }">
        <div class="metric-icon"><el-icon :size="20"><Histogram /></el-icon></div>
        <div class="metric-text">
          <div class="muted">报告次数</div>
          <div class="metric-value">{{ points.length }}</div>
        </div>
      </div>
      <div class="metric-card hoverable" :style="{ '--accent': '#ef4444' }">
        <div class="metric-icon"><el-icon :size="20"><Warning /></el-icon></div>
        <div class="metric-text">
          <div class="muted">累计高风险</div>
          <div class="metric-value">{{ totalHigh }}</div>
        </div>
      </div>
      <div class="metric-card hoverable" :style="{ '--accent': '#f59e0b' }">
        <div class="metric-icon"><el-icon :size="20"><DataLine /></el-icon></div>
        <div class="metric-text">
          <div class="muted">平均隐患 / 次</div>
          <div class="metric-value">{{ avgHazards }}</div>
        </div>
      </div>
      <div class="metric-card hoverable" :style="{ '--accent': '#10b981' }">
        <div class="metric-icon"><el-icon :size="20"><Calendar /></el-icon></div>
        <div class="metric-text">
          <div class="muted">最近报告</div>
          <div class="metric-value" style="font-size: 16px;">{{ latestAt }}</div>
        </div>
      </div>
    </div>

    <el-card class="hoverable">
      <template #header><span class="section-title" style="margin:0;">报告时间序列</span></template>
      <div ref="trendChart" style="height: 360px;"></div>
    </el-card>

    <el-card style="margin-top: 14px;" class="hoverable">
      <template #header><span class="section-title" style="margin:0;">逐次报告</span></template>
      <el-table :data="points" stripe>
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="total" label="隐患数" width="90" align="center" />
        <el-table-column prop="high" label="高" width="70" align="center">
          <template #default="{ row }">
            <span class="severity-high" style="font-weight: 600;">{{ row.high }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="medium" label="中" width="70" align="center">
          <template #default="{ row }">
            <span class="severity-medium" style="font-weight: 600;">{{ row.medium }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="low" label="低" width="70" align="center">
          <template #default="{ row }">
            <span class="severity-low" style="font-weight: 600;">{{ row.low }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="severityTag(row.overall_severity)">{{ severityLabel(row.overall_severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/reports/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { reportApi } from '@/api/reports'
import { severityTag, severityLabel, severityColor } from '@/utils/severity'

const route = useRoute()
const labName = computed(() => decodeURIComponent(route.params.lab as string))
const points = ref<any[]>([])
const loading = ref(false)
const trendChart = ref<HTMLElement>()

const totalHigh = computed(() => points.value.reduce((s, p) => s + (p.high || 0), 0))
const avgHazards = computed(() => {
  if (!points.value.length) return 0
  const sum = points.value.reduce((s, p) => s + (p.total || 0), 0)
  return (sum / points.value.length).toFixed(1)
})
const latestAt = computed(() => {
  if (!points.value.length) return '-'
  const last = points.value[points.value.length - 1]
  return last?.created_at || '-'
})

async function load() {
  loading.value = true
  try {
    const r = await reportApi.trend(labName.value)
    points.value = r.points || []
    await nextTick()
    if (trendChart.value) {
      echarts.init(trendChart.value).setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['总隐患', '高', '中', '低'], bottom: 0 },
        grid: { top: 40, left: 40, right: 20, bottom: 50 },
        xAxis: { type: 'category', data: points.value.map(p => p.created_at) },
        yAxis: { type: 'value' },
        series: [
          { name: '总隐患', type: 'line', smooth: true, lineStyle: { width: 3 },
            areaStyle: { opacity: .15 },
            itemStyle: { color: '#1f2c4d' },
            data: points.value.map(p => p.total) },
          { name: '高', type: 'line', smooth: true,
            data: points.value.map(p => p.high), itemStyle: { color: severityColor('high') } },
          { name: '中', type: 'line', smooth: true,
            data: points.value.map(p => p.medium), itemStyle: { color: severityColor('medium') } },
          { name: '低', type: 'line', smooth: true,
            data: points.value.map(p => p.low), itemStyle: { color: severityColor('low') } },
        ],
      })
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.metric-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 16px 18px;
  display: flex; gap: 14px; align-items: center;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  transition: transform .2s ease, box-shadow .2s ease;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}
.metric-icon {
  width: 42px; height: 42px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  background: var(--accent);
  box-shadow: 0 6px 14px color-mix(in srgb, var(--accent) 35%, transparent);
}
.metric-text { flex: 1; min-width: 0; }
.metric-value {
  font-size: 24px; font-weight: 700;
  color: var(--txt-primary);
  margin-top: 2px;
  line-height: 1.1;
  letter-spacing: .5px;
}
</style>
