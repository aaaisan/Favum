<template>
  <DashboardLayout>
    <div class="users-management">
      <div class="filters">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索用户..." 
            @input="handleSearch"
          />
          <button class="search-btn">🔍</button>
        </div>
        
        <div class="filter-options">
          <select v-model="roleFilter" @change="applyFilters">
            <option value="all">所有角色</option>
            <option value="user">普通用户</option>
            <option value="moderator">版主</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>
          
          <select v-model="statusFilter" @change="applyFilters">
            <option value="all">所有状态</option>
            <option value="active">活跃</option>
            <option value="inactive">非活跃</option>
            <option value="banned">已封禁</option>
          </select>
          
          <select v-model="sortBy" @change="applyFilters">
            <option value="newest">最新注册</option>
            <option value="oldest">最早注册</option>
            <option value="username">用户名</option>
            <option value="posts">帖子数量</option>
          </select>
        </div>
      </div>
      
      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="users.length === 0">
              <td colspan="7" class="empty-cell">暂无用户</td>
            </tr>
            <tr v-else v-for="user in users" :key="user.id" :class="{ 'banned': user.status === 'banned' }">
              <td>{{ user.id }}</td>
              <td class="username-cell">
                <div class="user-info">
                  <img v-if="user.avatar_url" :src="user.avatar_url" alt="头像" class="user-avatar" />
                  <div v-else class="user-avatar placeholder">{{ getUserInitials(user.username) }}</div>
                  <span>{{ user.username }}</span>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <span class="role-badge" :class="user.role">
                  {{ getRoleText(user.role) }}
                </span>
              </td>
              <td>
                <span class="status-badge" :class="user.status">
                  {{ getStatusText(user.status) }}
                </span>
              </td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td class="actions-cell">
                <button class="action-btn view" @click="viewUser(user)">查看</button>
                <button class="action-btn edit" @click="editUser(user)">编辑</button>
                <button 
                  v-if="user.status !== 'banned'" 
                  class="action-btn ban" 
                  @click="banUser(user)"
                >
                  封禁
                </button>
                <button 
                  v-else
                  class="action-btn unban" 
                  @click="unbanUser(user)"
                >
                  解封
                </button>
                <button 
                  v-if="user.role === 'user'"
                  class="action-btn promote" 
                  @click="promoteModerator(user)"
                >
                  设为版主
                </button>
                <button 
                  v-if="user.role === 'moderator'"
                  class="action-btn demote" 
                  @click="demoteModerator(user)"
                >
                  取消版主
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="pagination">
        <button 
          class="pagination-btn" 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        
        <div class="page-info">
          第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </div>
        
        <button 
          class="pagination-btn" 
          :disabled="currentPage === totalPages" 
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
      
      <!-- 用户详情模态框 -->
      <div v-if="showUserModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ selectedUser.username }}</h2>
            <button class="close-btn" @click="closeModal">×</button>
          </div>
          
          <div class="modal-body">
            <div class="user-profile">
              <div class="user-header">
                <div v-if="selectedUser.avatar_url" class="user-avatar large">
                  <img :src="selectedUser.avatar_url" alt="头像" />
                </div>
                <div v-else class="user-avatar large placeholder">
                  {{ getUserInitials(selectedUser.username) }}
                </div>
                <div class="user-basic-info">
                  <h3>{{ selectedUser.username }}</h3>
                  <p><strong>邮箱:</strong> {{ selectedUser.email }}</p>
                  <p><strong>角色:</strong> {{ getRoleText(selectedUser.role) }}</p>
                  <p><strong>状态:</strong> {{ getStatusText(selectedUser.status) }}</p>
                  <p><strong>注册时间:</strong> {{ formatDate(selectedUser.created_at) }}</p>
                </div>
              </div>
              
              <div class="user-stats">
                <div class="stat-item">
                  <h4>帖子</h4>
                  <p>{{ selectedUser.post_count || 0 }}</p>
                </div>
                <div class="stat-item">
                  <h4>评论</h4>
                  <p>{{ selectedUser.comment_count || 0 }}</p>
                </div>
                <div class="stat-item">
                  <h4>声望</h4>
                  <p>{{ selectedUser.reputation || 0 }}</p>
                </div>
                <div class="stat-item">
                  <h4>最后登录</h4>
                  <p>{{ selectedUser.last_login ? formatDate(selectedUser.last_login) : '从未登录' }}</p>
                </div>
              </div>
              
              <div class="user-bio">
                <h4>个人简介</h4>
                <p v-if="selectedUser.bio">{{ selectedUser.bio }}</p>
                <p v-else class="empty-text">用户未设置个人简介</p>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="action-btn edit" @click="editUser(selectedUser)">编辑</button>
            <button 
              v-if="selectedUser.status !== 'banned'" 
              class="action-btn ban" 
              @click="banUser(selectedUser)"
            >
              封禁
            </button>
            <button 
              v-else
              class="action-btn unban" 
              @click="unbanUser(selectedUser)"
            >
              解封
            </button>
            <button 
              v-if="selectedUser.role === 'user'"
              class="action-btn promote" 
              @click="promoteModerator(selectedUser)"
            >
              设为版主
            </button>
            <button 
              v-if="selectedUser.role === 'moderator'"
              class="action-btn demote" 
              @click="demoteModerator(selectedUser)"
            >
              取消版主
            </button>
            <button class="action-btn cancel" @click="closeModal">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '../components/DashboardLayout.vue'
