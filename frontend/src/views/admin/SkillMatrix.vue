<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span class="section-title" style="margin:0;">Skill 权限矩阵</span>
          </div>
          <div class="header-actions">
            <el-button plain @click="reset">
              <el-icon style="margin-right:4px;"><RefreshLeft /></el-icon>恢复默认
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" border class="matrix-table">
        <el-table-column label="角色" width="200" fixed>
          <template #default="{ row }">
            <div class="role-cell">
              <span class="role-icon" :style="{ background: roleGradient(row.role) }">
                <el-icon :size="14"><component :is="roleIcon(row.role)" /></el-icon>
              </span>
              <span class="role-name">{{ row.role_label }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-for="s in skills" :key="s.code" :label="s.label" align="center" min-width="160">
          <template #default="{ row }">
            <el-switch v-model="row[s.code].enabled"
                       inline-prompt active-text="开" inactive-text="关"
                       style="--el-switch-on-color: #ff7a1a;"
                       @change="toggle(row[s.code])" />
          </template>
        </el-table-column>
      </el-table>

    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { skillPermissionApi } from '@/api/analytics'

const ROLE_LABEL: Record<string, string> = {
  admin: '系统管理员',
  safety_officer: '实验室安全员',
  experimenter: '实验人员',
}

const skills = ref<{ code: string; label: string }[]>([])
const rows = ref<any[]>([])

function roleGradient(r: string) {
  if (r === 'admin') return 'linear-gradient(135deg, #d62828 0%, #ff7a1a 100%)'
  if (r === 'safety_officer') return 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)'
  return 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
}
function roleIcon(r: string) {
  if (r === 'admin') return 'Setting'
  if (r === 'safety_officer') return 'CircleCheck'
  return 'Avatar'
}

async function load() {
  const list = (await skillPermissionApi.list()).results || []
  const matrixResp = await skillPermissionApi.matrix()
  skills.value = matrixResp.skills

  const grouped: Record<string, any> = {}
  for (const item of list) {
    if (!grouped[item.role]) grouped[item.role] = { role: item.role, role_label: ROLE_LABEL[item.role] || item.role }
    grouped[item.role][item.skill] = { id: item.id, enabled: item.enabled }
  }
  rows.value = Object.values(grouped)
}

async function toggle(item: { id: number; enabled: boolean }) {
  await skillPermissionApi.update(item.id, item.enabled)
  ElMessage.success('已更新')
}

async function reset() {
  await ElMessageBox.confirm('确定恢复默认权限矩阵?', '确认', { type: 'warning' })
  await skillPermissionApi.reset()
  ElMessage.success('已恢复默认')
  load()
}

onMounted(load)
</script>

<style scoped>
.role-cell { display: flex; align-items: center; gap: 10px; }
.role-icon {
  width: 30px; height: 30px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0,0,0,.08);
}
.role-name { font-weight: 600; color: var(--txt-primary); }

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

.matrix-table :deep(.el-table th.el-table__cell) {
  text-align: center !important;
  background: linear-gradient(180deg, #fafbfc 0%, #f3f5fa 100%) !important;
}
.matrix-table :deep(.el-table__row) { transition: background .15s ease; }
.matrix-table :deep(.el-table__row:hover) { background: #f5efe6 !important; }

</style>
