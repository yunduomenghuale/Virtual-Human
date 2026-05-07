<template>
  <div class="tool-card" :class="cardCls">
    <!-- header -->
    <div class="tool-head">
      <span class="tool-icon" :style="{ background: headColor }">
        <el-icon :size="14"><component :is="headIcon" /></el-icon>
      </span>
      <span class="tool-name">{{ headTitle }}</span>
      <el-tag v-if="!tc.ok" type="danger" size="small" effect="plain" style="margin-left:auto">失败</el-tag>
      <el-tag v-else size="small" effect="plain" style="margin-left:auto">{{ headTitle }}</el-tag>
    </div>

    <!-- error -->
    <div v-if="tc.result.type === 'error'" class="err-msg">
      {{ tc.result.message }}
    </div>

    <!-- knowledge_qa -->
    <div v-else-if="tc.result.type === 'knowledge_qa'">
      <div class="kq-q">
        <el-icon><Search /></el-icon> 检索:{{ tc.result.query }}
      </div>
      <div v-if="!tc.result.sources?.length" class="muted">未命中知识库,以下回答基于通用知识。</div>
      <div v-else class="src-list">
        <div v-for="(s, i) in tc.result.sources" :key="i" class="src-item">
          <span class="src-num">{{ i + 1 }}</span>
          <div class="src-body">
            <div class="src-title">{{ s.title }}</div>
            <div class="src-snippet">{{ s.snippet }}</div>
          </div>
          <span class="src-score">{{ s.score?.toFixed(3) }}</span>
        </div>
      </div>
    </div>

    <!-- hazard_detection -->
    <div v-else-if="tc.result.type === 'hazard_detection'">
      <div class="hz-grid">
        <div class="hz-image">
          <img :src="hazardImage" />
        </div>
        <div class="hz-info">
          <div class="hz-row">
            <span class="hz-label">总体风险</span>
            <el-tag :type="severityTag(tc.result.data.overall_severity)" effect="dark">
              {{ severityLabel(tc.result.data.overall_severity) }}
            </el-tag>
          </div>
          <div class="hz-row">
            <span class="hz-label">地点</span>
            <span v-if="!editingLoc" style="display:flex; align-items:center; gap:6px;">
              {{ tc.result.data.lab_name || '未填' }}
              <el-button v-if="tc.result.data?.id" link size="small" @click="startEditLoc">
                <el-icon><Edit /></el-icon>
              </el-button>
            </span>
            <span v-else style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
              <LabSelect v-model:lab-id="editLabId" v-model:other-location="editOtherLocation" style="width:180px;" />
              <el-button size="small" :loading="locSaving" @click="saveLoc">保存</el-button>
            </span>
          </div>
          <div class="hz-row">
            <span class="hz-label">隐患数</span>
            <span class="hz-count">{{ tc.result.data.hazards.length }}</span>
          </div>
          <div class="hz-row" style="align-items: flex-start;">
            <span class="hz-label">评估</span>
            <MarkdownText v-if="tc.result.data.summary" class="hz-summary" :text="tc.result.data.summary" />
            <span v-else class="hz-summary">-</span>
          </div>
        </div>
      </div>
      <el-collapse v-if="tc.result.data.hazards.length" style="margin-top:10px;">
        <el-collapse-item>
          <template #title>
            <span style="font-weight:600;">隐患明细 ({{ tc.result.data.hazards.length }})</span>
          </template>
          <div v-for="(h, idx) in tc.result.data.hazards" :key="idx" class="hz-item">
            <div class="hz-item-head">
              <span class="hz-num">{{ idx + 1 }}</span>
              <span style="font-weight:600;">{{ h.name }}</span>
              <el-tag size="small" effect="plain" style="margin-left:6px">{{ h.category }}</el-tag>
              <el-tag size="small" :type="severityTag(h.severity)" style="margin-left:6px">
                {{ severityLabel(h.severity) }}
              </el-tag>
            </div>
            <div class="hz-item-body">
              <p><b>描述:</b><MarkdownText :text="h.description" inline /></p>
              <p><b>建议:</b><MarkdownText :text="h.suggestion" inline /></p>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- report -->
    <div v-else-if="tc.result.type === 'report'">
      <div class="rp-head">
        <div class="rp-title">{{ tc.result.data.title }}</div>
        <el-tag :type="severityTag(tc.result.data.overall_severity)" effect="dark">
          {{ severityLabel(tc.result.data.overall_severity) }}
        </el-tag>
      </div>
      <div class="rp-meta">
        <span><b>地点:</b>{{ tc.result.data.lab_name }}</span>
        <span><b>检查人:</b>{{ tc.result.data.inspector || '-' }}</span>
        <span><b>检测数:</b>{{ tc.result.data.detection_count }}</span>
        <span><b>隐患合计:</b>{{ tc.result.data.summary_stats?.total ?? 0 }}</span>
      </div>
      <div v-if="tc.result.data.agent_evaluation" class="rp-eval">
        <div class="rp-eval-label"><b>AI 评价</b></div>
        <MarkdownText :text="tc.result.data.agent_evaluation" />
      </div>
      <div class="rp-actions">
        <el-button type="primary" size="small" @click="goReport(tc.result.data.id)">
          <el-icon style="margin-right:4px"><View /></el-icon>查看详情
        </el-button>
        <el-button size="small" :disabled="!tc.result.data.pdf_file"
                   @click="download(tc.result.data.pdf_file, tc.result.data.title + '.pdf')">
          <el-icon style="margin-right:4px"><Download /></el-icon>PDF
        </el-button>
        <el-button size="small" :disabled="!tc.result.data.docx_file"
                   @click="download(tc.result.data.docx_file, tc.result.data.title + '.docx')">
          <el-icon style="margin-right:4px"><Download /></el-icon>Word
        </el-button>
      </div>
    </div>

    <!-- scenario_training -->
    <div v-else-if="tc.result.type === 'scenario_training'">
      <!-- 场景列表 -->
      <div v-if="tc.result.mode === 'list'" class="st-list">
        <div class="st-list-head">
          <div class="st-title">📚 消防培训场景库</div>
          <span class="st-count">共 {{ tc.result.items.length }} 个场景</span>
        </div>
        <div class="st-list-body">
          <div
            v-for="(item, idx) in tc.result.items"
            :key="item.id"
            class="st-list-item"
            @click="selectScenario(item)"
          >
            <div v-if="item.image" class="st-item-img">
              <img :src="item.image" />
            </div>
            <div class="st-item-info">
              <div class="st-item-title">
                <span class="st-item-num">{{ idx + 1 }}</span>
                {{ item.title }}
              </div>
              <div class="st-item-meta">
                <el-tag size="small" effect="plain">{{ item.topic }}</el-tag>
                <el-tag size="small" :type="difficultyTag(item.difficulty)" effect="dark">{{ item.difficulty }}</el-tag>
              </div>
              <div class="st-item-desc">{{ item.description }}</div>
            </div>
            <el-button type="primary" size="small" plain>选择学习</el-button>
          </div>
        </div>
      </div>

      <!-- 教学模式 -->
      <div v-else-if="tc.result.mode === 'teaching'" class="st-teaching">
        <div class="st-head">
          <div class="st-title">📖 消防培训：{{ tc.result.data.title }}</div>
        </div>
        <div class="st-content">
          <MarkdownText :text="tc.result.data.teaching_content" />
        </div>
        <div class="st-tip">
          <el-icon><InfoFilled /></el-icon> 讲解完毕后，请对小安说“开始实战测试”
        </div>
      </div>

      <!-- 演习模式 - 有评分结果 -->
      <div v-else-if="tc.result.mode === 'testing' && tc.result.score != null" class="st-testing">
        <div class="result-header">
          <div class="result-label">演练评估结果</div>
          <div class="score" :class="getScoreClass(tc.result.score)">{{ tc.result.score }}<span>分</span></div>
        </div>

        <div class="analysis-box">
          <div class="box-title">专家点评</div>
          <p>{{ tc.result.analysis }}</p>
        </div>

        <!-- 资料下载卡片 -->
        <div v-if="tc.result.data?.material_file" class="material-download-card">
          <div class="m-icon">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="m-info">
            <div class="m-name">{{ tc.result.data.material_name }}</div>
            <div class="m-tip">点击下载原始课件，巩固消防知识</div>
          </div>
          <el-button type="primary" size="small" circle @click="openMaterial(tc.result.data.material_file)">
            <el-icon><Download /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 演习模式 - 首次进入/场景描述 -->
      <div v-else-if="tc.result.mode === 'testing'" class="st-testing-intro">
        <div class="st-head">
          <div class="st-title">🎯 实战演练：{{ tc.result.data.title }}</div>
          <el-tag size="small" effect="dark">{{ tc.result.data.difficulty }}</el-tag>
        </div>
        <div v-if="tc.result.data.image" class="st-image">
          <img :src="tc.result.data.image" />
        </div>
        <div class="st-desc">
          <p><b>场景描述:</b> <MarkdownText :text="tc.result.data.description" inline /></p>
        </div>
        <!-- 资料下载卡片 -->
        <div v-if="tc.result.data?.material_file" class="material-download-card">
          <div class="m-icon">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="m-info">
            <div class="m-name">{{ tc.result.data.material_name }}</div>
            <div class="m-tip">点击下载原始课件，巩固消防知识</div>
          </div>
          <el-button type="primary" size="small" circle @click="openMaterial(tc.result.data.material_file)">
            <el-icon><Download /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- analytics -->
    <div v-else-if="tc.result.type === 'analytics'">
      <div class="an-metric">指标:<b>{{ metricLabel(tc.result.metric) }}</b></div>
      <component :is="'div'">
        <!-- overview -->
        <div v-if="tc.result.metric === 'overview'" class="an-overview">
          <div class="an-cell"><div class="an-num">{{ tc.result.data.users?.total ?? 0 }}</div><div class="muted">用户</div></div>
          <div class="an-cell"><div class="an-num">{{ tc.result.data.knowledge_docs ?? 0 }}</div><div class="muted">知识文档</div></div>
          <div class="an-cell"><div class="an-num">{{ tc.result.data.detections ?? 0 }}</div><div class="muted">隐患识别</div></div>
          <div class="an-cell"><div class="an-num">{{ tc.result.data.reports ?? 0 }}</div><div class="muted">报告</div></div>
        </div>

        <!-- severity -->
        <div v-else-if="tc.result.metric === 'severity'" class="sev-bar">
          <div v-for="k in ['high','medium','low']" :key="k" class="sev-cell" :class="'sev-'+k">
            <div class="sev-name">{{ severityLabel(k as any) }}</div>
            <div class="sev-num">{{ tc.result.data[k] ?? 0 }}</div>
          </div>
        </div>

        <!-- category / top_labs / recent_detections -->
        <el-table v-else-if="['category','top_labs','recent_detections','lab_overview'].includes(tc.result.metric)"
                  :data="tableData" stripe size="small" max-height="280">
          <el-table-column v-for="c in tableCols" :key="c.prop" v-bind="c" />
        </el-table>

        <!-- trend -->
        <div v-else-if="tc.result.metric === 'trend'" class="trend-mini">
          <p class="muted" style="margin: 0 0 6px;">最近 30 日检测次数</p>
          <div class="bars">
            <div v-for="(p, i) in tc.result.data" :key="i"
                 class="bar"
                 :style="{ height: barHeight(p.count) + '%' }"
                 :title="`${p.date}: ${p.count}`" />
          </div>
        </div>

        <!-- all / fallback -->
        <pre v-else class="json-dump">{{ jsonDump }}</pre>
      </component>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import { severityTag, severityLabel } from '@/utils/severity'
