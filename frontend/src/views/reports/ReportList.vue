<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="section-title" style="margin:0;">报告列表</span>
          <div class="header-actions">
            <el-input v-model="search" placeholder="标题 / 地点" clearable
                      style="width: 200px;" @keyup.enter="reload">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="labFilter" placeholder="地点筛选" clearable filterable style="width: 180px;">
              <el-option v-for="l in labOptions" :key="l.id" :label="l.name" :value="l.id" />
              <el-option label="其他地点" :value="-1" />
            </el-select>
            <el-button @click="reload">
              <el-icon style="margin-right:4px;"><Refresh /></el-icon>查询
            </el-button>
            <el-button type="primary" @click="$router.push('/reports/new')">
              <el-icon style="margin-right:4px;"><Document /></el-icon>生成报告
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" stripe class="report-table"
                @row-click="(row: ReportSummary) => $router.push(`/reports/${row.id}`)"
                empty-text="暂无数据">
        <el-table-column type="index" width="56" align="center" />
        <el-table-column label="标题" min-width="180">
          <template #default="{ row }">
            <div class="title-cell">
              <span class="title-bar" :style="{ background: bulletColor(row.overall_severity) }" />
              <span class="title-text">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="地点" min-width="110">
          <template #default="{ row }">
            <el-tag v-if="row.lab_name" size="small" effect="plain">{{ row.lab_name }}</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="inspector" label="检查人" min-width="100" />
        <el-table-column label="风险" min-width="80">
          <template #default="{ row }">
            <el-tag :type="severityTag(row.overall_severity)">{{ severityLabel(row.overall_severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="隐患数" min-width="80" align="center">
          <template #default="{ row }">{{ row.summary_stats?.total || 0 }}</template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建人" min-width="100" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" min-width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="查看" placement="top">
              <el-button text circle type="primary" @click.stop="$router.push(`/reports/${row.id}`)">
                <el-icon><View /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="PDF" placement="top">
              <el-button text circle @click.stop="downloadPdf(row)" :disabled="!row.pdf_file">
                <el-icon><Document /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="Word" placement="top">
              <el-button text circle @click.stop="downloadDocx(row)" :disabled="!row.docx_file">
                <el-icon><DocumentCopy /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="趋势" placement="top">
              <el-button text circle @click.stop="$router.push(`/reports/trend/${encodeURIComponent(row.lab_name)}`)">
                <el-icon><TrendCharts /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button text circle type="danger" @click.stop="remove(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination layout="total, prev, pager, next" :total="total" :page-size="20"
                     @current-change="onPage" style="margin-top: 14px; justify-content: flex-end;" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { reportApi } from '@/api/reports'
import { labApi } from '@/api/labs'
import type { ReportSummary, Lab } from '@/types'
import { severityTag, severityLabel, severityColor } from '@/utils/severity'

const route = useRoute()
const rows = ref<ReportSummary[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const labFilter = ref<number | ''>('')
const labOptions = ref<Lab[]>([])

function bulletColor(s: string) {
  return severityColor(s as any) || '#909399'
}

async function reload() {
  const params: any = {
    page: page.value, search: search.value || undefined,
  }
  if (labFilter.value !== '' && labFilter.value !== -1) {
    params.lab = labFilter.value
  } else if (labFilter.value === -1) {
    params.other_location__isnull = 'False'
  }
  const r = await reportApi.list(params)
  rows.value = r.results || []
  total.value = r.count || 0
}
function onPage(p: number) { page.value = p; reload() }

async function loadLabOptions() {
  try {
    const r = await labApi.list({ page_size: 999 })
    labOptions.value = r.results || []
  } catch {
    labOptions.value = []
  }
}

async function remove(row: ReportSummary) {
  await ElMessageBox.confirm(`确定删除「${row.title}」?`, '确认', { type: 'warning' })
  await reportApi.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

function downloadPdf(row: ReportSummary) {
  const token = localStorage.getItem('access_token')
  fetch(`/api/reports/${row.id}/download/pdf/`, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob()).then(blob => save(blob, `${row.title}.pdf`))
}
function downloadDocx(row: ReportSummary) {
  const token = localStorage.getItem('access_token')
  fetch(`/api/reports/${row.id}/download/docx/`, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => r.blob()).then(blob => save(blob, `${row.title}.docx`))
}
function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = name; a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  reload(); loadLabOptions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
}
.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.report-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background .15s ease;
}
.report-table :deep(.el-table__row:hover) { background: #f5efe6 !important; }

.title-cell { display: flex; align-items: center; gap: 10px; }
.title-bar {
  width: 3px;
  height: 18px;
  border-radius: 2px;
  flex-shrink: 0;
}
.title-text { font-weight: 600; color: var(--txt-primary); }
</style>
