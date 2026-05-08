<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="section-title" style="margin:0;">识别历史</span>
          </div>
          <div class="header-actions">
            <el-select v-model="labFilter" placeholder="地点筛选" clearable filterable style="width: 180px;">
              <el-option v-for="l in labOptions" :key="l.id" :label="l.name" :value="l.id" />
              <el-option label="其他地点" :value="-1" />
            </el-select>
            <el-select v-model="severity" placeholder="风险等级" clearable style="width: 130px;">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
            </el-select>
            <el-input v-model="search" placeholder="评估关键词" clearable
                      style="width: 200px;" @keyup.enter="reload">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="reload">
              <el-icon style="margin-right:4px;"><Refresh /></el-icon>查询
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" stripe class="hist-table" @row-click="open" empty-text="暂无数据">
        <el-table-column type="index" width="56" align="center" />
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <div class="thumb">
              <img :src="row.media_type === 'video' ? row.cover_image : (row.annotated_image || row.original_image)" />
              <div v-if="row.media_type === 'video'" class="thumb-play">
                <el-icon><VideoPlay /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column label="地点" width="160">
          <template #default="{ row }">
            <el-tag v-if="row.lab_name" size="small" effect="plain">{{ row.lab_name }}</el-tag>
            <span v-else class="muted">未填写</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="提交人" width="100" />
        <el-table-column label="隐患数" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.hazard_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="severityTag(row.overall_severity)">{{ severityLabel(row.overall_severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="评估" show-overflow-tooltip />
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
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

    <el-drawer v-model="drawer" :title="current?.lab_name || '识别详情'" size="60%">
      <div v-if="current" class="drawer-body">
        <img :src="current.media_type === 'video' ? current.cover_image : (current.annotated_image || current.original_image)" class="detail-img" />
        <div class="detail-summary">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap;">
            <b>地点:</b>
            <LabSelect v-model:lab-id="editLabId" v-model:other-location="editOtherLocation" style="width: 260px;" />
            <el-button type="primary" size="small" @click="saveDrawerLab">保存</el-button>
          </div>
          <p style="line-height:1.7; margin: 0 0 10px;"><b>整体评估:</b>{{ current.summary }}</p>
          <el-tag :type="severityTag(current.overall_severity)" effect="dark" size="large">
            总体风险:{{ severityLabel(current.overall_severity) }}
          </el-tag>
        </div>
        <el-divider content-position="left">隐患明细</el-divider>
        <el-empty v-if="!current.hazards.length" description="未识别到明显隐患" />
        <el-collapse v-else>
          <el-collapse-item v-for="(h, idx) in current.hazards" :key="idx" :name="idx">
            <template #title>
              <span style="font-weight:600;">{{ idx+1 }}. {{ h.name }}</span>
              <el-tag size="small" effect="plain" style="margin-left:8px;">{{ h.category }}</el-tag>
              <el-tag size="small" :type="severityTag(h.severity)" style="margin-left:6px;">
                {{ severityLabel(h.severity) }}
              </el-tag>
            </template>
            <p><b>描述:</b>{{ h.description }}</p>
            <p><b>建议:</b>{{ h.suggestion }}</p>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { hazardApi } from '@/api/hazards'
import { labApi } from '@/api/labs'
import type { HazardDetection, Lab } from '@/types'
import { severityTag, severityLabel } from '@/utils/severity'
import LabSelect from '@/components/LabSelect.vue'

const rows = ref<HazardDetection[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const severity = ref('')
const labFilter = ref<number | ''>('')
const labOptions = ref<Lab[]>([])
const drawer = ref(false)
const current = ref<HazardDetection | null>(null)
const editLabId = ref<number | null>(null)
const editOtherLocation = ref('')

async function saveDrawerLab() {
  if (!current.value) return
  try {
    const updated = await hazardApi.updateLocation(current.value.id, {
      lab_id: editLabId.value,
      other_location: editOtherLocation.value,
    })
    current.value.lab_name = updated.lab_name
    const row = rows.value.find(r => r.id === current.value!.id)
    if (row) row.lab_name = updated.lab_name
    ElMessage.success('地点已更新')
    loadLabOptions()
  } catch {
    ElMessage.error('更新失败')
  }
}

async function reload() {
  const params: any = {
    page: page.value, search: search.value || undefined,
    overall_severity: severity.value || undefined,
  }
  if (labFilter.value !== '' && labFilter.value !== -1) {
    params.lab = labFilter.value
  } else if (labFilter.value === -1) {
    params.other_location__isnull = 'False'
  }
  const r = await hazardApi.list(params)
  rows.value = r.results || []
  total.value = r.count || 0
}

async function loadLabOptions() {
  try {
    const r = await labApi.list({ page_size: 999 })
    labOptions.value = r.results || []
  } catch {
    labOptions.value = []
  }
}

function onPage(p: number) { page.value = p; reload() }

function open(row: HazardDetection) {
  current.value = row
  editLabId.value = (row as any).lab ?? null
  editOtherLocation.value = (row as any).other_location ?? ''
  drawer.value = true
}

async function remove(row: HazardDetection) {
  await ElMessageBox.confirm(`确定删除该识别记录?`, '确认', { type: 'warning' })
  await hazardApi.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

onMounted(() => {
  loadLabOptions()
  reload()
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
.hist-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background .15s ease;
}
.hist-table :deep(.el-table__row:hover) { background: #f5efe6 !important; }

.thumb {
  width: 70px; height: 52px;
  border-radius: 6px;
  overflow: hidden;
  background: #f3f5fa;
  border: 1px solid var(--line-soft);
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb-play {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.25);
  color: #fff;
  font-size: 20px;
  pointer-events: none;
}
.thumb { position: relative; }

.drawer-body { padding: 6px 18px 18px; }
.detail-img {
  max-width: 100%;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  box-shadow: 0 6px 20px rgba(15, 23, 42, .08);
}
.detail-summary {
  margin: 14px 0;
  padding: 14px 16px;
  background: linear-gradient(180deg, #fafbfc 0%, #f3f5fa 100%);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
}
</style>
