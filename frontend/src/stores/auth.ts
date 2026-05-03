import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import type { UserInfo, Skill, Role } from '@/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as UserInfo | null,
    access: localStorage.getItem('access_token') || '',
  }),
  getters: {
    isLoggedIn: state => !!state.access,
    role: state => state.user?.role as Role | undefined,
    skills: state => (state.user?.skills || []) as Skill[],
    isAdmin: state => state.user?.role === 'admin',
  },
  actions: {
    async login(username: string, password: string) {
      const resp = await authApi.login(username, password)
      this.access = resp.access
      this.user = resp.user
      localStorage.setItem('access_token', resp.access)
      localStorage.setItem('refresh_token', resp.refresh)
    },
    async fetchMe() {
      try {
        const u = await authApi.me()
        this.user = u
      } catch {
        this.logout()
      }
    },
    logout() {
      this.user = null
      this.access = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
    hasSkill(skill: Skill) {
      return this.skills.includes(skill)
    },
  },
})
