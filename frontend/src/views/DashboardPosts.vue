<template>
  <DashboardLayout>
    <div class="posts-management">
      <div class="filters">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索帖子..." 
            @input="handleSearch"
          />
          <button class="search-btn">🔍</button>
        </div>
        
        <div class="filter-options">
          <select v-model="statusFilter" @change="applyFilters">
            <option value="all">所有状态</option>
            <option value="published">已发布</option>
            <option value="pending">待审核</option>
            <option value="reported">被举报</option>
            <option value="deleted">已删除</option>
          </select>
          
          <select v-model="categoryFilter" @change="applyFilters">
            <option value="all">所有分类</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
          
          <select v-model="sortBy" @change="applyFilters">
            <option value="newest">最新发布</option>
            <option value="oldest">最早发布</option>
            <option value="most_viewed">最多浏览</option>
            <option value="most_commented">最多评论</option>
          </select>
        </div>
      </div>
      
      <div class="posts-table-container">
        <table class="posts-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>作者</th>
              <th>分类</th>
              <th>状态</th>
              <th>发布时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="loading-cell">加载中...</td>
            </tr>
            <tr v-else-if="posts.length === 0">
              <td colspan="7" class="empty-cell">暂无帖子</td>
            </tr>
            <tr v-else v-for="post in posts" :key="post.id" :class="{ 'reported': post.status === 'reported' }">
              <td>{{ post.id }}</td>
              <td class="title-cell">
                <router-link :to="`/posts/${post.id}`">{{ post.title }}</router-link>
              </td>
              <td>{{ post.author }}</td>
              <td>{{ post.category }}</td>
              <td>
                <span class="status-badge" :class="post.status">
                  {{ getStatusText(post.status) }}
                </span>
              </td>
              <td>{{ formatDate(post.createdAt) }}</td>
              <td class="actions-cell">
                <button class="action-btn view" @click="viewPost(post)">查看</button>
                <button class="action-btn edit" @click="editPost(post)">编辑</button>
                <button 
                  v-if="post.status === 'pending'" 
                  class="action-btn approve" 
                  @click="approvePost(post)"
                >
                  批准
                </button>
                <button 
                  v-if="post.status === 'reported'" 
                  class="action-btn resolve" 
                  @click="resolveReport(post)"
                >
                  处理举报
                </button>
                <button 
                  v-if="post.status !== 'deleted'" 
                  class="action-btn delete" 
                  @click="deletePost(post)"
                >
                  删除
                </button>
                <button 
                  v-else
                  class="action-btn restore" 
                  @click="restorePost(post)"
                >
                  恢复
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
      
      <!-- 帖子详情模态框 -->
      <div v-if="showPostModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ selectedPost.title }}</h2>
            <button class="close-btn" @click="closeModal">×</button>
          </div>
          
          <div class="modal-body">
            <div class="post-info">
              <p><strong>作者:</strong> {{ selectedPost.author }}</p>
              <p><strong>分类:</strong> {{ selectedPost.category }}</p>
              <p><strong>发布时间:</strong> {{ formatDate(selectedPost.createdAt) }}</p>
              <p><strong>状态:</strong> {{ getStatusText(selectedPost.status) }}</p>
            </div>
            
            <div class="post-content">
              <h3>帖子内容</h3>
              <div v-html="selectedPost.content"></div>
            </div>
            
            <div v-if="selectedPost.status === 'reported'" class="report-info">
              <h3>举报信息</h3>
              <p><strong>举报原因:</strong> {{ selectedPost.reportReason }}</p>
              <p><strong>举报人:</strong> {{ selectedPost.reportedBy }}</p>
              <p><strong>举报时间:</strong> {{ formatDate(selectedPost.reportedAt) }}</p>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="action-btn edit" @click="editPost(selectedPost)">编辑</button>
            <button 
              v-if="selectedPost.status === 'pending'" 
              class="action-btn approve" 
              @click="approvePost(selectedPost)"
            >
              批准
            </button>
            <button 
              v-if="selectedPost.status === 'reported'" 
              class="action-btn resolve" 
              @click="resolveReport(selectedPost)"
            >
              处理举报
            </button>
            <button 
              v-if="selectedPost.status !== 'deleted'" 
              class="action-btn delete" 
              @click="deletePost(selectedPost)"
            >
              删除
            </button>
            <button 
              v-else
              class="action-btn restore" 
              @click="restorePost(selectedPost)"
            >
              恢复
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

