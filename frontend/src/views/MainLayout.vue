<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="brand" :class="{ collapsed }">
        <span class="logo">
          <el-icon :size="18" color="#fff"><Shield /></el-icon>
        </span>
        <span class="brand-text" :class="{ hidden: collapsed }">智安平台</span>
      </div>
      <el-menu :default-active="route.path" :collapse="collapsed" router unique-opened>
        <template v-for="item in menus" :key="item.path">
          <el-menu-item :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <el-button text @click="collapsed = !collapsed">
          <el-icon :size="18">
            <component :is="collapsed ? 'Expand' : 'Fold'" />
          </el-icon>
        </el-button>
        <div class="topbar-title">{{ route.meta.title || '' }}</div>
        <div class="topbar-right">
          <el-tag :type="roleTag" effect="plain">{{ auth.user?.role_label }}</el-tag>
          <el-dropdown @command="onCommand">
            <span class="user-trigger">
              <el-avatar :size="28" style="background:#ff8c00; color:#fff;">
                {{ (auth.user?.real_name || auth.user?.username || '?').slice(0,1) }}
              </el-avatar>
              <span style="margin-left:8px">{{ auth.user?.real_name || auth.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="changepwd">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="pwdVisible" title="修改密码" width="380px">
    <el-form :model="pwdForm" label-width="90px">
      <el-form-item label="原密码"><el-input v-model="pwdForm.old_password" type="password" show-password /></el-form-item>
      <el-form-item label="新密码"><el-input v-model="pwdForm.new_password" type="password" show-password /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" @click="submitPwd">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const collapsed = ref(false)
const pwdVisible = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '' })

onMounted(() => { if (!auth.user) auth.fetchMe() })

const roleTag = computed(() => {
  if (auth.role === 'admin') return 'danger'
  if (auth.role === 'safety_officer') return 'warning'
  return 'info'
})

interface MenuItem { path: string; title: string; icon: string; condition: () => boolean }
const allMenus: MenuItem[] = [
  { path: '/dashboard', title: '首页', icon: 'House', condition: () => true },
  { path: '/admin/users', title: '用户管理', icon: 'User', condition: () => auth.isAdmin },
  { path: '/admin/labs', title: '实验室管理', icon: 'OfficeBuilding', condition: () => auth.isAdmin },
  { path: '/admin/permissions', title: 'Skill 权限', icon: 'Lock', condition: () => auth.isAdmin },
  { path: '/admin/knowledge', title: '知识库管理', icon: 'Collection', condition: () => auth.isAdmin },
  { path: '/agent', title: '小安', icon: 'MagicStick', condition: () => true },
  { path: '/agent/history', title: '对话历史', icon: 'ChatDotRound', condition: () => true },
  { path: '/hazards/history', title: '识别历史', icon: 'List', condition: () => auth.hasSkill('hazard_detect') },
  { path: '/reports', title: '报告列表', icon: 'Document', condition: () => auth.hasSkill('report_gen') },
  { path: '/analytics/deep', title: '深度分析', icon: 'TrendCharts', condition: () => auth.isAdmin },
]
const menus = computed(() => allMenus.filter(m => m.condition()))

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    router.replace('/login')
  } else if (cmd === 'changepwd') {
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdVisible.value = true
  }
}
async function submitPwd() {
  if (!pwdForm.old_password || !pwdForm.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  await authApi.changePassword(pwdForm.old_password, pwdForm.new_password)
  ElMessage.success('密码已更新,请重新登录')
  pwdVisible.value = false
  auth.logout()
  router.replace('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.aside {
  background: linear-gradient(180deg, #1f2c4d 0%, #2c3a64 100%);
  transition: width .35s cubic-bezier(.4, 0, .2, 1);
  overflow-x: hidden;
  position: relative;
}
.aside::after {
  content: '';
  position: absolute;
  inset: 0 0 0 auto;
  width: 1px;
  background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,140,0,.4) 50%, rgba(255,255,255,0) 100%);
  pointer-events: none;
}
.brand {
  height: 60px;
  display: flex; align-items: center; gap: 10px;
  padding: 0 18px;
  color: #fff;
  font-weight: 700;
  letter-spacing: .5px;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.brand .logo {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%);
  box-shadow: 0 4px 12px rgba(214, 40, 40, .35);
}
.brand.collapsed { justify-content: center; padding: 0; }
.brand.collapsed .logo { width: 36px; height: 36px; margin: 0; }
.brand.collapsed .logo .el-icon { font-size: 20px; }
.brand-text {
  opacity: 1;
  max-width: 200px;
  transition: opacity .3s cubic-bezier(.4, 0, .2, 1), max-width .3s cubic-bezier(.4, 0, .2, 1);
  overflow: hidden;
  white-space: nowrap;
}
.brand-text.hidden {
  opacity: 0;
  max-width: 0;
}

:deep(.el-menu) {
  border-right: none !important;
  background: transparent !important;
  padding: 8px;
}
:deep(.el-menu-item) {
  height: 48px !important;
  line-height: 48px !important;
  border-radius: 8px;
  margin: 6px;
  color: #cfd6e4 !important;
  transition: background .15s ease, color .15s ease;
}
:deep(.el-menu-item .el-icon) {
  font-size: 20px;
  transition: margin .3s cubic-bezier(.4, 0, .2, 1);
}
:deep(.el-menu-item:hover) {
  background: rgba(255, 140, 0, .12) !important;
  color: #fff !important;
}
:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(255,122,26,.22) 0%, rgba(214,40,40,.22) 100%) !important;
  color: #ffd166 !important;
  position: relative;
}
:deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: -6px; top: 10px; bottom: 10px; width: 3px;
  background: linear-gradient(180deg, #ff7a1a 0%, #d62828 100%);
  border-radius: 2px;
}

/* 收起状态美化 */
:deep(.el-menu--collapse) {
  padding: 8px;
}
:deep(.el-menu--collapse .el-menu-item) {
  margin: 6px auto;
  width: 48px;
  height: 48px !important;
  line-height: 48px !important;
  border-radius: 12px;
  justify-content: center;
  padding: 0 !important;
}
:deep(.el-menu--collapse .el-menu-item .el-icon) {
  font-size: 20px;
  margin: 0;
}
:deep(.el-menu--collapse .el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(255,122,26,.35) 0%, rgba(214,40,40,.35) 100%) !important;
  box-shadow: 0 4px 14px rgba(255, 122, 26, .25), inset 0 0 0 1px rgba(255, 180, 100, .15);
}
:deep(.el-menu--collapse .el-menu-item.is-active::before) {
  left: -8px;
  top: 10px;
  bottom: 10px;
  width: 4px;
  border-radius: 0 3px 3px 0;
}
:deep(.el-menu--collapse .el-tooltip__trigger) {
  justify-content: center;
  padding: 0 !important;
}

.topbar {
  display: flex; align-items: center; gap: 12px;
  background: rgba(242,244,248,.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #d5dae5;
  padding: 0 22px;
  height: 60px;
  box-shadow: 0 1px 0 rgba(15, 23, 42, .03);
}
.topbar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--txt-primary, #1f2937);
}
.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 14px; }
.user-trigger {
  display: inline-flex; align-items: center; cursor: pointer;
  padding: 4px 8px; border-radius: 8px;
  transition: background .15s ease;
}
.user-trigger:hover { background: #f3f5fa; }

.fade-enter-active, .fade-leave-active { transition: opacity .15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
