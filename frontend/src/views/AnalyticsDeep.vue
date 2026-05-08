<template>
  <div class="page deep-page">
    <!-- 头部 -->
    <div class="deep-hero">
      <div class="deep-hero-icon">
        <el-icon :size="28" color="#fff"><TrendCharts /></el-icon>
      </div>
      <div class="deep-hero-text">
        <div class="deep-hero-title">深度分析</div>
        <div class="deep-hero-sub">基于大模型的趋势根因分析与风险预测</div>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="ctrl-panel">
      <div class="ctrl-inner">
        <el-select v-model="selectedLab" placeholder="选择实验室" style="width: 200px;" popper-class="dark-select">
          <el-option label="全部实验室" value="__all__" />
          <el-option v-for="lab in labs" :key="lab.id" :label="lab.name" :value="lab.name" />
        </el-select>
        <el-select v-model="days" style="width: 140px;" popper-class="dark-select">
          <el-option label="最近 7 天" :value="7" />
          <el-option label="最近 30 天" :value="30" />
          <el-option label="最近 90 天" :value="90" />
        </el-select>
        <el-button
          :type="loading === 'rca' ? 'info' : 'primary'"
          :loading="loading === 'rca'"
          class="btn-rca"
          @click="runRootCause"
        >
          <el-icon style="margin-right:4px;"><Search /></el-icon>根因分析
        </el-button>
        <el-button
          :type="loading === 'pred' ? 'info' : 'warning'"
          :loading="loading === 'pred'"
          class="btn-pred"
          @click="runPrediction"
        >
          <el-icon style="margin-right:4px;"><TrendCharts /></el-icon>风险预测
        </el-button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!rcaResult && !predResult && !loading" class="empty-state">
      <div class="empty-icon">
        <el-icon :size="48" color="#c0c4cc"><DataAnalysis /></el-icon>
      </div>
      <div class="empty-title">选择分析维度</div>
      <div class="empty-desc">选择实验室和时间范围，点击上方按钮开始深度分析</div>
      <div class="empty-cards">
        <div class="empty-card">
          <div class="empty-card-icon rca"><el-icon :size="20"><Search /></el-icon></div>
          <div class="empty-card-title">根因分析</div>
          <div class="empty-card-desc">从管理、设备、环境、人员四个维度挖掘隐患根本原因</div>
        </div>
        <div class="empty-card">
          <div class="empty-card-icon pred"><el-icon :size="20"><TrendCharts /></el-icon></div>
          <div class="empty-card-title">风险预测</div>
          <div class="empty-card-desc">基于历史时间序列和季节因素预测未来风险趋势</div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="loading-spin" :size="32" color="#ff7a1a"><Loading /></el-icon>
      <div class="loading-text">{{ loading === 'rca' ? '正在分析根因...' : '正在预测风险...' }}</div>
      <div class="loading-sub">大模型正在处理数据，请稍候</div>
    </div>

    <!-- 根因分析结果 -->
    <template v-if="rcaResult && !loading">
      <!-- 核心结论 -->
      <div class="insight-card rca-insight">
        <div class="insight-icon"><el-icon :size="20" color="#fff"><Search /></el-icon></div>
        <div class="insight-body">
          <div class="insight-title">根因分析 · {{ rcaResult.lab_name }} · 最近 {{ rcaResult.period_days }} 天</div>
          <div class="insight-text">{{ rcaResult.summary }}</div>
        </div>
      </div>

      <!-- 统计指标 -->
      <div class="metric-row">
        <div class="metric-item">
          <div class="metric-icon"><el-icon :size="18" color="#ff7a1a"><Warning /></el-icon></div>
          <div class="metric-data">
            <div class="metric-num">{{ rcaResult.stats?.total ?? 0 }}</div>
            <div class="metric-label">隐患总数</div>
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-icon"><el-icon :size="18" color="#3b82f6"><Camera /></el-icon></div>
          <div class="metric-data">
            <div class="metric-num">{{ rcaResult.stats?.detection_count ?? 0 }}</div>
            <div class="metric-label">识别次数</div>
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-icon"><el-icon :size="18" color="#10b981"><Grid /></el-icon></div>
          <div class="metric-data">
            <div class="metric-num">{{ Object.keys(rcaResult.stats?.by_category || {}).length }}</div>
            <div class="metric-label">涉及类别</div>
          </div>
        </div>
        <div class="metric-item">
          <div class="metric-icon"><el-icon :size="18" color="#ef4444"><RefreshLeft /></el-icon></div>
          <div class="metric-data">
            <div class="metric-num">{{ (rcaResult.stats?.recurring || []).length }}</div>
            <div class="metric-label">重复隐患</div>
          </div>
        </div>
      </div>

      <!-- 各实验室分布(全局分析时显示) -->
      <div v-if="labTableData.length > 1" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#3b82f6;"></span>
          <span class="section-name">各实验室隐患分布</span>
        </div>
        <div class="lab-rank-list">
          <div v-for="(row, i) in labTableData" :key="row.lab" class="lab-rank-item"
               :class="{ 'lab-rank-top3': i < 3 }"
               @click="selectedLab = (labs.find(l => l.name === row.lab)?.name || ''); runRootCause()"
          >
            <div class="lab-rank-left">
              <div class="lab-rank-num" :class="'rank-' + (i + 1)">{{ i + 1 }}</div>
              <div class="lab-rank-info">
                <div class="lab-rank-name">{{ row.lab }}</div>
                <el-tag size="small" effect="light" class="lab-rank-cat">{{ row.top_category }}</el-tag>
              </div>
            </div>
            <div class="lab-rank-right">
              <div class="lab-rank-metric">
                <div class="lab-rank-val">{{ row.count }}</div>
                <div class="lab-rank-label">隐患</div>
              </div>
              <div v-if="row.high > 0" class="lab-rank-metric danger">
                <div class="lab-rank-val">{{ row.high }}</div>
                <div class="lab-rank-label">高风险</div>
              </div>
              <div v-else class="lab-rank-metric safe">
                <div class="lab-rank-val">0</div>
                <div class="lab-rank-label">高风险</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 根因维度 -->
      <template v-if="rcaResult.root_causes?.length">
        <div class="section-card">
          <div class="section-header">
            <span class="section-dot" style="background:#8b5cf6;"></span>
            <span class="section-name">根因维度</span>
          </div>
          <div class="dim-grid">
            <div v-for="(rc, i) in rcaResult.root_causes" :key="i" class="dim-card"
                 :class="'dim-' + rc.dimension">
              <div class="dim-top">
                <span class="dim-name">{{ rc.dimension }}</span>
                <el-tag size="small" :type="rc.confidence === '高' ? 'danger' : rc.confidence === '中' ? 'warning' : 'info'" effect="dark">
                  {{ rc.confidence }}
                </el-tag>
              </div>
              <div class="dim-body">{{ rc.finding }}</div>
              <div class="dim-foot">证据: {{ rc.evidence }}</div>
            </div>
          </div>
        </div>
      </template>

      <!-- 风险热点 -->
      <div v-if="rcaResult.risk_hotspots?.length" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#ef4444;"></span>
          <span class="section-name">风险热点</span>
        </div>
        <div class="hotspot-list">
          <div v-for="(h, i) in rcaResult.risk_hotspots" :key="i" class="hotspot-item">
            <span class="hotspot-cat">{{ h.category }}</span>
            <el-tag size="small" :type="h.trend === '上升' ? 'danger' : h.trend === '下降' ? 'success' : 'info'" effect="plain">{{ h.trend }}</el-tag>
            <el-tag size="small" :type="h.urgency === '紧急' ? 'danger' : h.urgency === '重要' ? 'warning' : 'info'" effect="plain">{{ h.urgency }}</el-tag>
            <span class="hotspot-reason">{{ h.reason }}</span>
          </div>
        </div>
      </div>

      <!-- 整改建议 -->
      <div v-if="rcaResult.recommendations?.length" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#10b981;"></span>
          <span class="section-name">整改建议</span>
        </div>
        <div class="rec-list">
          <div v-for="(r, i) in rcaResult.recommendations" :key="i" class="rec-item">
            <span class="rec-num">{{ i + 1 }}</span>
            <span class="rec-text">{{ r }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 风险预测结果 -->
    <template v-if="predResult && !loading">
      <!-- 核心结论 -->
      <div class="insight-card pred-insight">
        <div class="insight-icon"><el-icon :size="20" color="#fff"><TrendCharts /></el-icon></div>
        <div class="insight-body">
          <div class="insight-title">风险预测 · {{ predResult.lab_name }} · 未来 {{ predResult.forecast_days }} 天</div>
          <div class="insight-text">{{ predResult.summary }}</div>
        </div>
      </div>

      <!-- 历史趋势评估 -->
      <div v-if="predResult.trend_assessment" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#3b82f6;"></span>
          <span class="section-name">历史趋势评估</span>
        </div>
        <div class="trend-text">{{ predResult.trend_assessment }}</div>
      </div>

      <!-- 预测时间线 -->
      <div v-if="predResult.forecast?.length" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#f59e0b;"></span>
          <span class="section-name">预测时间线</span>
        </div>
        <div class="timeline">
          <div v-for="(f, i) in predResult.forecast" :key="i" class="timeline-item">
            <div class="timeline-dot" :class="'sev-' + f.risk_level"></div>
            <div class="timeline-content">
              <div class="timeline-head">
                <span class="timeline-period">{{ f.period }}</span>
                <el-tag size="small" :type="severityTag(f.risk_level)" effect="dark">{{ severityLabel(f.risk_level) }}</el-tag>
                <el-tag size="small" effect="plain">置信度 {{ f.confidence }}</el-tag>
              </div>
              <div class="timeline-cats">{{ f.likely_categories?.join('、') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 早期预警 -->
      <div v-if="predResult.early_warnings?.length" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#ef4444;"></span>
          <span class="section-name">早期预警</span>
        </div>
        <div class="warning-list">
          <div v-for="(w, i) in predResult.early_warnings" :key="i" class="warning-item">
            <div class="warning-title">{{ w.category }}</div>
            <div class="warning-reason">{{ w.reason }}</div>
            <div class="warning-action">建议: {{ w.suggested_action }}</div>
          </div>
        </div>
      </div>

      <!-- 季节因素 -->
      <div v-if="predResult.seasonal_insights" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#10b981;"></span>
          <span class="section-name">季节因素洞察</span>
        </div>
        <div class="season-text">{{ predResult.seasonal_insights }}</div>
      </div>

      <!-- 历史趋势图 -->
      <div v-if="predResult.historical_trend?.length" class="section-card">
        <div class="section-header">
          <span class="section-dot" style="background:#06b6d4;"></span>
          <span class="section-name">历史隐患趋势</span>
        </div>
        <v-chart :option="trendChartOption" autoresize style="height: 220px;" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import { analyticsApi } from '@/api/analytics'
import { labApi } from '@/api/labs'
import type { Lab } from '@/types'
import { severityTag, severityLabel, severityColor } from '@/utils/severity'

use([CanvasRenderer, LineChart, BarChart, TooltipComponent, LegendComponent, GridComponent])

const loading = ref(false)
const selectedLab = ref('__all__')
const days = ref(30)
const labs = ref<Lab[]>([])
const rcaResult = ref<any>(null)
const predResult = ref<any>(null)

const labTableData = computed(() => {
  const byLab = rcaResult.value?.stats?.by_lab || {}
  return Object.entries(byLab).map(([lab, data]: [string, any]) => ({
    lab,
    count: data.count,
    high: data.high,
    top_category: data.top_category,
  }))
})

const trendChartOption = computed(() => {
  const data = predResult.value?.historical_trend || []
  if (!data.length) return {}
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, left: 40, right: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#e5e8ef' } },
      axisLabel: { color: '#8b94a3', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#8b94a3', fontSize: 10 },
    },
    series: [
      {
        type: 'line',
        name: '隐患数',
        smooth: true,
        data: data.map((d: any) => d.count),
        lineStyle: { width: 2, color: '#3b82f6' },
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.2)' }, { offset: 1, color: 'rgba(59,130,246,0.02)' }],
          },
        },
      },
      {
        type: 'line',
        name: '高风险',
        smooth: true,
        data: data.map((d: any) => d.high_risk_count),
        lineStyle: { width: 2, color: '#ef4444' },
        itemStyle: { color: '#ef4444' },
      },
    ],
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
  }
})

