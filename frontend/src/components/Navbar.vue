<template>
  <nav class="navbar">
    <div class="navbar-brand">
      <router-link to="/" class="logo">论坛</router-link>
    </div>
    <div class="navbar-menu">
      <div class="navbar-start">
        <router-link to="/" class="navbar-item">首页</router-link>
      </div>
      <div class="navbar-end">
        <template v-if="isAuthenticated">
          <!-- 管理员和版主可见的仪表盘链接 -->
          <router-link 
            v-if="isAdmin || isModerator" 
            to="/dashboard" 
            class="navbar-item"
          >
            仪表盘
          </router-link>
          <div class="navbar-item has-dropdown">
            <a class="navbar-link">{{ currentUser?.username }}</a>
            <div class="navbar-dropdown">
              <router-link :to="`/users/${currentUser?.id}`" class="dropdown-item">个人资料</router-link>
              <router-link :to="`/users/${currentUser?.id}/posts`" class="dropdown-item">我的帖子</router-link>
              <router-link :to="`/users/${currentUser?.id}/favorites`" class="dropdown-item">我的收藏</router-link>
              <hr class="dropdown-divider">
              <a class="dropdown-item" @click="handleLogout">退出登录</a>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="navbar-item">登录</router-link>
          <router-link to="/register" class="navbar-item">注册</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { UserRole } from '../types/user'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.currentUser)

// 检查用户是否是管理员
const isAdmin = computed(() => {
  return currentUser.value?.role === UserRole.ADMIN || 
         currentUser.value?.role === UserRole.SUPER_ADMIN
})

// 检查用户是否是版主
const isModerator = computed(() => {
  return currentUser.value?.role === UserRole.MODERATOR
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.logo {
  color: #3498db;
  text-decoration: none;
}

.navbar-menu {
  display: flex;
  justify-content: space-between;
  flex-grow: 1;
  margin-left: 1rem;
}

.navbar-start, .navbar-end {
  display: flex;
  align-items: center;
}

.navbar-item {
  padding: 0.5rem 1rem;
  color: #333;
  text-decoration: none;
}

.navbar-item:hover {
  color: #3498db;
}

.has-dropdown {
  position: relative;
}

.navbar-link {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.navbar-dropdown {
  display: none;
  position: absolute;
  right: 0;
  top: 100%;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  z-index: 20;
}

.has-dropdown:hover .navbar-dropdown {
  display: block;
}

.dropdown-item {
  display: block;
  padding: 0.75rem 1rem;
  color: #333;
  text-decoration: none;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
  color: #3498db;
}

.dropdown-divider {
  height: 1px;
  background-color: #e9ecef;
  margin: 0.5rem 0;
}
</style> 