<template>
  <div class="user-list-container">
    <h1>用户管理</h1>
    
    <div class="filters">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索用户名或邮箱" 
          @input="handleSearch"
        />
        <button 
          v-if="searchQuery" 
          @click="clearSearch" 
          class="clear-search"
        >
          ✕
        </button>
      </div>
    </div>
    
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="errorMessage" class="error-message">
      <i class="error-icon">!</i>
      <p>{{ errorMessage }}</p>
    </div>
    
    <div v-else-if="users.length === 0" class="empty-message">
      <p>没有找到用户</p>
      <small v-if="searchQuery">尝试使用不同的搜索条件</small>
    </div>
    
    <table v-else class="users-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名</th>
          <th>邮箱</th>
          <th>角色</th>
          <th>注册时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id" :class="{ 'deleted': user.is_deleted }">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span class="role-badge" :class="getRoleBadgeClass(user.role)">
              {{ formatRole(user.role) }}
            </span>
          </td>
          <td>{{ formatDate(user.created_at) }}</td>
          <td>
            <span v-if="user.is_deleted" class="status-badge deleted">已删除</span>
            <span v-else-if="user.is_active" class="status-badge active">活跃</span>
            <span v-else class="status-badge inactive">未激活</span>
          </td>
          <td class="actions">
            <button @click="viewUser(user.id!)" class="btn-view" title="查看用户详情">
              查看
            </button>
            <button 
              v-if="!user.is_deleted" 
              @click="deleteUser(user.id!)" 
              class="btn-delete"
              :title="`删除用户 ${user.username}`"
            >
              删除
            </button>
            <button 
              v-else 
              @click="restoreUser(user.id!)" 
              class="btn-restore"
              :title="`恢复用户 ${user.username}`"
            >
              恢复
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <div v-if="users.length > 0" class="pagination">
      <button 
        :disabled="page === 1" 
        @click="changePage(page - 1)" 
        class="btn-pagination"
      >
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} 页 / 共 {{ Math.ceil(totalUsers / pageSize) || 1 }} 页
        ({{ totalUsers }} 个用户)
      </span>
      <button 
        :disabled="users.length < pageSize || page * pageSize >= totalUsers" 
        @click="changePage(page + 1)" 
        class="btn-pagination"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate } from '../utils/format'
import { formatRole, getRoleBadgeClass } from '../utils/roles'
import { useUserList } from '../composables/useUserList'
import type { User } from '../types'

const router = useRouter()

// 使用用户列表组合式函数
const {
  searchQuery,
  page,
  pageSize,
  users,
  isLoading,
  errorMessage,
  totalUsers,
  handleSearch,
  changePage,
  fetchUsers,
  deleteUser,
  restoreUser
} = useUserList()

// 查看用户详情
const viewUser = (userId: number) => {
  router.push(`/users/${userId}`)
}

/**
 * 清除搜索内容
 */
const clearSearch = () => {
  searchQuery.value = '';
  handleSearch();
}

onMounted(fetchUsers)
</script>

<style scoped>
.user-list-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filters {
  margin-bottom: 20px;
}

.search-box {
  position: relative;
  display: inline-block;
}

input {
  padding: 10px 12px;
  width: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

input:focus {
  border-color: #3498db;
  outline: none;
}

.clear-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 14px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s;
}

.clear-search:hover {
  color: #333;
}

.loading, .error-message, .empty-message {
  text-align: center;
  padding: 40px;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3498db;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: #e74c3c;
  color: white;
  border-radius: 50%;
  font-style: normal;
  font-weight: bold;
  font-size: 20px;
  margin-bottom: 10px;
}

.error-message {
  color: #e74c3c;
}

.empty-message small {
  margin-top: 8px;
  color: #999;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.users-table th, .users-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.users-table th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #333;
  position: sticky;
  top: 0;
}

.users-table tr:hover {
  background-color: #f5f5f5;
}

.users-table tr.deleted {
  color: #999;
  background-color: #f8f8f8;
}

.role-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background-color: #3498db;
  color: white;
}

.role-badge.super-admin {
  background-color: #9b59b6;
  color: white;
}

.role-badge.moderator {
  background-color: #f39c12;
  color: white;
}

.role-badge.user {
  background-color: #7f8c8d;
  color: white;
}

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background-color: #2ecc71;
  color: white;
}

.status-badge.inactive {
  background-color: #95a5a6;
  color: white;
}

.status-badge.deleted {
  background-color: #e74c3c;
  color: white;
}

.actions {
  display: flex;
  gap: 8px;
}

button {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s, opacity 0.3s;
}

.btn-view {
  background-color: #3498db;
  color: white;
}

.btn-delete {
  background-color: #e74c3c;
  color: white;
}

.btn-restore {
  background-color: #2ecc71;
  color: white;
}

.btn-pagination {
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  color: #333;
  transition: background-color 0.3s;
}

.btn-pagination:hover:not(:disabled) {
  background-color: #e9ecef;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.page-info {
  font-size: 14px;
  color: #666;
}

@media (max-width: 768px) {
  .user-list-container {
    padding: 10px;
  }
  
  .users-table {
    font-size: 14px;
  }
  
  .users-table th, .users-table td {
    padding: 8px;
  }
  
  input {
    width: 100%;
  }
}
</style> 