import { UserRole } from '../types/user'

const router = useRouter()

// 加载状态
const isLoading = ref(true)

// 搜索和筛选
const searchQuery = ref('')
const roleFilter = ref('all')
const statusFilter = ref('all')
const sortBy = ref('newest')

// 分页
const currentPage = ref(1)
const totalPages = ref(1)

// 模态框
const showUserModal = ref(false)
const selectedUser = ref({
  id: 0,
  username: '',
  email: '',
  role: '',
  status: '',
  bio: '',
  avatar_url: '',
  created_at: new Date(),
  post_count: 0,
  comment_count: 0,
  reputation: 0,
  last_login: null as Date | null
})

// 用户列表
const users = ref([
  {
    id: 1,
    username: '张三',
    email: 'zhangsan@example.com',
    role: 'admin',
    status: 'active',
    bio: '管理员账号',
    avatar_url: null,
    created_at: new Date(Date.now() - 86400000 * 30), // 30天前
    post_count: 15,
    comment_count: 45,
    reputation: 120,
    last_login: new Date(Date.now() - 86400000)
  },
  {
    id: 2,
    username: '李四',
    email: 'lisi@example.com',
    role: 'moderator',
    status: 'active',
    bio: '版主账号',
    avatar_url: null,
    created_at: new Date(Date.now() - 86400000 * 25), // 25天前
    post_count: 10,
    comment_count: 32,
    reputation: 85,
    last_login: new Date(Date.now() - 172800000)
  },
  {
    id: 3,
    username: '王五',
    email: 'wangwu@example.com',
    role: 'user',
    status: 'banned',
    bio: '普通用户',
    avatar_url: null,
    created_at: new Date(Date.now() - 86400000 * 20), // 20天前
    post_count: 5,
    comment_count: 12,
    reputation: 25,
    last_login: new Date(Date.now() - 432000000)
  },
  {
    id: 4,
    username: '赵六',
    email: 'zhaoliu@example.com',
    role: 'user',
    status: 'active',
    bio: '普通用户',
    avatar_url: null,
    created_at: new Date(Date.now() - 86400000 * 15), // 15天前
    post_count: 8,
    comment_count: 23,
    reputation: 42,
    last_login: new Date(Date.now() - 259200000)
  }
])

// 获取用户名首字母
const getUserInitials = (username: string) => {
  if (!username) return '?'
  return username.charAt(0).toUpperCase()
}

