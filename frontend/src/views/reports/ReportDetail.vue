<template>
  <div class="page" v-loading="loading">
    <div v-if="report">
      <el-page-header @back="$router.back()" :content="report.title" style="margin-bottom: 14px;" />

      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="section-title" style="margin:0;">基本信息</span>
            <el-tag :type="severityTag(report.overall_severity)" style="margin-left:8px;">
              总体风险:{{ severityLabel(report.overall_severity) }}
            </el-tag>
            <div style="margin-left:auto; display:flex; gap:8px;">
              <el-button @click="downloadPdf" :disabled="!report.pdf_file" type="primary">下载 PDF</el-button>
              <el-button @click="downloadDocx" :disabled="!report.docx_file">下载 Word</el-button>
              <el-button @click="regenerate" :loading="regen">重新渲染</el-button>
            </div>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="地点">{{ report.lab_name }}</el-descriptions-item>
          <el-descriptions-item label="检查人">{{ report.inspector || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ report.creator_name }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ report.created_at }}</el-descriptions-item>
          <el-descriptions-item label="包含记录">{{ report.detection_count }} 条</el-descriptions-item>
          <el-descriptions-item label="备注">{{ report.extra_notes || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card style="margin-top: 14px;">
        <template #header><span class="section-title" style="margin:0;">汇总统计</span></template>
        <el-row :gutter="14">
          <el-col :span="14"><div ref="sevChart" style="height:240px;"></div></el-col>
          <el-col :span="10"><div ref="catChart" style="height:240px;"></div></el-col>
        </el-row>
      </el-card>

      <el-card style="margin-top: 14px;">
        <template #header><span class="section-title" style="margin:0;">隐患明细与媒体快照</span></template>
        <div v-for="(d, i) in report.detections" :key="d.id" class="det-block">
          <h4>{{ i+1 }}. {{ d.lab_name || '现场记录' }} <span class="muted">({{ d.created_at }})</span></h4>
          <video v-if="d.media_type === 'video'" :src="d.original_image || undefined"
                 :poster="d.cover_image || undefined" controls class="det-video" />
          <img v-else :src="d.annotated_image || d.original_image" />
          <div class="det-summary"><b>评估:</b><MarkdownText :text="d.summary" /></div>
          <el-table :data="d.hazards" size="small" border>
            <el-table-column type="index" width="50" />
            <el-table-column prop="name" label="隐患" width="160" />
            <el-table-column prop="category" label="类别" width="100" />
            <el-table-column label="风险" width="80">
              <template #default="{ row }">
                <el-tag :type="severityTag(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="描述">
              <template #default="{ row }">
                <MarkdownText :text="row.description" inline />
              </template>
            </el-table-column>
            <el-table-column label="建议">
              <template #default="{ row }">
                <MarkdownText :text="row.suggestion" inline />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <el-card style="margin-top: 14px;" v-if="report.references.length">
        <template #header><span class="section-title" style="margin:0;">参考依据</span></template>
        <ul>
          <li v-for="(r, i) in report.references" :key="i">
            <b>{{ r.title }}</b> — {{ r.snippet }}
          </li>
        </ul>
      </el-card>

      <el-card style="margin-top: 14px;">
        <template #header><span class="section-title" style="margin:0;">AI 评价与整改建议</span></template>
        <MarkdownText class="rd-eval" :text="report.agent_evaluation" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { reportApi } from '@/api/reports'
import type { ReportDetail } from '@/types'
import { severityTag, severityLabel, severityColor } from '@/utils/severity'
import MarkdownText from '@/components/MarkdownText.vue'

const route = useRoute()
const report = ref<ReportDetail | null>(null)
const loading = ref(false)
const regen = ref(false)
const sevChart = ref<HTMLElement>()
const catChart = ref<HTMLElement>()

async function load() {
  loading.value = true
  try {
    report.value = await reportApi.retrieve(Number(route.params.id))
    await nextTick()
    drawCharts()
  } finally {
    loading.value = false
  }
}

function drawCharts() {
  if (!report.value) return
  const stats = report.value.summary_stats || { by_severity: {}, by_category: {} } as any
  const sev = stats.by_severity || {}
  if (sevChart.value) {
    echarts.init(sevChart.value).setOption({
      title: { text: '严重等级分布', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: {},
      series: [{
        type: 'pie', radius: ['40%', '70%'], label: { formatter: '{b}: {c}' },
        data: [
          { name: '高', value: sev.high || 0, itemStyle: { color: severityColor('high') } },
          { name: '中', value: sev.medium || 0, itemStyle: { color: severityColor('medium') } },
          { name: '低', value: sev.low || 0, itemStyle: { color: severityColor('low') } },
        ],
      }],
    })
  }
  const cats = Object.entries(stats.by_category || {})
  if (catChart.value) {
    echarts.init(catChart.value).setOption({
      title: { text: '类别分布', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: {}, grid: { top: 40, left: 30, right: 10, bottom: 30 },
      xAxis: { type: 'category', data: cats.map(([k]) => k) },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: cats.map(([, v]) => v), itemStyle: { color: '#409eff' } }],
    })
  }
}

function downloadPdf() {
  if (!report.value) return
  const token = localStorage.getItem('access_token')
  fetch(`/api/reports/${report.value.id}/download/pdf/`, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob()).then(blob => save(blob, `${report.value!.title}.pdf`))
}
function downloadDocx() {
  if (!report.value) return
  const token = localStorage.getItem('access_token')
  fetch(`/api/reports/${report.value.id}/download/docx/`, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob()).then(blob => save(blob, `${report.value!.title}.docx`))
}
function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = name; a.click()
  URL.revokeObjectURL(url)
}

async function regenerate() {
  if (!report.value) return
  regen.value = true
  try {
    await reportApi.regenerate(report.value.id)
    ElMessage.success('已重新渲染 PDF / DOCX')
    await load()
  } finally {
    regen.value = false
  }
}

watch(() => route.params.id, () => { if (route.params.id) load() })
onMounted(load)
</script>

<style scoped>
.det-block {
  padding: 14px 0;
  border-bottom: 1px dashed #ebeef5;
}
.det-block:last-child { border-bottom: none; }
.det-block img {
  max-width: 100%; max-height: 480px;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  box-shadow: 0 6px 20px rgba(15, 23, 42, .08);
  margin: 8px 0;
}
.det-video {
  display: block;
  max-width: 100%;
  max-height: 480px;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  background: #0f172a;
  margin: 8px 0;
}
.det-block h4 {
  margin: 6px 0 10px;
  font-size: 15px;
  color: var(--txt-primary);
  font-weight: 600;
}
.det-block h4 .muted { font-weight: normal; }
.det-summary { margin: 8px 0; line-height: 1.7; }
.rd-eval { line-height: 1.8; }
ul { padding-left: 20px; line-height: 2; }
ul li b { color: var(--txt-primary); }
</style>
