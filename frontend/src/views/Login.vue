<template>
  <div class="login-page">
    <div class="bg-shape shape-a"></div>
    <div class="bg-shape shape-b"></div>
    <div class="bg-shape shape-c"></div>

    <div class="login-card">
      <div class="brand">
        <div class="logo">
          <el-icon :size="38" color="#fff"><TrendCharts /></el-icon>
        </div>
        <h1>智安平台</h1>
        <p class="subtitle">AI 驱动的实验室隐患排查与报告平台</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onLogin">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码"
                    size="large" :prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" size="large" native-type="submit" :loading="loading"
                   class="login-btn">
          登 录
        </el-button>
      </el-form>
    </div>

    <p class="footer">© 2026 Lab Fire Safety AI · Powered by Vue 3 + Django + LangChain</p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
async function onLogin() {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 20%, rgba(255,140,0,.18) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(214,40,40,.18) 0%, transparent 45%),
    linear-gradient(135deg, #182245 0%, #2c3a64 60%, #4a1c4a 100%);
}
.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
  animation: float 14s ease-in-out infinite;
}
.shape-a {
  width: 320px; height: 320px;
  background: rgba(255, 122, 26, .35);
  top: -80px; left: -80px;
}
.shape-b {
  width: 380px; height: 380px;
  background: rgba(214, 40, 40, .28);
  bottom: -120px; right: -100px;
  animation-delay: -5s;
}
.shape-c {
  width: 220px; height: 220px;
  background: rgba(96, 165, 250, .22);
  top: 40%; left: 60%;
  animation-delay: -9s;
}
@keyframes float {
  0%, 100% { transform: translateY(0) translateX(0); }
  50%      { transform: translateY(-20px) translateX(15px); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 36px 36px 28px;
  background: rgba(255,255,255,.95);
  backdrop-filter: blur(14px);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,.5);
  box-shadow: 0 24px 60px rgba(15, 23, 42, .35);
}
.brand { text-align: center; margin-bottom: 24px; }
.brand .logo {
  width: 64px; height: 64px;
  border-radius: 16px;
  display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%);
  box-shadow: 0 10px 24px rgba(214, 40, 40, .4);
}
.brand h1 {
  font-size: 20px;
  margin: 14px 0 6px;
  color: #1f2937;
  font-weight: 700;
  letter-spacing: .5px;
}
.subtitle { font-size: 13px; color: #8b94a3; margin: 0; }

.login-btn {
  width: 100%;
  height: 44px !important;
  margin-top: 4px;
  background: linear-gradient(135deg, #ff7a1a 0%, #d62828 100%) !important;
  border: none !important;
  font-size: 15px;
  letter-spacing: 4px;
  box-shadow: 0 8px 18px rgba(214, 40, 40, .25);
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 10px 22px rgba(214, 40, 40, .32); }

.footer {
  position: absolute;
  bottom: 16px;
  width: 100%;
  text-align: center;
  font-size: 12px;
  color: rgba(255,255,255,.5);
}
</style>
