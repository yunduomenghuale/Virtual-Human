<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="section-title" style="margin:0;">用户管理</span>
          <div class="header-actions">
            <el-input v-model="search" placeholder="用户名 / 地点" clearable
                      style="width: 200px;" @keyup.enter="reload">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="role" placeholder="角色" clearable style="width: 140px;">
              <el-option label="系统管理员" value="admin" />
              <el-option label="实验室安全员" value="safety_officer" />
              <el-option label="实验人员" value="experimenter" />
            </el-select>
            <el-button @click="reload">
              <el-icon style="margin-right:4px;"><Refresh /></el-icon>查询
            </el-button>
            <el-button type="primary" @click="openDialog()">
              <el-icon style="margin-right:4px;"><Plus /></el-icon>新增用户
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" stripe class="user-table" empty-text="暂无数据">
        <el-table-column type="index" width="56" align="center" />
        <el-table-column label="账号" min-width="160">
          <template #default="{ row }">
            <div class="user-cell">
              <span class="avatar" :style="{ background: roleGradient(row.role) }">
                {{ initial(row) }}
              </span>
              <div class="user-info">
                <div class="username">{{ row.username }}</div>
                <div class="muted real-name">{{ row.real_name || '—' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="地点" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.lab_name" size="small" effect="plain">{{ row.lab_name }}</el-tag>
            <span v-else class="muted">未填写</span>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="150">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : (row.role === 'safety_officer' ? 'warning' : 'info')" effect="light">
              {{ row.role_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" effect="light" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="加入时间" width="170" />
        <el-table-column label="操作" min-width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="编辑" placement="top">
              <el-button text circle type="primary" @click="openDialog(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="重置密码" placement="top">
              <el-button text circle @click="resetPwd(row)">
                <el-icon><Key /></el-icon>
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

    <el-dialog v-model="dialog" :title="form.id ? '编辑用户' : '新增用户'" width="460px" class="user-dialog">
      <el-form :model="form" label-width="90px">
        <el-form-item label="账号"><el-input v-model="form.username" :disabled="!!form.id" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" /></el-form-item>
        <el-form-item label="地点">
          <LabSelect v-model:lab-id="form.lab_id" v-model:other-location="form.other_location" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%;">
            <el-option label="系统管理员" value="admin" />
            <el-option label="实验室安全员" value="safety_officer" />
            <el-option label="实验人员" value="experimenter" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
        <el-form-item v-if="!form.id" label="初始密码"><el-input v-model="form.password" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api/auth'
import LabSelect from '@/components/LabSelect.vue'

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const role = ref('')
const dialog = ref(false)

const form = reactive({
  id: 0,
  username: '',
  real_name: '',
  lab_id: null as number | null,
  other_location: '',
  role: 'experimenter',
  is_active: true,
  password: '',
})

const countByRole = computed(() => {
  const counter = { admin: 0, safety_officer: 0, experimenter: 0 } as Record<string, number>
  for (const r of rows.value) counter[r.role] = (counter[r.role] || 0) + 1
  return counter
})

function roleGradient(r: string) {
  if (r === 'admin') return 'linear-gradient(135deg, #d62828 0%, #ff7a1a 100%)'
  if (r === 'safety_officer') return 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)'
  return 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
}
function initial(row: any) {
  const s = (row.real_name || row.username || '?').trim()
  return s.charAt(0).toUpperCase()
}

async function reload() {
  const r = await userApi.list({
    page: page.value, search: search.value || undefined, role: role.value || undefined,
  })
  rows.value = r.results || []
  total.value = r.count || 0
}

function onPage(p: number) { page.value = p; reload() }

function openDialog(row?: any) {
  if (row) {
    Object.assign(form, { ...row, password: '' })
  } else {
    Object.assign(form, { id: 0, username: '', real_name: '', lab_id: null, other_location: '',
                          role: 'experimenter', is_active: true, password: 'changeme' })
  }
  dialog.value = true
}

async function submit() {
  if (form.id) {
    await userApi.update(form.id, {
      real_name: form.real_name,
      lab: form.lab_id,
      other_location: form.other_location,
      role: form.role,
      is_active: form.is_active,
    })
  } else {
    await userApi.create(form)
  }
  ElMessage.success('已保存')
  dialog.value = false
  reload()
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除「${row.username}」?`, '确认', { type: 'warning' })
  await userApi.remove(row.id)
  ElMessage.success('已删除')
  reload()
}

async function resetPwd(row: any) {
  const { value } = await ElMessageBox.prompt('输入新密码', '重置密码', {
    inputPattern: /.{6,}/, inputErrorMessage: '至少 6 位',
  })
  await userApi.update(row.id, { password: value })
  ElMessage.success('密码已重置')
}

onMounted(reload)
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
  flex: 1;
  min-width: 180px;
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
  box-shadow: 0 6px 16px rgba(0,0,0,.15);
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

.user-table :deep(.el-table__row) { transition: background .15s ease; }
.user-table :deep(.el-table__row:hover) { background: #f5efe6 !important; }

.user-cell { display: flex; align-items: center; gap: 12px; }
.avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0,0,0,.12);
  letter-spacing: .5px;
}
.user-info { line-height: 1.3; }
.username { font-weight: 600; color: var(--txt-primary); }
.real-name { font-size: 12px; }

:deep(.user-dialog .el-dialog__body) { padding: 20px 24px 10px; }
</style>
