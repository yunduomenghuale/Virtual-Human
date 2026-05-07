<template>
  <div class="scenario-manage">
    <el-tabs v-model="activeTab" class="manage-tabs">
      <el-tab-pane label="演练场景库" name="scenarios">
        <div class="tab-content">
          <div class="page-header">
            <div class="header-left">
              <h2>场景演练库管理</h2>
              <span class="subtitle">管理用于消防培训和案例分析的模拟场景</span>
            </div>
            <div class="header-actions">
              <el-button type="success" plain @click="openImportDialog">
                <el-icon><DocumentAdd /></el-icon> 智能导入方案
              </el-button>
              <el-button type="primary" @click="openDialog()">
                <el-icon><Plus /></el-icon> 新增场景
              </el-button>
            </div>
          </div>

          <div class="filter-bar">
            <el-input v-model="filters.topic" placeholder="搜索主题分类" clearable style="width: 200px" @change="fetchData" />
            <el-select v-model="filters.difficulty" placeholder="选择难度" clearable style="width: 150px" @change="fetchData">
              <el-option label="低难度" value="low" />
              <el-option label="中难度" value="medium" />
              <el-option label="高难度" value="high" />
            </el-select>
          </div>

          <el-table v-loading="loading" :data="tableData" border stripe>
            <el-table-column prop="id" label="ID" width="80" align="center" />
            <el-table-column prop="title" label="场景标题" min-width="150" />
            <el-table-column prop="topic" label="主题分类" width="120" />
            <el-table-column prop="difficulty" label="难度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.difficulty === 'high' ? 'danger' : row.difficulty === 'medium' ? 'warning' : 'success'">
                  {{ row.difficulty === 'high' ? '高难度' : row.difficulty === 'medium' ? '中难度' : '低难度' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="material_name" label="关联课件" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.material_name" style="color: #606266; font-size: 13px">
                  <el-icon><Document /></el-icon> {{ row.material_name }}
                </span>
                <span v-else class="muted">手动录入</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除该场景吗？" @confirm="handleDelete(row.id)">
                  <template #reference>
                    <el-button link type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="原始课件库" name="materials">
        <div class="tab-content">
          <div class="page-header">
            <div class="header-left">
              <h2>课件素材管理</h2>
              <span class="subtitle">管理上传的 PPTX 和 PDF 培训课件源文件</span>
            </div>
          </div>

          <el-table v-loading="materialLoading" :data="materials" border stripe>
            <el-table-column prop="id" label="ID" width="80" align="center" />
            <el-table-column prop="file_name" label="课件名称" min-width="200" />
            <el-table-column prop="file_type" label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.file_type === 'pdf' ? 'warning' : 'danger'">
                  {{ row.file_type.toUpperCase() }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="downloadFile(row.file)">下载原文</el-button>
                <el-popconfirm title="确定删除该课件吗？(不会删除已生成的场景)" @confirm="handleDeleteMaterial(row.id)">
                  <template #reference>
                    <el-button link type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 弹窗表单 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑场景' : '新增场景'" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="场景标题" prop="title">
          <el-input v-model="form.title" placeholder="例如：实验室电气起火应急演练" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主题分类" prop="topic">
              <el-input v-model="form.topic" placeholder="例如：电气火灾" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度" prop="difficulty">
              <el-select v-model="form.difficulty" style="width: 100%">
                <el-option label="低难度" value="low" />
                <el-option label="中难度" value="medium" />
                <el-option label="高难度" value="high" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="场景描述" prop="description">
          <el-input type="textarea" :rows="3" v-model="form.description" placeholder="用于向用户播报的事故现场情况描述..." />
        </el-form-item>

        <el-form-item label="现场模拟图">
          <el-upload
            class="avatar-uploader"
            action=""
            :auto-upload="false"
            :show-file-list="false"
            :on-change="onImageChange"
            accept="image/*"
          >
            <img v-if="previewImageUrl" :src="previewImageUrl" class="uploaded-img" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持 jpg/png，主要用于辅助用户判断</div>
        </el-form-item>

        <el-form-item label="标准处置流程" prop="correct_actions">
          <el-input type="textarea" :rows="4" v-model="form.correct_actions" placeholder="供 AI 评判作答的参考标准..." />
        </el-form-item>

        <el-form-item label="案例点评分析" prop="analysis">
          <el-input type="textarea" :rows="3" v-model="form.analysis" placeholder="演练结束后给出的总结与事故防范建议..." />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveData" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <DocImportDialog ref="importDialogRef" @success="fetchData" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { scenarioApi } from '@/api/scenarios'
import type { FireScenario } from '@/api/scenarios'
import { Plus, DocumentAdd, Document } from '@element-plus/icons-vue'
import DocImportDialog from './components/DocImportDialog.vue'

const activeTab = ref('scenarios')
const loading = ref(false)
const tableData = ref<FireScenario[]>([])
const filters = ref({ topic: '', difficulty: '' })

const materials = ref<any[]>([])
const materialLoading = ref(false)

// 智能导入
const importDialogRef = ref()
function openImportDialog() {
  importDialogRef.value.open()
}

// 表单弹窗
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const formRef = ref()
const form = ref<any>({})
const selectedImage = ref<File | null>(null)
const previewImageUrl = ref('')

async function fetchMaterials() {
  materialLoading.value = true
  try {
    const res: any = await scenarioApi.listMaterials()
    materials.value = res.results || res
  } catch (e) {
    ElMessage.error('获取课件库失败')
  } finally {
    materialLoading.value = false
  }
}

function downloadFile(url: string) {
  if (!url) return
  window.open(url, '_blank')
}

async function handleDeleteMaterial(id: number) {
  try {
    await scenarioApi.deleteMaterial(id)
    ElMessage.success('删除成功')
    fetchMaterials()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

watch(activeTab, (val) => {
  if (val === 'materials') fetchMaterials()
  else fetchData()
})

const rules = {
  title: [{ required: true, message: '必填', trigger: 'blur' }],
  topic: [{ required: true, message: '必填', trigger: 'blur' }],
  difficulty: [{ required: true, message: '必选', trigger: 'change' }],
  description: [{ required: true, message: '必填', trigger: 'blur' }],
  correct_actions: [{ required: true, message: '必填', trigger: 'blur' }],
}

async function fetchData() {
  loading.value = true
  try {
    const res: any = await scenarioApi.list(filters.value)
    tableData.value = res.results || res
  } catch (e: any) {
    if (e.response?.status !== 401) {
      ElMessage.error('获取场景列表失败')
    }
  } finally {
    loading.value = false
  }
}

function openDialog(row?: FireScenario) {
  isEdit.value = !!row
  selectedImage.value = null
  previewImageUrl.value = ''
  
  if (row) {
    form.value = { ...row }
    if (row.image) previewImageUrl.value = row.image
  } else {
    form.value = {
      title: '', topic: '', difficulty: 'medium',
      description: '', correct_actions: '', analysis: ''
    }
  }
  dialogVisible.value = true
}

function onImageChange(file: any) {
  if (file && file.raw) {
    selectedImage.value = file.raw
    previewImageUrl.value = URL.createObjectURL(file.raw)
  }
}

async function saveData() {
  await formRef.value.validate()
  saving.value = true
  
  try {
    const formData = new FormData()
    formData.append('title', form.value.title)
    formData.append('topic', form.value.topic)
    formData.append('difficulty', form.value.difficulty)
    formData.append('description', form.value.description)
    formData.append('correct_actions', form.value.correct_actions)
    formData.append('analysis', form.value.analysis || '')
    
    if (selectedImage.value) {
      formData.append('image', selectedImage.value)
    }

    if (isEdit.value) {
      await scenarioApi.update(form.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await scenarioApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await scenarioApi.delete(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) {
    ElMessage.error('删除失败')
  }
}

function formatDate(ds: string) {
  if (!ds) return ''
  const d = new Date(ds)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.scenario-manage {
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header-left h2 { margin: 0 0 4px; font-size: 18px; color: #1f2937; }
.header-left .subtitle { font-size: 13px; color: #6b7280; }
.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.avatar-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 178px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}
.avatar-uploader:hover { border-color: #409eff; }
.avatar-uploader-icon { font-size: 28px; color: #8c939d; }
.uploaded-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.upload-tip { font-size: 12px; color: #9ca3af; margin-top: 6px; line-height: 1.4; }
</style>
