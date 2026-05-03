<template>
  <div class="page">
    <el-card>
      <template #header>
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <span class="section-title" style="margin:0;">对话历史</span>
          <el-button type="primary" @click="$router.push('/agent')">+ 新对话</el-button>
        </div>
      </template>

      <el-empty v-if="!sessions.length" description="暂无对话记录" />

      <div v-else class="session-list">
        <div v-for="s in sessions" :key="s.id" class="session-item">
          <div class="session-main" @click="goChat(s.id)">
            <div class="session-title">{{ s.title || '新对话' }}</div>
            <div class="session-meta">
              <span>{{ formatTime(s.updated_at) }}</span>
              <el-tag size="small" type="info">{{ s.message_count || s.messages.length }} 条消息</el-tag>
              <el-tag v-if="auth.isAdmin && s.user_name" size="small" type="warning" effect="plain">
                {{ s.user_real_name || s.user_name }}
              </el-tag>
            </div>
            <div v-if="lastContent(s)" class="session-preview">{{ lastContent(s) }}</div>
          </div>
          <div class="session-actions">
            <el-button link type="primary" @click="goChat(s.id)">继续</el-button>
            <el-button link type="danger" @click="remove(s.id)">删除</el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { chatApi, type ChatSession } from '@/api/chat'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const sessions = ref<ChatSession[]>([])

async function load() {
  try {
    const r = await chatApi.list()
    sessions.value = r.results || []
  } catch {
    sessions.value = []
  }
}

async function remove(id: string) {
  await ElMessageBox.confirm('确定删除这条对话记录?', '确认', { type: 'warning' })
  await chatApi.remove(id)
  ElMessage.success('已删除')
  load()
}

function goChat(id: string) {
  window.location.href = `/agent?session=${id}`
}

function lastContent(s: ChatSession): string {
  const msgs = Array.isArray(s.messages) ? s.messages : []
  const last = [...msgs].reverse().find((m: any) => m.content)
  return last ? (last.content as string).slice(0, 60) : ''
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(load)
</script>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  background: #fff;
  transition: all .15s ease;
  cursor: pointer;
}
.session-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.session-main {
  flex: 1;
  min-width: 0;
}
.session-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--txt-primary);
  margin-bottom: 4px;
}
.session-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--txt-muted);
  margin-bottom: 4px;
}
.session-preview {
  font-size: 13px;
  color: var(--txt-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 12px;
}
</style>
