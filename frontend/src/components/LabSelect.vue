<template>
  <div>
    <el-select
      :model-value="selectedLabId"
      placeholder="选择地点"
      clearable
      style="width: 100%;"
      @change="onLabChange"
    >
      <el-option
        v-for="l in labs"
        :key="l.id"
        :label="l.name"
        :value="l.id"
      />
      <el-option label="其他地点" :value="-1" />
    </el-select>
    <el-input
      v-if="isOther"
      :model-value="otherLocation"
      placeholder="请输入具体地点"
      style="margin-top: 8px;"
      @update:model-value="$emit('update:otherLocation', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { labApi } from '@/api/labs'
import type { Lab } from '@/types'

const props = defineProps<{
  labId?: number | null
  otherLocation?: string
}>()

const emit = defineEmits<{
  (e: 'update:labId', val: number | null): void
  (e: 'update:otherLocation', val: string): void
}>()

const labs = ref<Lab[]>([])

const selectedLabId = computed(() => {
  if (props.labId) return props.labId
  // labId 被显式设为 null 表示选了"其他地点"；有 otherLocation 文本也表示其他地点
  if (props.labId === null || props.otherLocation) return -1
  return undefined
})

const isOther = computed(() => selectedLabId.value === -1)

function onLabChange(val: number | undefined) {
  if (val === -1) {
    emit('update:labId', null)
    emit('update:otherLocation', props.otherLocation || '')
  } else {
    emit('update:labId', val || null)
    emit('update:otherLocation', '')
  }
}

async function loadLabs() {
  try {
    const r = await labApi.list({ page_size: 999 })
    labs.value = r.results || []
  } catch {
    labs.value = []
  }
}

onMounted(loadLabs)
</script>