const router = useRouter()

// 加载状态
const isLoading = ref(true)

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref('all')
const categoryFilter = ref('all')
const sortBy = ref('newest')

// 分页
const currentPage = ref(1)
const totalPages = ref(1)

// 模态框
const showPostModal = ref(false)
const selectedPost = ref({
  id: 0,
  title: '',
  author: '',
  category: '',
  status: '',
  content: '',
  createdAt: new Date(),
  reportReason: '',
  reportedBy: '',
  reportedAt: new Date()
})

// 分类列表
const categories = ref([
  { id: 1, name: '技术讨论' },
  { id: 2, name: '问题求助' },
  { id: 3, name: '经验分享' },
  { id: 4, name: '资源推荐' }
])

// 帖子列表
const posts = ref([
  {
    id: 1,
    title: 'Vue 3 最佳实践',
    author: '张三',
    category: '技术讨论',
    status: 'published',
    content: '<p>Vue 3 带来了许多新特性，包括 Composition API、Teleport、Fragments 等。</p><p>本文将分享一些使用 Vue 3 的最佳实践...</p>',
    createdAt: new Date(Date.now() - 86400000 * 2) // 2天前
  },
  {
    id: 2,
    title: '如何优化 React 应用性能',
    author: '李四',
    category: '经验分享',
    status: 'pending',
    content: '<p>React 应用性能优化是一个常见问题，本文将分享一些实用技巧...</p>',
    createdAt: new Date(Date.now() - 86400000) // 1天前
  },
  {
    id: 3,
    title: '不当内容测试',
    author: '王五',
    category: '问题求助',
    status: 'reported',
    content: '<p>这是一个测试帖子，包含一些不当内容...</p>',
    createdAt: new Date(Date.now() - 86400000 * 3), // 3天前
    reportReason: '包含不当内容',
    reportedBy: '赵六',
    reportedAt: new Date(Date.now() - 43200000) // 12小时前
  },
  {
    id: 4,
    title: '已删除的帖子',
    author: '赵六',
    category: '资源推荐',
    status: 'deleted',
    content: '<p>这是一个已删除的帖子...</p>',
    createdAt: new Date(Date.now() - 86400000 * 5) // 5天前
  }
])

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'published': return '已发布'
    case 'pending': return '待审核'
    case 'reported': return '被举报'
    case 'deleted': return '已删除'
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
      status: statusFilter.value,
      category: categoryFilter.value,
      sortBy: sortBy.value
    })
    
    // 在实际应用中，这里会根据筛选条件从API获取数据
    isLoading.value = false
  }, 500)
}

// 查看帖子
const viewPost = (post: any) => {
  selectedPost.value = { ...post }
  showPostModal.value = true
}

// 编辑帖子
const editPost = (post: any) => {
  // 实际应用中这里会跳转到编辑页面或打开编辑模态框
  console.log('编辑帖子:', post.id)
  closeModal()
}

// 批准帖子
const approvePost = (post: any) => {
  // 实际应用中这里会调用API
  console.log('批准帖子:', post.id)
  
  // 更新帖子状态
  const index = posts.value.findIndex(p => p.id === post.id)
  if (index !== -1) {
    posts.value[index].status = 'published'
  }
  
  closeModal()
}

// 处理举报
const resolveReport = (post: any) => {
  // 实际应用中这里会打开处理举报的模态框
  console.log('处理举报:', post.id)
  
  // 更新帖子状态
  const index = posts.value.findIndex(p => p.id === post.id)
  if (index !== -1) {
    posts.value[index].status = 'published'
  }
  
  closeModal()
}

