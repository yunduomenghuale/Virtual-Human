import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true, layout: 'blank' },
  },
  {
    path: '/',
    component: () => import('@/views/MainLayout.vue'),
    redirect: '/agent',
    children: [
      { path: 'agent', name: 'agent',
        component: () => import('@/views/Agent.vue'),
        meta: { title: '小安' } },
      { path: 'agent/history', name: 'agent-history',
        component: () => import('@/views/ChatHistory.vue'),
        meta: { title: '对话历史' } },
      { path: 'dashboard', name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页' } },
      { path: 'knowledge', name: 'knowledge',
        component: () => import('@/views/KnowledgeQA.vue'),
        meta: { title: '知识库问答', skill: 'knowledge_qa' } },
      { path: 'hazards', name: 'hazards',
        component: () => import('@/views/HazardDetect.vue'),
        meta: { title: '隐患识别', skill: 'hazard_detect' } },
      { path: 'hazards/history', name: 'hazards-history',
        component: () => import('@/views/HazardHistory.vue'),
        meta: { title: '识别历史', skill: 'hazard_detect' } },
      { path: 'reports', name: 'reports-list',
        component: () => import('@/views/reports/ReportList.vue'),
        meta: { title: '报告列表', skill: 'report_gen' } },
      { path: 'reports/new', name: 'reports-new',
        component: () => import('@/views/reports/ReportGenerate.vue'),
        meta: { title: '生成报告', skill: 'report_gen' } },
      { path: 'reports/:id', name: 'reports-detail',
        component: () => import('@/views/reports/ReportDetail.vue'),
        meta: { title: '报告详情', skill: 'report_gen' } },
      { path: 'reports/trend/:lab', name: 'reports-trend',
        component: () => import('@/views/reports/ReportTrend.vue'),
        meta: { title: '趋势分析', skill: 'report_gen' } },
      { path: 'analytics', name: 'analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { title: '数据分析', skill: 'analytics', adminOnly: true } },
      { path: 'admin/users', name: 'admin-users',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', adminOnly: true } },
      { path: 'admin/permissions', name: 'admin-permissions',
        component: () => import('@/views/admin/SkillMatrix.vue'),
        meta: { title: 'Skill 权限', adminOnly: true } },
      { path: 'admin/knowledge', name: 'admin-knowledge',
        component: () => import('@/views/admin/KnowledgeManage.vue'),
        meta: { title: '知识库管理', adminOnly: true } },
      { path: 'admin/labs', name: 'admin-labs',
        component: () => import('@/views/admin/LabManage.vue'),
        meta: { title: '实验室管理', adminOnly: true } },
    ],
  },
  { path: '/:catchAll(.*)', redirect: '/agent' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.isLoggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (!auth.user) await auth.fetchMe()
  if (to.meta.adminOnly && auth.role !== 'admin') return '/agent'
  if (to.meta.skill && !auth.hasSkill(to.meta.skill as any)) return '/agent'
  return true
})

export default router
