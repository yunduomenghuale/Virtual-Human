<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="section-title" style="margin:0;">实验室管理</span>
          <div class="header-actions">
            <el-input v-model="search" placeholder="搜索名称" clearable
                      style="width: 200px;" @keyup.enter="reload">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button @click="reload">
              <el-icon style="margin-right:4px;"><Refresh /></el-icon>查询
            </el-button>
            <el-button type="primary" @click="openDialog()">
              <el-icon style="margin-right:4px;"><Plus /></el-icon>新增实验室
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" stripe class="lab-table" empty-text="暂无数据">
        <el-table-column type="index" width="56" align="center" />
        <el-table-column label="名称" min-width="140">
          <template #default="{ row }">
            <div class="lab-name-cell">
              <span class="lab-bar" />
              <span class="lab-name-text">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" min-width="120">
          <template #default="{ row }">
            <div v-if="row.manager_name" class="manager-tag">
              <el-avatar :size="22" :style="{ background: avatarBg(row.manager_name), color: '#fff', fontSize: '11px', marginRight: '6px' }">
                {{ row.manager_name.charAt(0) }}
              </el-avatar>
              <span>{{ row.manager_name }}</span>
            </div>
            <span v-else class="muted">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" min-width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="编辑" placement="top">
              <el-button text circle type="primary" @click="openDialog(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button text circle type="danger" @click="remove(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination layout="total, prev, pager, next" :total="total" :page-size="20"
                     @current-change="onPage" style="margin-top: 14px; justify-content: flex-end;" />
    </el-card>

    <el-dialog v-model="dialog" :title="form.id ? '编辑实验室' : '新增实验室'" width="420px" class="lab-dialog">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入实验室名称" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="form.manager" clearable placeholder="请选择负责人" style="width: 100%;">
            <el-option v-for="u in users" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { labApi } from '@/api/labs'
import { userApi } from '@/api/auth'
import type { Lab } from '@/types'

const rows = ref<Lab[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const dialog = ref(false)
const users = ref<any[]>([])

const form = reactive({
  id: 0,
  name: '',
  manager: null as number | null,
})

const avatarColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
function avatarBg(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return avatarColors[Math.abs(hash) % avatarColors.length]
}

async function reload() {
  const r = await labApi.list({
    page: page.value, search: search.value || undefined,
  })
  rows.value = r.results || []
  total.value = r.count || 0
}

function onPage(p: number) { page.value = p; reload() }

async function loadUsers() {
  try {
    const r = await userApi.list({ page_size: 999 })
    users.value = r.results || []
  } catch {
    users.value = []
  }
}

function openDialog(row?: Lab) {
  if (row) {
    Object.assign(form, { id: row.id, name: row.name, manager: row.manager })
  } else {
    Object.assign(form, { id: 0, name: '', manager: null })
  }
  dialog.value = true
}

async function submit() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写实验室名称')
    return
  }
  const payload = { name: form.name.trim(), manager: form.manager }
  if (form.id) {
    await labApi.update(form.id, payload)
  } else {
    await labApi.create(payload)
  }
  ElMessage.success('已保存')
  dialog.value = false
  reload()
}

async function remove(row: Lab) {
  await ElMessageBox.confirm(`确定删除「${row.name}」?`, '确认', { type: 'warning' })
  await labApi.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

onMounted(() => {
  reload()
  loadUsers()
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

.metric-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 16px 20px;
  display: flex;
  gap: 14px;
  align-items: center;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  transition: transform .2s ease, box-shadow .2s ease;
  min-width: 200px;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}
.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--grad-brand);
}
.metric-text { flex: 1; min-width: 0; }
.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--txt-primary);
  margin-top: 2px;
  line-height: 1.1;
  letter-spacing: .5px;
}

.lab-table :deep(.el-table__row) { transition: background .15s ease; }
.lab-table :deep(.el-table__row:hover) { background: #f5efe6 !important; }
.lab-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.lab-bar {
  width: 3px;
  height: 18px;
  border-radius: 2px;
  background: var(--grad-brand);
  flex-shrink: 0;
}
.lab-name-text {
  font-weight: 600;
  color: var(--txt-primary);
}
.manager-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px 2px 4px;
  background: #f3f5fa;
  border-radius: 999px;
  font-size: 13px;
  color: var(--txt-secondary);
}

:deep(.lab-dialog .el-dialog__body) { padding: 20px 24px 10px; }
</style>