async function loadLabs() {
  try {
    const r = await labApi.list({ page_size: 999 })
    labs.value = r.results || []
  } catch {
    labs.value = []
  }
}

function _labParam() {
  return selectedLab.value === '__all__' ? '' : selectedLab.value
}

async function runRootCause() {
  loading.value = 'rca'
  try {
    rcaResult.value = await analyticsApi.rootCause(_labParam(), days.value)
    predResult.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '根因分析失败')
  } finally {
    loading.value = false
  }
}

async function runPrediction() {
  loading.value = 'pred'
  try {
    predResult.value = await analyticsApi.prediction(_labParam(), days.value, 30)
    rcaResult.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '风险预测失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLabs()
})
</script>

<style scoped>
.deep-page {
  padding: 0;
  background: #f2f4f8;
  min-height: 100%;
}

/* ===== Hero ===== */
.deep-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #1f2c4d 0%, #2c3a64 100%);
  color: #fff;
  position: relative;
  overflow: hidden;
}
.deep-hero::after {
  content: '';
  position: absolute;
  inset: auto 0 0 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #ff7a1a, #d62828, transparent);
}
.deep-hero-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 20px rgba(214, 40, 40, .35);
  z-index: 1;
}
.deep-hero-text { z-index: 1; }
.deep-hero-title {
  font-size: 22px; font-weight: 700; letter-spacing: .5px;
}
.deep-hero-sub {
  font-size: 13px; color: rgba(255,255,255,.7); margin-top: 4px;
}

