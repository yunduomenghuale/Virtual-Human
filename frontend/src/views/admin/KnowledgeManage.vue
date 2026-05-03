<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <span class="section-title" style="margin:0;">知识库管理</span>
          </div>
          <div class="header-actions">
            <el-button plain @click="reloadCorpus">
              <el-icon style="margin-right:4px;"><RefreshLeft /></el-icon>重置示例语料
            </el-button>
            <el-button type="primary" @click="openText">
              <el-icon style="margin-right:4px;"><Plus /></el-icon>录入文本
            </el-button>
            <el-upload :auto-upload="false" :on-change="onFile" :show-file-list="false"
                       accept=".txt,.md,.pdf">
              <el-button>
                <el-icon style="margin-right:4px;"><Upload /></el-icon>上传文件
              </el-button>
            </el-upload>
          </div>
        </div>
      </template>

      <el-table :data="rows" stripe>
        <el-table-column type="index" width="50" />
        <el-table-column label="标题" min-width="180">
          <template #default="{ row }">
            <div class="doc-cell">
              <span class="doc-icon" :style="{ background: docColor(row.source) }">
                <el-icon :size="16"><Document /></el-icon>
              </span>
              <div class="doc-info">
                <div class="doc-title">{{ row.title }}</div>
                <div class="muted doc-source">{{ row.source }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="片段数" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.chunk_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
        <el-table-column prop="uploader_name" label="上传者" width="100" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" min-width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="删除" placement="top">
              <el-button text circle type="danger" @click="remove(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="textDialog" title="录入文本" width="640px">
      <el-form :model="textForm" label-width="80px">
        <el-form-item label="标题"><el-input v-model="textForm.title" /></el-form-item>
        <el-form-item label="标识">
          <el-input v-model="textForm.source" placeholder="source 唯一标识,例:lab-fire-2026-04" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="textForm.description" /></el-form-item>
        <el-form-item label="正文">
          <el-input v-model="textForm.text" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="textDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitText">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="fileDialog" title="上传文件" width="480px">
      <p class="muted" style="margin-top: 0;">即将上传:<b>{{ pendingFile?.name }}</b></p>
      <el-form :model="fileForm" label-width="80px">
        <el-form-item label="标题"><el-input v-model="fileForm.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="fileForm.description" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fileDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitFile">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '@/api/knowledge'

const rows = ref<any[]>([])
const totalChunks = computed(() => rows.value.reduce((s, r) => s + (r.chunk_count || 0), 0))
const uniqueUploaders = computed(() => {
  const set = new Set<string>()
  for (const r of rows.value) if (r.uploader_name) set.add(r.uploader_name)
  return set.size
})

const textDialog = ref(false)
const fileDialog = ref(false)
const submitting = ref(false)
const pendingFile = ref<File | null>(null)
const textForm = reactive({ title: '', source: '', description: '', text: '' })
const fileForm = reactive({ title: '', description: '' })

const PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
function docColor(source: string) {
  if (!source) return PALETTE[0]
  let h = 0
  for (let i = 0; i < source.length; i++) h = (h * 31 + source.charCodeAt(i)) >>> 0
  return PALETTE[h % PALETTE.length]
}

async function reload() {
  const r = await knowledgeApi.documentList()
  rows.value = r.results || []
}

function openText() {
  Object.assign(textForm, { title: '', source: '', description: '', text: '' })
  textDialog.value = true
}

async function submitText() {
  if (!textForm.title || !textForm.source || !textForm.text) {
    ElMessage.warning('请填写标题 / 标识 / 正文')
    return
  }
  submitting.value = true
  try {
    await knowledgeApi.ingestText(textForm)
    ElMessage.success('已写入向量库')
    textDialog.value = false
    reload()
  } finally {
    submitting.value = false
  }
}

function onFile(f: any) {
  const real = f.raw || f
  if (!real) return
  pendingFile.value = real
  fileForm.title = real.name
  fileForm.description = ''
  fileDialog.value = true
}

async function submitFile() {
  if (!pendingFile.value) return
  submitting.value = true
  try {
    await knowledgeApi.ingestFile(pendingFile.value, fileForm.title, fileForm.description)
    ElMessage.success('已写入向量库')
    fileDialog.value = false
    reload()
  } finally {
    submitting.value = false
  }
}

async function remove(row: any) {
  await ElMessageBox.confirm(`确定删除「${row.title}」及其全部向量片段?`, '确认', { type: 'warning' })
  await knowledgeApi.removeDocument(row.id)
  ElMessage.success('已删除')
  reload()
}

async function reloadCorpus() {
  await ElMessageBox.confirm('将重置内置示例语料(覆盖同名 source),继续?', '确认', { type: 'warning' })
  await knowledgeApi.reloadCorpus()
  ElMessage.success('已重新载入示例语料')
  reload()
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

:deep(.el-table__row) { transition: background .15s ease; }
:deep(.el-table__row:hover) { background: #f5efe6 !important; }

.metric-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 16px 18px;
  display: flex; gap: 14px; align-items: center;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  transition: transform .2s ease, box-shadow .2s ease;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
}
.metric-icon {
  width: 42px; height: 42px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  background: var(--accent);
  box-shadow: 0 6px 14px color-mix(in srgb, var(--accent) 35%, transparent);
}
.metric-text { flex: 1; min-width: 0; }
.metric-value {
  font-size: 24px; font-weight: 700;
  color: var(--txt-primary);
  margin-top: 2px;
  line-height: 1.1;
  letter-spacing: .5px;
}

.doc-cell { display: flex; align-items: center; gap: 12px; }
.doc-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 10px color-mix(in srgb, currentColor 20%, transparent);
}
.doc-info { min-width: 0; }
.doc-title { font-weight: 600; color: var(--txt-primary); }
.doc-source { font-size: 12px; font-family: 'Consolas', 'Monaco', monospace; }
</style>