// 删除帖子
const deletePost = (post: any) => {
  if (confirm(`确定要删除帖子 "${post.title}" 吗？`)) {
    // 实际应用中这里会调用API
    console.log('删除帖子:', post.id)
    
    // 更新帖子状态
    const index = posts.value.findIndex(p => p.id === post.id)
    if (index !== -1) {
      posts.value[index].status = 'deleted'
    }
    
    closeModal()
  }
}

// 恢复帖子
const restorePost = (post: any) => {
  // 实际应用中这里会调用API
  console.log('恢复帖子:', post.id)
  
  // 更新帖子状态
  const index = posts.value.findIndex(p => p.id === post.id)
  if (index !== -1) {
    posts.value[index].status = 'published'
  }
  
  closeModal()
}

// 关闭模态框
const closeModal = () => {
  showPostModal.value = false
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
    totalPages.value = 5 // 假设总共有5页
    isLoading.value = false
  }, 1000)
})
</script>

<style scoped>
.posts-management {
  display: flex;
  flex-direction: column;
  gap: 2rem;
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
  border-radius: 12px;
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

.posts-table-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
}

.posts-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.posts-table th {
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

.posts-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.posts-table tr:last-child td {
  border-bottom: none;
}

.posts-table tr:hover {
  background-color: #f8fafc;
}

.posts-table tr.reported {
  background-color: #fef2f2;
}

.posts-table tr.reported:hover {
  background-color: #fee2e2;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
  font-size: 1.1rem;
}

.title-cell a {
  color: #1e293b;
  text-decoration: none;
  font-weight: 500;
  display: block;
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.title-cell a:hover {
  color: #3498db;
}

.status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 2rem;
  font-size: 0.8rem;
  font-weight: 500;
  text-align: center;
  min-width: 80px;
}

.status-badge.published {
  background-color: #dcfce7;
  color: #166534;
}

.status-badge.pending {
  background-color: #fef9c3;
  color: #854d0e;
}

.status-badge.reported {
  background-color: #fee2e2;
  color: #b91c1c;
}

.status-badge.deleted {
  background-color: #f3f4f6;
  color: #4b5563;
}

.actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
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

.action-btn.approve {
  background-color: #dcfce7;
  color: #166534;
}

.action-btn.approve:hover {
  background-color: #bbf7d0;
}

.action-btn.resolve {
  background-color: #f3e8ff;
  color: #7e22ce;
}

.action-btn.resolve:hover {
  background-color: #e9d5ff;
}

.action-btn.delete {
  background-color: #fee2e2;
  color: #b91c1c;
}

.action-btn.delete:hover {
  background-color: #fecaca;
}

.action-btn.restore {
  background-color: #f3f4f6;
  color: #4b5563;
}

.action-btn.restore:hover {
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
  border-radius: 12px;
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
  font-weight: 600;
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

.post-info {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.post-info p {
  margin: 0.5rem 0;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.post-info p strong {
  color: #64748b;
  font-weight: 500;
  font-size: 0.85rem;
}

.post-content {
  margin-bottom: 2rem;
}

.post-content h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #334155;
  font-size: 1.25rem;
  font-weight: 600;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.post-content div {
  color: #1e293b;
  line-height: 1.6;
}

.report-info {
  background-color: #fef2f2;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.report-info h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #b91c1c;
  font-size: 1.1rem;
  font-weight: 600;
}

.report-info p {
  margin: 0.5rem 0;
  color: #334155;
}

.report-info p strong {
  color: #64748b;
  font-weight: 500;
  margin-right: 0.5rem;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #eee;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background-color: #f8fafc;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .filters {
    grid-template-columns: 1fr;
  }
  
  .post-info {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .filter-options {
    grid-template-columns: 1fr;
  }
}
</style> 