// 获取角色文本
const getRoleText = (role: string) => {
  switch (role) {
    case UserRole.ADMIN: return '管理员'
    case UserRole.SUPER_ADMIN: return '超级管理员'
    case UserRole.MODERATOR: return '版主'
    case UserRole.USER: return '普通用户'
    default: return '未知'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'inactive': return '非活跃'
    case 'banned': return '已封禁'
    default: return '未知'
  }
}

// 格式化日期
const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 搜索处理
const handleSearch = () => {
  // 实际应用中这里会调用API
  console.log('搜索:', searchQuery.value)
  applyFilters()
}

// 应用筛选
const applyFilters = () => {
  isLoading.value = true
  
  // 模拟API请求
  setTimeout(() => {
    console.log('应用筛选:', {
      role: roleFilter.value,
      status: statusFilter.value,
      sortBy: sortBy.value
    })
    
    // 在实际应用中，这里会根据筛选条件从API获取数据
    isLoading.value = false
  }, 500)
}

// 查看用户
const viewUser = (user: any) => {
  selectedUser.value = { ...user }
  showUserModal.value = true
}

// 编辑用户
const editUser = (user: any) => {
  // 实际应用中这里会跳转到编辑页面或打开编辑模态框
  console.log('编辑用户:', user.id)
  closeModal()
}

// 封禁用户
const banUser = (user: any) => {
  if (confirm(`确定要封禁用户 "${user.username}" 吗？`)) {
    // 实际应用中这里会调用API
    console.log('封禁用户:', user.id)
    
    // 更新用户状态
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].status = 'banned'
      if (selectedUser.value.id === user.id) {
        selectedUser.value.status = 'banned'
      }
    }
  }
}

// 解封用户
const unbanUser = (user: any) => {
  // 实际应用中这里会调用API
  console.log('解封用户:', user.id)
  
  // 更新用户状态
  const index = users.value.findIndex(u => u.id === user.id)
  if (index !== -1) {
    users.value[index].status = 'active'
    if (selectedUser.value.id === user.id) {
      selectedUser.value.status = 'active'
    }
  }
}

// 提升为版主
const promoteModerator = (user: any) => {
  if (confirm(`确定要将用户 "${user.username}" 提升为版主吗？`)) {
    // 实际应用中这里会调用API
    console.log('提升为版主:', user.id)
    
    // 更新用户角色
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].role = 'moderator'
      if (selectedUser.value.id === user.id) {
        selectedUser.value.role = 'moderator'
      }
    }
  }
}

// 取消版主
const demoteModerator = (user: any) => {
  if (confirm(`确定要取消用户 "${user.username}" 的版主权限吗？`)) {
    // 实际应用中这里会调用API
    console.log('取消版主:', user.id)
    
    // 更新用户角色
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].role = 'user'
      if (selectedUser.value.id === user.id) {
        selectedUser.value.role = 'user'
      }
    }
  }
}

// 关闭模态框
const closeModal = () => {
  showUserModal.value = false
}

// 切换页面
const changePage = (page: number) => {
  currentPage.value = page
  
  // 实际应用中这里会调用API获取对应页的数据
  console.log('切换到页面:', page)
}

// 组件挂载时加载数据
onMounted(() => {
  // 模拟API请求
  setTimeout(() => {
    totalPages.value = 3 // 假设总共有3页
    isLoading.value = false
  }, 1000)
})
</script>

<style scoped>
.users-management {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

.filters {
  display: grid;
  grid-template-columns: minmax(250px, 1fr) 2fr;
  gap: 1.5rem;
  align-items: center;
  background-color: white;
  padding: 1.25rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-box {
  position: relative;
  width: 100%;
}

.search-box input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box input:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
  outline: none;
}

.search-btn {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #7f8c8d;
  font-size: 1rem;
  cursor: pointer;
}

.filter-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.filter-options select {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: white;
  width: 100%;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.filter-options select:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
  outline: none;
}

.users-table-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
}

.users-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.users-table th {
  position: sticky;
  top: 0;
  background-color: #f8f9fa;
  z-index: 10;
  padding: 1rem 1.5rem;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #eee;
  white-space: nowrap;
}

