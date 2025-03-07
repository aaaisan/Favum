<template>
  <div class="dashboard-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>管理仪表盘</h2>
      </div>
      <nav class="sidebar-menu">
        <!-- 所有管理员和版主都可以看到的菜单项 -->
        <router-link to="/dashboard" class="menu-item" exact-active-class="active">
          <i class="icon">📊</i> 概览
        </router-link>
        
        <router-link to="/dashboard/posts" class="menu-item" active-class="active">
          <i class="icon">📝</i> 帖子管理
        </router-link>
        
        <!-- 只有管理员可以看到的菜单项 -->
        <template v-if="isAdmin">
          <router-link to="/dashboard/users" class="menu-item" active-class="active">
            <i class="icon">👥</i> 用户管理
          </router-link>
          
          <router-link to="/dashboard/categories" class="menu-item" active-class="active">
            <i class="icon">📂</i> 分类管理
          </router-link>
          
          <router-link to="/dashboard/tags" class="menu-item" active-class="active">
            <i class="icon">🏷️</i> 标签管理
          </router-link>
        </template>
        
        <!-- 返回主站 -->
        <router-link to="/" class="menu-item back-to-site">
          <i class="icon">🏠</i> 返回主站
        </router-link>
      </nav>
    </aside>
    
    <main class="dashboard-content">
      <div class="content-header">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <div class="user-info">
          <span>{{ currentUser?.username }}</span>
          <span class="role-badge" :class="roleClass">{{ roleDisplay }}</span>
        </div>
      </div>
      
      <div class="content-body">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { UserRole } from '../types/user'

const route = useRoute()
const authStore = useAuthStore()

const currentUser = computed(() => authStore.currentUser)

// 检查用户是否是管理员
const isAdmin = computed(() => {
  return currentUser.value?.role === UserRole.ADMIN || 
         currentUser.value?.role === UserRole.SUPER_ADMIN
})

// 根据路由获取页面标题
const pageTitle = computed(() => {
  const path = route.path
  if (path === '/dashboard') return '仪表盘概览'
  if (path === '/dashboard/posts') return '帖子管理'
  if (path === '/dashboard/users') return '用户管理'
  if (path === '/dashboard/categories') return '分类管理'
  if (path === '/dashboard/tags') return '标签管理'
  return '仪表盘'
})

// 获取用户角色显示文本
const roleDisplay = computed(() => {
  const role = currentUser.value?.role
  if (role === UserRole.ADMIN) return '管理员'
  if (role === UserRole.SUPER_ADMIN) return '超级管理员'
  if (role === UserRole.MODERATOR) return '版主'
  return '用户'
})

// 获取角色对应的CSS类
const roleClass = computed(() => {
  const role = currentUser.value?.role
  if (role === UserRole.ADMIN || role === UserRole.SUPER_ADMIN) return 'admin'
  if (role === UserRole.MODERATOR) return 'moderator'
  return 'user'
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: calc(100vh - 60px);
}

.sidebar {
  width: 250px;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #34495e;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  color: #ecf0f1;
  text-decoration: none;
  transition: background-color 0.3s;
}

.menu-item:hover {
  background-color: #34495e;
}

.menu-item.active {
  background-color: #3498db;
  color: white;
}

.icon {
  margin-right: 0.75rem;
  font-size: 1.25rem;
}

.back-to-site {
  margin-top: auto;
  border-top: 1px solid #34495e;
  padding-top: 1rem;
}

.dashboard-content {
  flex: 1;
  background-color: #f8f9fa;
  overflow-y: auto;
}

.content-header {
  background-color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.role-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
}

.role-badge.admin {
  background-color: #e74c3c;
  color: white;
}

.role-badge.moderator {
  background-color: #f39c12;
  color: white;
}

.role-badge.user {
  background-color: #3498db;
  color: white;
}

.content-body {
  padding: 2rem;
}
</style> 