/* ===== Control Panel ===== */
.ctrl-panel {
  padding: 16px 28px;
  background: #fff;
  border-bottom: 1px solid #e5e8ef;
  position: sticky;
  top: 0;
  z-index: 10;
}
.ctrl-inner {
  display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
}
.btn-rca {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
  border: none !important;
}
.btn-pred {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
  border: none !important;
}

/* ===== Empty State ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}
.empty-icon {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: #f3f5fa;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.empty-title { font-size: 18px; font-weight: 600; color: var(--txt-primary); margin-bottom: 6px; }
.empty-desc { font-size: 13px; color: var(--txt-muted); margin-bottom: 28px; }
.empty-cards {
  display: flex; gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}
.empty-card {
  width: 260px;
  padding: 24px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  text-align: center;
  transition: transform .2s ease, box-shadow .2s ease;
}
.empty-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,.08);
}
.empty-card-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff;
  margin-bottom: 12px;
}
.empty-card-icon.rca { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.empty-card-icon.pred { background: linear-gradient(135deg, #06b6d4, #0891b2); }
.empty-card-title { font-size: 15px; font-weight: 600; color: var(--txt-primary); margin-bottom: 6px; }
.empty-card-desc { font-size: 12px; color: var(--txt-muted); line-height: 1.6; }

/* ===== Loading State ===== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}
.loading-spin { animation: spin 1.2s linear infinite; }
@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
.loading-text { font-size: 16px; font-weight: 600; color: var(--txt-primary); margin-top: 16px; }
.loading-sub { font-size: 12px; color: var(--txt-muted); margin-top: 6px; }

/* ===== Insight Card ===== */
.insight-card {
  display: flex;
  gap: 14px;
  padding: 18px 24px;
  margin: 16px 28px 0;
  border-radius: 12px;
  color: #fff;
  position: relative;
  overflow: hidden;
}
.rca-insight {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  box-shadow: 0 6px 20px rgba(139, 92, 246, .25);
}
.pred-insight {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  box-shadow: 0 6px 20px rgba(6, 182, 212, .25);
}
.insight-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  background: rgba(255,255,255,.15);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.insight-title { font-size: 12px; opacity: .8; margin-bottom: 4px; }
.insight-text { font-size: 14px; font-weight: 500; line-height: 1.6; }

