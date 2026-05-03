<template>
  <div class="page" v-loading="loading">
    <div class="card-row">
      <div v-for="item in metrics" :key="item.title" class="metric-card hoverable"
           :style="{ '--accent': item.color }">
        <div class="metric-icon">
          <el-icon :size="22"><component :is="item.icon" /></el-icon>
        </div>
        <div class="metric-text">
          <div class="muted">{{ item.title }}</div>
          <div class="metric-value">{{ item.value }}</div>
        </div>
      </div>
    </div>

    <el-row :gutter="14" style="margin-top: 14px;">
      <el-col :span="8"><el-card class="hoverable"><template #header>风险等级分布</template><div ref="sevEl" style="height: 280px;" /></el-card></el-col>
      <el-col :span="8"><el-card class="hoverable"><template #header>类别分布 Top 10</template><div ref="catEl" style="height: 280px;" /></el-card></el-col>
      <el-col :span="8"><el-card class="hoverable"><template #header>近 30 天 skill 调用</template><div ref="skillEl" style="height: 280px;" /></el-card></el-col>
    </el-row>

    <el-card style="margin-top: 14px;" class="hoverable">
      <template #header>近 30 天隐患识别量</template>
      <div ref="trendEl" style="height: 280px;" />
    </el-card>

    <el-card style="margin-top: 14px;" class="hoverable">
      <template #header>隐患高发地点 TOP 5</template>
      <el-table :data="dash?.top_labs || []">
        <el-table-column type="index" width="50" />
        <el-table-column prop="lab_name" label="地点" />
        <el-table-column prop="hazards" label="累计隐患" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { analyticsApi } from '@/api/analytics'
import { severityColor } from '@/utils/severity'

const loading = ref(false)
const dash = ref<any>(null)
const sevEl = ref<HTMLElement>()
const catEl = ref<HTMLElement>()
const skillEl = ref<HTMLElement>()
const trendEl = ref<HTMLElement>()

const metrics = computed(() => {
  const o = dash.value?.overview || {}
  return [
    { title: '用户总数', value: o.users?.total || 0, icon: 'User', color: '#3b82f6' },
    { title: '知识库文档', value: o.knowledge_docs || 0, icon: 'Collection', color: '#10b981' },
    { title: '问答记录', value: o.qa_sessions || 0, icon: 'ChatLineSquare', color: '#8b5cf6' },
    { title: '隐患识别', value: o.detections || 0, icon: 'Picture', color: '#ef4444' },
    { title: '报告', value: o.reports || 0, icon: 'Document', color: '#f59e0b' },
  ]
})

async function load() {
  loading.value = true
  try {
    dash.value = await analyticsApi.dashboard()
    await nextTick()
    drawCharts()
  } finally {
    loading.value = false
  }
}

function drawCharts() {
  const sev = dash.value?.severity_distribution || {}
  const cats = dash.value?.category_distribution || []
  const skill = dash.value?.skill_usage || {}
  const trend = dash.value?.detection_trend || []

  if (sevEl.value) {
    echarts.init(sevEl.value).setOption({
      tooltip: {}, legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: ['45%', '72%'],
        data: [
          { name: '高', value: sev.high || 0, itemStyle: { color: severityColor('high') } },
          { name: '中', value: sev.medium || 0, itemStyle: { color: severityColor('medium') } },
          { name: '低', value: sev.low || 0, itemStyle: { color: severityColor('low') } },
        ],
      }],
    })
  }
  if (catEl.value) {
    echarts.init(catEl.value).setOption({
      tooltip: {}, grid: { top: 20, left: 70, right: 30, bottom: 30 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: cats.map((c: any) => c.category).reverse() },
      series: [{ type: 'bar', data: cats.map((c: any) => c.count).reverse(),
                 itemStyle: { color: '#409eff' } }],
    })
  }
  if (skillEl.value) {
    echarts.init(skillEl.value).setOption({
      tooltip: {},
      xAxis: { type: 'category', data: ['知识问答', '隐患识别', '报告生成'] },
      yAxis: { type: 'value' },
      series: [{ type: 'bar',
                 data: [skill.knowledge_qa || 0, skill.hazard_detect || 0, skill.report_gen || 0],
                 itemStyle: { color: '#67c23a' } }],
    })
  }
  if (trendEl.value) {
    echarts.init(trendEl.value).setOption({
      tooltip: { trigger: 'axis' },
      grid: { top: 30, left: 40, right: 20, bottom: 40 },
      xAxis: { type: 'category', data: trend.map((p: any) => p.date) },
      yAxis: { type: 'value' },
      series: [{ type: 'line', smooth: true, areaStyle: {},
                 data: trend.map((p: any) => p.count) }],
    })
  }
}

onMounted(load)
</script>

<style scoped>
.metric-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 18px;
  display: flex;
  gap: 14px;
  align-items: center;
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
  width: 44px; height: 44px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  background: var(--accent);
  box-shadow: 0 6px 14px color-mix(in srgb, var(--accent) 35%, transparent);
}
.metric-text { flex: 1; min-width: 0; }
.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--txt-primary);
  margin-top: 2px;
  line-height: 1.1;
  letter-spacing: .5px;
}
</style>