import MarkdownText from '@/components/MarkdownText.vue'
import { hazardApi } from '@/api/hazards'
import LabSelect from '@/components/LabSelect.vue'
import type { AgentToolCall } from '@/types'

const props = defineProps<{ tc: AgentToolCall }>()
const emit = defineEmits<{ (e: 'select-scenario', title: string): void }>()
const router = useRouter()

const editingLoc = ref(false)
const locInput = ref('')
const editLabId = ref<number | null>(null)
const editOtherLocation = ref('')
const locSaving = ref(false)

function startEditLoc() {
  editingLoc.value = true
  editLabId.value = null
  editOtherLocation.value = props.tc.result.data?.lab_name || ''
}

async function saveLoc() {
  const id = props.tc.result.data?.id
  if (!id) return
  locSaving.value = true
  try {
    const updated = await hazardApi.updateLocation(id, {
      lab_id: editLabId.value,
      other_location: editOtherLocation.value,
    })
    props.tc.result.data.lab_name = updated.lab_name || ''
    editingLoc.value = false
    ElMessage.success('地点已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    locSaving.value = false
  }
}

const cardCls = computed(() => `tool-${props.tc.result.type}`)

const HEAD_MAP: Record<string, { icon: string; color: string; title: string }> = {
  knowledge_qa: { icon: 'ChatLineSquare', color: '#3b82f6', title: '知识问答' },
  hazard_detect: { icon: 'Picture', color: '#ef4444', title: '隐患识别' },
  hazard_detection: { icon: 'Picture', color: '#ef4444', title: '隐患识别' },
  report_gen: { icon: 'Document', color: '#f59e0b', title: '报告生成' },
  report: { icon: 'Document', color: '#f59e0b', title: '报告生成' },
  analytics_query: { icon: 'DataAnalysis', color: '#10b981', title: '数据分析' },
  analytics: { icon: 'DataAnalysis', color: '#10b981', title: '数据分析' },
  scenario_training: { icon: 'HelpFilled', color: '#8b5cf6', title: '场景演练' },
  error: { icon: 'WarningFilled', color: '#909399', title: '工具调用' },
}
const headIcon = computed(() => HEAD_MAP[props.tc.result.type]?.icon || 'MagicStick')
const headColor = computed(() => HEAD_MAP[props.tc.result.type]?.color || '#909399')
const headTitle = computed(() => HEAD_MAP[props.tc.result.type]?.title || '工具调用')

const hazardImage = computed(() => {
  if (props.tc.result.type !== 'hazard_detection') return ''
  return props.tc.result.data.annotated_image || props.tc.result.data.original_image
})

function metricLabel(m: string) {
  return ({
    overview: '系统概览',
    severity: '隐患等级分布',
    category: '隐患分类分布',
    trend: '检测趋势',
    top_labs: '地点隐患排行',
    lab_overview: '地点全景',
    recent_detections: '最近隐患识别记录',
    all: '完整看板',
  } as any)[m] || m
}

const tableData = computed(() => {
  if (props.tc.result.type !== 'analytics') return []
  return Array.isArray(props.tc.result.data) ? props.tc.result.data : []
})

const tableCols = computed(() => {
  if (props.tc.result.type !== 'analytics') return []
  const m = props.tc.result.metric
  if (m === 'category') return [
    { prop: 'category', label: '类别' },
    { prop: 'count', label: '数量', width: 100, align: 'right' },
  ]
  if (m === 'top_labs') return [
    { prop: 'lab_name', label: '地点' },
    { prop: 'hazards', label: '累计隐患', width: 120, align: 'right' },
  ]
  if (m === 'recent_detections') return [
    { prop: 'id', label: 'ID', width: 70 },
    { prop: 'lab_name', label: '地点' },
    { prop: 'overall_severity', label: '等级', width: 80 },
    { prop: 'hazard_count', label: '隐患数', width: 90, align: 'right' },
    { prop: 'created_at', label: '时间', width: 150 },
  ]
  if (m === 'lab_overview') return [
    { prop: 'lab_name', label: '地点' },
    { prop: 'detection_count', label: '检测', width: 80, align: 'right' },
    { prop: 'report_count', label: '报告', width: 80, align: 'right' },
    { prop: 'hazards_total', label: '隐患', width: 80, align: 'right' },
    { prop: 'overall_severity', label: '风险', width: 80 },
  ]
  return []
})

const jsonDump = computed(() => {
  if (props.tc.result.type !== 'analytics') return ''
  return JSON.stringify(props.tc.result.data, null, 2).slice(0, 1500)
})

function barHeight(v: number) {
  if (props.tc.result.type !== 'analytics' || props.tc.result.metric !== 'trend') return 0
  const arr = props.tc.result.data as any[]
  const max = Math.max(1, ...arr.map(p => p.count || 0))
  return Math.max(2, Math.round((v / max) * 100))
}

function goReport(id: number) {
  router.push(`/reports/${id}`)
}

function download(url: string | null, name: string) {
  if (!url) {
    ElMessage.warning('文件未生成')
    return
  }
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
}

function openMaterial(url: string) {
  window.open(url, '_blank')
}

function getScoreClass(score: number) {
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-medium'
  return 'score-low'
}

function difficultyTag(d: string) {
  if (d === '高难度') return 'danger'
  if (d === '中难度') return 'warning'
  return 'success'
}

function selectScenario(item: any) {
  emit('select-scenario', `我要学习「${item.title}」`)
}
</script>

<style scoped>
.tool-card {
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  background: #fcfdff;
  padding: 12px 14px;
}
.tool-card.tool-error { background: #fff5f5; border-color: #fecaca; }

.tool-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600;
  margin-bottom: 8px;
  color: var(--txt-primary);
}
.tool-icon {
  width: 22px; height: 22px;
  border-radius: 6px;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.tool-name { font-weight: 600; }
.err-msg { color: #d62828; font-size: 13px; }

/* knowledge_qa */
.kq-q {
  font-size: 12px; color: var(--txt-secondary);
  background: #f3f5fa;
  padding: 6px 10px; border-radius: 6px;
  margin-bottom: 8px;
  display: inline-flex; align-items: center; gap: 4px;
}
.src-list { display: flex; flex-direction: column; gap: 8px; }
.src-item {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
}
.src-num {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: #fff;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.src-body { flex: 1; min-width: 0; }
.src-title { font-weight: 600; font-size: 13px; }
.src-snippet { color: var(--txt-secondary); font-size: 12px; margin-top: 2px; line-height: 1.5; }
.src-score { color: var(--txt-muted); font-size: 11px; font-family: 'Consolas', monospace; }

/* hazard */
.hz-grid {
  display: flex; gap: 14px;
  align-items: flex-start;
}
.hz-image {
  flex: 0 0 220px;
  border-radius: 8px; overflow: hidden;
  background: #000;
}
.hz-image img { display: block; width: 100%; }
.hz-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.hz-row { display: flex; gap: 10px; align-items: center; font-size: 13px; }
.hz-label { color: var(--txt-muted); width: 60px; flex-shrink: 0; font-size: 12px; }
.hz-count { font-weight: 700; font-size: 18px; color: var(--brand-orange); }
.hz-summary { color: var(--txt-secondary); line-height: 1.6; font-size: 12px; }
.hz-item {
  padding: 8px 0;
  border-bottom: 1px dashed var(--line-soft);
}
.hz-item:last-child { border-bottom: none; }
.hz-item-head { display: flex; align-items: center; flex-wrap: wrap; }
.hz-num {
  display: inline-flex; width: 20px; height: 20px; border-radius: 50%;
  background: var(--grad-brand);
  color: #fff; font-size: 11px; font-weight: 700;
  align-items: center; justify-content: center;
  margin-right: 6px;
}
.hz-item-body p { margin: 4px 0; font-size: 12px; line-height: 1.65; color: var(--txt-secondary); }

/* report */
.rp-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 8px;
}
.rp-title { font-weight: 700; font-size: 14px; flex: 1; }
.rp-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: 12px; color: var(--txt-secondary);
  margin-bottom: 8px;
}
.rp-eval {
  background: #f7f9fd;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 12px; line-height: 1.65;
  color: var(--txt-secondary);
  margin: 8px 0;
  max-height: 200px;
  overflow-y: auto;
}
.rp-eval-label { margin-bottom: 4px; color: var(--txt-primary); }
.rp-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* scenario_training */
.st-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 8px;
}
.st-title { font-weight: 700; font-size: 14px; flex: 1; }
.st-image { margin-bottom: 8px; border-radius: 8px; overflow: hidden; background: #000; display: flex; justify-content: center; max-height: 200px; }
.st-image img { max-width: 100%; object-fit: contain; }
.st-desc p { margin: 4px 0; font-size: 12px; line-height: 1.65; color: var(--txt-secondary); }

.st-teaching {
  padding: 4px 0;
}
.st-testing-intro {
  padding: 4px 0;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.result-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--txt-primary);
}
.score {
  font-size: 32px;
  font-weight: 700;
  color: #f59e0b;
}
.score span {
  font-size: 14px;
  font-weight: 500;
  margin-left: 2px;
}
.score-high { color: #10b981; }
.score-medium { color: #f59e0b; }
.score-low { color: #ef4444; }
.analysis-box {
  background: #f7f9fd;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.analysis-box .box-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--txt-primary);
}
.analysis-box p {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
  color: var(--txt-secondary);
}
.st-content {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.7;
  color: #374151;
  max-height: 300px;
  overflow-y: auto;
}
.st-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
}

/* scenario list */
.st-list { padding: 4px 0; }
.st-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.st-count {
  font-size: 12px;
  color: var(--txt-muted);
}
.st-list-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.st-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  cursor: pointer;
  transition: all .2s ease;
}
.st-list-item:hover {
  border-color: #c7d2fe;
  background: #f5f7ff;
  box-shadow: 0 2px 8px rgba(99,102,241,.08);
}
.st-item-img {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  background: #f3f4f6;
}
.st-item-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.st-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.st-item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--txt-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.st-item-num {
  display: inline-flex;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  align-items: center;
  justify-content: center;
}
.st-item-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.st-item-desc {
  font-size: 12px;
  color: var(--txt-secondary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* analytics */
.an-metric { font-size: 12px; color: var(--txt-secondary); margin-bottom: 8px; }
.an-overview {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}
.an-cell {
  text-align: center;
  padding: 10px 6px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
}
.an-num { font-size: 20px; font-weight: 700; color: var(--brand-orange); line-height: 1.2; }
.sev-bar { display: flex; gap: 10px; }
.sev-cell {
  flex: 1;
  text-align: center;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid;
}
.sev-cell.sev-high { background: #fef2f2; border-color: #fecaca; }
.sev-cell.sev-medium { background: #fffaeb; border-color: #fde68a; }
.sev-cell.sev-low { background: #f0fdf4; border-color: #bbf7d0; }
.sev-cell.sev-high .sev-num { color: #dc2626; }
.sev-cell.sev-medium .sev-num { color: #d97706; }
.sev-cell.sev-low .sev-num { color: #16a34a; }
.sev-name { font-size: 12px; color: var(--txt-secondary); margin-bottom: 4px; }
.sev-num { font-size: 20px; font-weight: 700; }

.trend-mini .bars {
  display: flex; gap: 2px; align-items: flex-end;
  height: 60px;
  background: #f7f9fd;
  border-radius: 6px;
  padding: 4px 6px;
}
.trend-mini .bar {
  flex: 1;
  background: var(--grad-brand);
  border-radius: 2px 2px 0 0;
  min-height: 2px;
}
.json-dump {
  background: #f7f9fd;
  padding: 10px;
  border-radius: 6px;
  font-size: 11px;
  max-height: 240px;
  overflow: auto;
  margin: 0;
}
.material-download-card {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.m-icon {
  width: 40px;
  height: 40px;
  background: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.m-info {
  flex: 1;
  min-width: 0;
}
.m-name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.m-tip {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}
</style>