/* ===== Metric Row ===== */
.metric-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 16px 28px;
}
@media (max-width: 768px) {
  .metric-row { grid-template-columns: repeat(2, 1fr); }
}
.metric-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--line-soft);
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
  transition: transform .2s ease;
}
.metric-item:hover { transform: translateY(-2px); }
.metric-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  background: #f3f5fa;
  display: flex; align-items: center; justify-content: center;
}
.metric-num { font-size: 24px; font-weight: 700; color: var(--txt-primary); line-height: 1.2; }
.metric-label { font-size: 12px; color: var(--txt-muted); margin-top: 2px; }

/* ===== Section Card ===== */
.section-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--line-soft);
  margin: 0 28px 14px;
  padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.section-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
}
.section-name { font-size: 14px; font-weight: 600; color: var(--txt-primary); }

/* ===== Dim Grid ===== */
.dim-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
@media (max-width: 768px) {
  .dim-grid { grid-template-columns: 1fr; }
}
.dim-card {
  padding: 16px 18px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line-soft);
  transition: box-shadow .2s ease;
}
.dim-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.dim-card.dim-管理 {
  background: linear-gradient(180deg, #fff 0%, #fffbeb 100%);
  border-left: 3px solid #f59e0b;
}
.dim-card.dim-设备 {
  background: linear-gradient(180deg, #fff 0%, #eff6ff 100%);
  border-left: 3px solid #3b82f6;
}
.dim-card.dim-环境 {
  background: linear-gradient(180deg, #fff 0%, #f0fdf4 100%);
  border-left: 3px solid #10b981;
}
.dim-card.dim-人员 {
  background: linear-gradient(180deg, #fff 0%, #fdf2f8 100%);
  border-left: 3px solid #ec4899;
}
.dim-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.dim-name { font-weight: 600; font-size: 14px; color: var(--txt-primary); }
.dim-body { font-size: 13px; color: var(--txt-primary); line-height: 1.7; margin-bottom: 6px; }
.dim-foot { font-size: 11px; color: var(--txt-muted); line-height: 1.5; }

/* ===== Hotspot ===== */
.hotspot-list { display: flex; flex-direction: column; gap: 8px; }
.hotspot-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  flex-wrap: wrap;
}
.hotspot-cat { font-weight: 600; color: var(--txt-primary); font-size: 13px; min-width: 80px; }
.hotspot-reason { color: var(--txt-secondary); font-size: 12px; flex: 1; }

/* ===== Recommendations ===== */
.rec-list { display: flex; flex-direction: column; gap: 8px; }
.rec-item {
  display: flex; gap: 10px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 8px;
  align-items: flex-start;
}
.rec-num {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rec-text { font-size: 13px; color: var(--txt-secondary); line-height: 1.6; flex: 1; }

/* ===== Timeline ===== */
.timeline { position: relative; padding-left: 20px; }
.timeline::before {
  content: '';
  position: absolute;
  left: 6px; top: 8px; bottom: 8px;
  width: 2px;
  background: linear-gradient(180deg, #f59e0b, #ef4444);
  border-radius: 1px;
}
.timeline-item {
  display: flex;
  gap: 14px;
  padding: 10px 0;
  position: relative;
}
.timeline-dot {
  width: 14px; height: 14px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px currentColor;
  position: absolute;
  left: -20px; top: 14px;
  z-index: 1;
}
.timeline-dot.sev-high { background: #ef4444; box-shadow: 0 0 0 2px #ef4444; }
.timeline-dot.sev-medium { background: #f59e0b; box-shadow: 0 0 0 2px #f59e0b; }
.timeline-dot.sev-low { background: #10b981; box-shadow: 0 0 0 2px #10b981; }
.timeline-content { flex: 1; }
.timeline-head {
  display: flex; align-items: center; gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.timeline-period { font-weight: 600; color: var(--txt-primary); font-size: 13px; }
.timeline-cats { font-size: 12px; color: var(--txt-secondary); margin-top: 2px; }

/* ===== Warning ===== */
.warning-list { display: flex; flex-direction: column; gap: 10px; }
.warning-item {
  padding: 14px 16px;
  background: linear-gradient(180deg, #fff 0%, #fef2f2 100%);
  border: 1px solid #fecaca;
  border-radius: 10px;
  border-left: 3px solid #ef4444;
}
.warning-title { font-weight: 600; color: #dc2626; font-size: 13px; margin-bottom: 4px; }
.warning-reason { font-size: 12px; color: var(--txt-secondary); margin-bottom: 4px; }
.warning-action { font-size: 12px; color: #b45309; }

/* ===== Season & Trend ===== */
.season-text {
  padding: 14px 16px;
  background: linear-gradient(180deg, #fff 0%, #f0fdfa 100%);
  border-radius: 10px;
  font-size: 13px;
  color: var(--txt-secondary);
  line-height: 1.7;
}
.trend-text {
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 10px;
  font-size: 13px;
  color: var(--txt-secondary);
  line-height: 1.7;
}

/* ===== Table ===== */
.high-risk-num { color: #dc2626; font-weight: 600; }

/* ===== Lab Rank List ===== */
.lab-rank-list { display: flex; flex-direction: column; gap: 8px; }
.lab-rank-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  cursor: pointer;
  transition: all .2s ease;
}
.lab-rank-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59,130,246,.1);
  transform: translateX(4px);
}
.lab-rank-top3 { background: linear-gradient(90deg, #fff 0%, #f8fafc 100%); }
.lab-rank-left { display: flex; align-items: center; gap: 12px; }
.lab-rank-num {
  width: 28px; height: 28px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
  color: #fff;
  background: #c0c4cc;
  flex-shrink: 0;
}
.lab-rank-num.rank-1 { background: linear-gradient(135deg, #ff7a1a, #d62828); }
.lab-rank-num.rank-2 { background: linear-gradient(135deg, #f59e0b, #f97316); }
.lab-rank-num.rank-3 { background: linear-gradient(135deg, #3b82f6, #1e40af); }
.lab-rank-info { display: flex; flex-direction: column; gap: 4px; }
.lab-rank-name { font-weight: 600; font-size: 14px; color: var(--txt-primary); }
.lab-rank-cat { --el-tag-bg-color: #f3f5fa !important; --el-tag-border-color: transparent !important; }
.lab-rank-right { display: flex; align-items: center; gap: 20px; }
.lab-rank-metric { text-align: center; }
.lab-rank-metric.danger .lab-rank-val { color: #dc2626; }
.lab-rank-metric.safe .lab-rank-val { color: #10b981; }
.lab-rank-val { font-size: 20px; font-weight: 700; line-height: 1.2; }
.lab-rank-label { font-size: 11px; color: var(--txt-muted); margin-top: 2px; }
</style>
