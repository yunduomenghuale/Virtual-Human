<template>
  <div class="page dashboard-page" v-loading="loading">
    <!-- ========== 管理员大屏 ========== -->
    <template v-if="auth.isAdmin">
      <!-- 大屏 Hero -->
      <div class="hero compact">
        <div class="hero-grid"></div>
        <div class="hero-glow"></div>

        <div class="hero-text">
          <div class="hero-greet">{{ greeting }}, {{ auth.user?.real_name || auth.user?.username }} 👋</div>
          <div class="hero-sub">
            <span class="sub-line">智安平台</span>
            <el-tag size="small" :type="roleTag" effect="dark" class="role-badge">
              {{ auth.user?.role_label }}
            </el-tag>
          </div>
          <div class="hero-meta">
            <span class="meta-pill"><el-icon><Calendar /></el-icon> {{ today }}</span>
            <span class="meta-pill"><el-icon><Setting /></el-icon> 已开通技能 <strong>{{ skillCount }}</strong> 项</span>
          </div>
        </div>

        <div class="hero-art">
          <div class="art-circle a"></div>
          <div class="art-circle b"></div>
          <div class="art-ring"></div>
          <el-icon :size="64" color="rgba(255,255,255,.12)"><TrendCharts /></el-icon>
        </div>
      </div>

      <!-- KPI 卡片 -->
      <div class="card-row" style="margin-top: 16px;">
        <div v-for="item in kpiList" :key="item.title" class="kpi-card hoverable"
             :style="{ '--accent': item.color }">
          <div class="kpi-icon">
            <el-icon :size="18"><component :is="item.icon" /></el-icon>
          </div>
          <div class="kpi-text">
            <div class="muted">{{ item.title }}</div>
            <div class="kpi-value">{{ item.value }}</div>
          </div>
        </div>
      </div>

      <!-- 图表区 -->
      <el-row :gutter="14" style="margin-top: 16px;">
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="hoverable chart-card">
            <template #header>风险等级分布</template>
            <v-chart :option="sevOption" autoresize style="height: 100%;" />
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="hoverable chart-card">
            <template #header>近 30 天隐患趋势</template>
            <v-chart :option="trendOption" autoresize style="height: 100%;" />
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="hoverable chart-card">
            <template #header>隐患类别 Top 10</template>
            <v-chart :option="catOption" autoresize style="height: 100%;" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 数据区 -->
      <el-row :gutter="14" style="margin-top: 16px;">
        <el-col :xs="24" :sm="24" :md="15">
          <el-card class="hoverable data-card">
            <template #header>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="section-title" style="margin:0;">最近 5 次隐患识别</span>
                <el-button type="primary" link @click="$router.push('/hazards/history')">查看全部 →</el-button>
              </div>
            </template>
            <el-table :data="recentDetections" stripe size="small" empty-text="暂无识别记录"
                      max-height="180"
                      @row-click="(row: HazardDetection) => $router.push(`/hazards/history?id=${row.id}`)">
              <el-table-column prop="created_at" label="时间" width="155" />
              <el-table-column prop="lab_name" label="地点" min-width="100" show-overflow-tooltip />
              <el-table-column label="隐患数" width="70" align="center">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain">{{ row.hazard_count }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="风险" width="60" align="center">
                <template #default="{ row }">
                  <el-tag :type="severityTag(row.overall_severity)" effect="plain" size="small">
                    {{ severityLabel(row.overall_severity) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="summary" label="评估" min-width="140" show-overflow-tooltip />
            </el-table>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="24" :md="9">
          <el-card class="hoverable data-card">
            <template #header>隐患高发地点 TOP 5</template>
            <div v-if="!topLabs.length" class="muted" style="padding: 16px 0; text-align:center;">暂无数据</div>
            <div v-else class="top-lab-list">
              <div v-for="(lab, idx) in topLabs" :key="lab.lab_name" class="top-lab-item"
                   @click="$router.push('/hazards/history')">
                <span class="top-rank" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span>
                <span class="top-name">{{ lab.lab_name }}</span>
                <span class="top-count">{{ lab.hazards }} 项隐患</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- ========== 普通用户首页 ========== -->
    <template v-else>
      <!-- Hero -->
      <div class="hero compact">
        <div class="hero-grid"></div>
        <div class="hero-glow"></div>

        <div class="hero-text">
          <div class="hero-greet">{{ greeting }}, {{ auth.user?.real_name || auth.user?.username }} 👋</div>
          <div class="hero-sub">
            <span class="sub-line">智安平台</span>
            <el-tag size="small" :type="roleTag" effect="dark" class="role-badge">
              {{ auth.user?.role_label }}
            </el-tag>
          </div>
          <div class="hero-meta">
            <span class="meta-pill"><el-icon><Calendar /></el-icon> {{ today }}</span>
            <span class="meta-pill"><el-icon><Setting /></el-icon> 已开通技能 <strong>{{ skillCount }}</strong> 项</span>
          </div>
        </div>

        <div class="hero-art">
          <div class="art-circle a"></div>
          <div class="art-circle b"></div>
          <div class="art-ring"></div>
          <el-icon :size="64" color="rgba(255,255,255,.12)"><TrendCharts /></el-icon>
        </div>
      </div>

      <!-- Recent detections -->
      <el-card style="margin-top: 18px;" class="hoverable">
        <template #header>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="section-title" style="margin:0;">最近 5 次隐患识别</span>
            <el-button type="primary" link @click="$router.push('/hazards/history')">查看全部 →</el-button>
          </div>
        </template>
        <el-table :data="recent" stripe size="small" empty-text="暂无识别记录">
          <el-table-column prop="created_at" label="时间" width="170" />
          <el-table-column prop="lab_name" label="地点" />
          <el-table-column label="隐患数" width="90">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.hazard_count }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="风险" width="80">
            <template #default="{ row }">
              <el-tag :type="severityTag(row.overall_severity)" effect="plain">
                {{ severityLabel(row.overall_severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="评估" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useAuthStore } from '@/stores/auth'
import { hazardApi } from '@/api/hazards'
import { analyticsApi } from '@/api/analytics'
import type { HazardDetection } from '@/types'
import { severityTag, severityLabel, severityColor } from '@/utils/severity'

use([CanvasRenderer, PieChart, LineChart, BarChart, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const recent = ref<HazardDetection[]>([])

// Admin 大屏数据
const dash = ref<any>(null)

const skillCount = computed(() => auth.user?.skills?.length || 0)

const roleTag = computed(() => {
  if (auth.role === 'admin') return 'danger'
  if (auth.role === 'safety_officer') return 'warning'
  return 'info'
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const today = computed(() => {
  const d = new Date()
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 星期${week}`
})

// Admin KPI
const kpiList = computed(() => {
  const o = dash.value?.overview || {}
  return [
    { title: '用户总数', value: o.users?.total || 0, icon: 'User', color: '#3b82f6' },
    { title: '知识库文档', value: o.knowledge_docs || 0, icon: 'Collection', color: '#10b981' },
    { title: '问答记录', value: o.qa_sessions || 0, icon: 'ChatLineSquare', color: '#8b5cf6' },
    { title: '隐患识别', value: o.detections || 0, icon: 'Picture', color: '#ef4444' },
    { title: '报告', value: o.reports || 0, icon: 'Document', color: '#f59e0b' },
    { title: '技能数', value: auth.user?.skills?.length || 0, icon: 'MagicStick', color: '#14b8a6' },
  ]
})

const recentDetections = computed(() => {
  const trend = dash.value?.detection_trend || []
  // 从 dashboard 接口没有直接给最近识别记录，这里复用普通用户加载的 recent
  return recent.value.slice(0, 5)
})

const topLabs = computed(() => dash.value?.top_labs || [])

// 图表配置
const sevOption = computed(() => {
  const sev = dash.value?.severity_distribution || {}
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['45%', '68%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { name: '高', value: sev.high || 0, itemStyle: { color: severityColor('high') } },
        { name: '中', value: sev.medium || 0, itemStyle: { color: severityColor('medium') } },
        { name: '低', value: sev.low || 0, itemStyle: { color: severityColor('low') } },
      ],
    }],
  }
})

const trendOption = computed(() => {
  const trend = dash.value?.detection_trend || []
  const data = trend.map((p: any) => p.count)
  const dates = trend.map((p: any) => p.date.slice(5)) // '05-01'
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 15, left: 36, right: 14, bottom: 24 },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: '#e5e8ef' } }, axisLabel: { color: '#8b94a3', fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f2f5' } }, axisLabel: { color: '#8b94a3', fontSize: 10 } },
    series: [{
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 3, color: '#ff7a1a' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255,122,26,0.25)' },
            { offset: 1, color: 'rgba(255,122,26,0.02)' },
          ],
        },
      },
      data,
    }],
  }
})

const catOption = computed(() => {
  const cats = dash.value?.category_distribution || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 8, left: 76, right: 14, bottom: 14 },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f2f5' } }, axisLabel: { color: '#8b94a3', fontSize: 10 } },
    yAxis: {
      type: 'category',
      data: cats.map((c: any) => c.category).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#4b5563', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      data: cats.map((c: any) => c.count).reverse(),
      barWidth: 16,
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#3b82f6' },
    }],
  }
})

onMounted(async () => {
  // 普通用户也需要的识别记录
  if (auth.hasSkill('hazard_detect')) {
    try {
      const r = await hazardApi.list({ page: 1 })
      recent.value = (r.results || []).slice(0, 5)
    } catch (e: any) {
      if (e.response?.status !== 401) {
        console.error('Failed to load recent hazards', e)
      }
    }
  }

  // Admin 大屏额外加载 dashboard 数据
  if (auth.isAdmin) {
    loading.value = true
    try {
      dash.value = await analyticsApi.dashboard()
    } catch {
      dash.value = null
    } finally {
      loading.value = false
    }
  }
})
</script>

<style scoped>
/* ===== Hero ===== */
.hero {
  position: relative;
  background: var(--grad-hero);
  border-radius: 14px;
  padding: 26px 28px;
  color: #fff;
  overflow: hidden;
  display: flex;
  align-items: center;
  box-shadow: 0 10px 26px rgba(31, 44, 77, .25);
}
.hero.compact { padding: 16px 24px; }

/* 网格背景 */
.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
  z-index: 0;
}

/* 底部发光条 */
.hero-glow {
  position: absolute;
  left: 0; right: 0; bottom: 0; height: 2px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255,122,26,.6) 20%,
    rgba(255,140,0,.8) 50%,
    rgba(214,40,40,.6) 80%,
    transparent 100%
  );
  z-index: 2;
}

.hero-text { flex: 1; z-index: 1; }
.hero-greet { font-size: 22px; font-weight: 700; margin-bottom: 6px; letter-spacing: .5px; }
.hero.compact .hero-greet { font-size: 20px; margin-bottom: 6px; }

.hero-sub {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  opacity: .9;
}
.hero.compact .hero-sub { font-size: 13px; }
.sub-line {
  position: relative;
  padding-left: 14px;
  color: rgba(255,255,255,.85);
}
.sub-line::before {
  content: '';
  position: absolute;
  left: 0; top: 50%; transform: translateY(-50%);
  width: 4px; height: 14px;
  background: linear-gradient(180deg, #ff7a1a, #d62828);
  border-radius: 2px;
}
.role-badge {
  --el-tag-bg-color: rgba(255,255,255,.12) !important;
  --el-tag-border-color: rgba(255,255,255,.2) !important;
  --el-tag-text-color: #ffd166 !important;
}

.hero-meta {
  display: flex; gap: 14px; margin-top: 14px;
}
.hero.compact .hero-meta { margin-top: 12px; }
.meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.1);
  font-size: 12px;
  color: rgba(255,255,255,.85);
  backdrop-filter: blur(4px);
}
.meta-pill strong {
  color: #ffd166;
  font-weight: 700;
}

.hero-art {
  position: relative;
  width: 160px; height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero.compact .hero-art { width: 130px; height: 90px; }
.art-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,.06);
}
.art-circle.a { width: 140px; height: 140px; right: -30px; top: -20px; }
.art-circle.b { width: 80px; height: 80px; right: 60px; bottom: -20px; background: rgba(255, 140, 0, .2); }
.art-ring {
  position: absolute;
  width: 90px; height: 90px;
  border-radius: 50%;
  border: 1px dashed rgba(255,255,255,.12);
  animation: rotate 20s linear infinite;
}
@keyframes rotate {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.dashboard-page {
  padding: 14px 18px;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.dashboard-page::-webkit-scrollbar { display: none; }

/* ===== KPI Cards ===== */
.kpi-card {
  background: #fff;
  border-radius: var(--radius-card);
  padding: 14px;
  display: flex;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  transition: transform .2s ease, box-shadow .2s ease;
}
.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}
.kpi-card::after {
  content: '';
  position: absolute;
  inset: auto 0 0 0;
  height: 3px;
  background: var(--accent);
  opacity: .7;
}
.kpi-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  background: var(--accent);
  box-shadow: 0 6px 14px color-mix(in srgb, var(--accent) 35%, transparent);
}
.kpi-text { flex: 1; min-width: 0; }
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--txt-primary);
  margin-top: 2px;
  line-height: 1.1;
  letter-spacing: .5px;
}

/* ===== Chart / Data cards ===== */
.chart-card {
  height: 320px;
  display: flex;
  flex-direction: column;
}
.chart-card :deep(.el-card__header) {
  padding: 10px 16px !important;
  font-size: 13px;
  flex-shrink: 0;
}
.chart-card :deep(.el-card__body) {
  padding: 8px !important;
  flex: 1;
  min-height: 0;
}
.data-card :deep(.el-card__body) {
  padding: 10px 16px !important;
}

/* ===== Top labs list ===== */
.top-lab-list { padding: 0; }
.top-lab-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--line-soft);
  cursor: pointer;
  transition: background .15s ease;
}
.top-lab-item:last-child { border-bottom: none; }
.top-lab-item:hover { background: #f7f9fc; margin: 0 -16px; padding-left: 16px; padding-right: 16px; }
.top-rank {
  width: 24px; height: 24px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff;
  background: #c0c4cc;
  flex-shrink: 0;
}
.top-rank.rank-1 { background: linear-gradient(135deg, #ff7a1a, #d62828); }
.top-rank.rank-2 { background: linear-gradient(135deg, #f59e0b, #f97316); }
.top-rank.rank-3 { background: linear-gradient(135deg, #3b82f6, #1e40af); }
.top-name { flex: 1; font-weight: 500; color: var(--txt-primary); font-size: 14px; }
.top-count { color: var(--txt-muted); font-size: 12px; }
</style>