.users-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.users-table tr:last-child td {
  border-bottom: none;
}

.users-table tr:hover {
  background-color: #f8fafc;
}

.users-table tr.banned {
  background-color: #fef2f2;
}

.users-table tr.banned:hover {
  background-color: #fee2e2;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
  font-size: 1.1rem;
}

.username-cell {
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar.large {
  width: 100px;
  height: 100px;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar.placeholder {
  background-color: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
}

.user-avatar.large.placeholder {
  font-size: 2.5rem;
}

.role-badge, .status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 2rem;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  min-width: 80px;
}

.role-badge.admin, .role-badge.super_admin {
  background-color: #fee2e2;
  color: #b91c1c;
}

.role-badge.moderator {
  background-color: #fff7ed;
  color: #c2410c;
}

.role-badge.user {
  background-color: #eff6ff;
  color: #1d4ed8;
}

.status-badge.active {
  background-color: #ecfdf5;
  color: #047857;
}

.status-badge.inactive {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-badge.banned {
  background-color: #fef2f2;
  color: #b91c1c;
}

.actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.action-btn {
  padding: 0.4rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.view {
  background-color: #e0f2fe;
  color: #0369a1;
}

.action-btn.view:hover {
  background-color: #bae6fd;
}

.action-btn.edit {
  background-color: #fef9c3;
  color: #854d0e;
}

.action-btn.edit:hover {
  background-color: #fef08a;
}

.action-btn.ban {
  background-color: #fee2e2;
  color: #b91c1c;
}

.action-btn.ban:hover {
  background-color: #fecaca;
}

.action-btn.unban {
  background-color: #dcfce7;
  color: #166534;
}

.action-btn.unban:hover {
  background-color: #bbf7d0;
}

.action-btn.promote {
  background-color: #f3e8ff;
  color: #7e22ce;
}

.action-btn.promote:hover {
  background-color: #e9d5ff;
}

.action-btn.demote {
  background-color: #f3f4f6;
  color: #4b5563;
}

.action-btn.demote:hover {
  background-color: #e5e7eb;
}

.action-btn.cancel {
  background-color: #f3f4f6;
  color: #4b5563;
}

.action-btn.cancel:hover {
  background-color: #e5e7eb;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-btn {
  padding: 0.6rem 1.2rem;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #dbeafe;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #dbeafe;
}

.pagination-btn:disabled {
  background-color: #f3f4f6;
  border-color: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.9rem;
  color: #4b5563;
}

/* Modal styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background-color: white;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  animation: modal-fade-in 0.3s ease-out;
}

@keyframes modal-fade-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  transition: color 0.2s;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  color: #334155;
  background-color: #f8fafc;
}

.modal-body {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
}

.user-profile {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.user-header {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2rem;
  align-items: start;
}

.user-basic-info {
  display: grid;
  gap: 0.5rem;
}

.user-basic-info h3 {
  margin-top: 0;
  font-size: 1.75rem;
  color: #1e293b;
}

.user-basic-info p {
  margin: 0.25rem 0;
  color: #64748b;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.user-basic-info p strong {
  color: #334155;
  min-width: 100px;
  display: inline-block;
}

.user-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.stat-item h4 {
  margin: 0;
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 500;
}

.stat-item p {
  margin: 0.5rem 0 0;
  font-size: 1.75rem;
  font-weight: bold;
  color: #1e293b;
}

.user-bio {
  background-color: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
}

.user-bio h4 {
  margin-top: 0;
  color: #334155;
  font-size: 1.1rem;
}

.user-bio p {
  margin: 0.75rem 0 0;
  color: #1e293b;
  line-height: 1.6;
}

.empty-text {
  color: #94a3b8;
  font-style: italic;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #eee;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .filters {
    grid-template-columns: 1fr;
  }
  
  .user-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .filter-options {
    grid-template-columns: 1fr;
  }
  
  .user-header {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }
  
  .user-basic-info p {
    justify-content: center;
  }
}
</style> 