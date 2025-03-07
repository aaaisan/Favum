<template>
  <DashboardLayout>
    <div class="tags-management">
      <div class="top-section">
        <div class="header-actions">
          <h1>标签管理</h1>
          <button class="primary-btn" @click="openAddModal">
            <i class="icon">➕</i> 添加标签
          </button>
        </div>
        
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-value">{{ tags.length }}</div>
            <div class="stat-label">总标签数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ totalPostsWithTags }}</div>
            <div class="stat-label">已标记帖子</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ mostPopularTag ? mostPopularTag.name : '无' }}</div>
            <div class="stat-label">最热门标签</div>
          </div>
        </div>
      </div>
      
      <div class="search-section">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索标签..." 
            @input="handleSearch"
          />
          <button class="search-btn">🔍</button>
        </div>
      </div>
      
      <div class="tags-container">
        <div v-if="isLoading" class="loading">加载中...</div>
        <div v-else-if="filteredTags.length === 0 && searchQuery" class="empty-state">
          没有找到匹配"{{ searchQuery }}"的标签
        </div>
        <div v-else-if="tags.length === 0" class="empty-state">
          暂无标签，点击"添加标签"按钮创建第一个标签
        </div>
        <div v-else class="tags-grid">
          <div v-for="tag in filteredTags" :key="tag.id" class="tag-card">
            <div class="tag-header">
              <div class="tag-name" :style="{ backgroundColor: tag.color || '#3498db' }">
                {{ tag.name }}
              </div>
              <div class="tag-count">{{ tag.post_count }} 篇帖子</div>
            </div>
            
            <div class="tag-meta">
              <div class="tag-description">
                <p v-if="tag.description">{{ tag.description }}</p>
                <p v-else class="no-description">无描述</p>
              </div>
              <div class="tag-dates">
                <div class="date-item">
                  <span class="date-label">创建时间:</span>
                  <span class="date-value">{{ formatDate(tag.created_at) }}</span>
                </div>
                <div class="date-item">
                  <span class="date-label">最后使用:</span>
                  <span class="date-value">{{ tag.last_used ? formatDate(tag.last_used) : '从未' }}</span>
                </div>
              </div>
            </div>
            
            <div class="tag-actions">
              <button class="action-btn edit" @click="editTag(tag)">编辑</button>
              <button class="action-btn merge" @click="openMergeModal(tag)">合并</button>
              <button class="action-btn delete" @click="deleteTag(tag)">删除</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 添加/编辑标签模态框 -->
      <div v-if="showTagModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ isEditing ? '编辑标签' : '添加标签' }}</h2>
            <button class="close-btn" @click="closeModal">×</button>
          </div>
          
          <div class="modal-body">
            <form class="tag-form" @submit.prevent="saveTag">
              <div class="form-group">
                <label for="tag-name">标签名称 <span class="required">*</span></label>
                <input
                  id="tag-name"
                  v-model="tagForm.name"
                  type="text"
                  required
                  placeholder="输入标签名称"
                  maxlength="30"
                />
                <div v-if="formErrors.name" class="error-text">{{ formErrors.name }}</div>
              </div>
              
              <div class="form-group">
                <label for="tag-description">标签描述</label>
                <textarea
                  id="tag-description"
                  v-model="tagForm.description"
                  placeholder="输入标签描述"
                  rows="3"
                  maxlength="200"
                ></textarea>
              </div>
              
              <div class="form-group">
                <label for="tag-color">标签颜色</label>
                <div class="color-selector">
                  <input
                    id="tag-color"
                    v-model="tagForm.color"
                    type="color"
                  />
                  <span class="color-value">{{ tagForm.color }}</span>
                </div>
              </div>
            </form>
          </div>
          
          <div class="modal-footer">
            <button class="cancel-btn" @click="closeModal">取消</button>
            <button class="submit-btn" @click="saveTag">保存</button>
          </div>
        </div>
      </div>
      
      <!-- 合并标签模态框 -->
      <div v-if="showMergeModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>合并标签</h2>
            <button class="close-btn" @click="closeMergeModal">×</button>
          </div>
          
          <div class="modal-body">
            <div class="merge-info">
              <p>合并标签会将所有使用"<strong>{{ selectedTag.name }}</strong>"标签的帖子改为使用你选择的目标标签，并删除原标签。</p>
              <p class="warning">⚠️ 此操作无法撤销。</p>
            </div>
            
            <div class="form-group">
              <label for="target-tag">目标标签 <span class="required">*</span></label>
              <select
                id="target-tag"
                v-model="mergeForm.targetId"
                required
              >
                <option value="" disabled>选择目标标签</option>
                <option 
                  v-for="tag in tags.filter(t => t.id !== selectedTag.id)" 
                  :key="tag.id" 
                  :value="tag.id"
                >
                  {{ tag.name }} ({{ tag.post_count }} 篇帖子)
                </option>
              </select>
              <div v-if="formErrors.targetId" class="error-text">{{ formErrors.targetId }}</div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="cancel-btn" @click="closeMergeModal">取消</button>
            <button class="submit-btn danger" @click="mergeTag">合并标签</button>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import DashboardLayout from '../components/DashboardLayout.vue'

// 加载状态
const isLoading = ref(true)

// 搜索
const searchQuery = ref('')

// 标签列表
const tags = ref([
  {
    id: 1,
    name: 'JavaScript',
    description: '与 JavaScript 编程语言相关的问题和讨论',
    color: '#f7df1e',
    created_at: new Date(Date.now() - 86400000 * 30), // 30天前
    last_used: new Date(Date.now() - 86400000 * 2), // 2天前
    post_count: 42
  },
  {
    id: 2,
    name: 'Vue.js',
    description: '关于 Vue.js 框架的问题、教程和讨论',
    color: '#4fc08d',
    created_at: new Date(Date.now() - 86400000 * 25), // 25天前
    last_used: new Date(Date.now() - 86400000), // 1天前
    post_count: 38
  },
  {
    id: 3,
    name: 'React',
    description: '关于 React 库的问题和讨论',
    color: '#61dafb',
    created_at: new Date(Date.now() - 86400000 * 20), // 20天前
    last_used: new Date(Date.now() - 86400000 * 3), // 3天前
    post_count: 27
  },
  {
    id: 4,
    name: 'CSS',
    description: '关于 CSS 样式和布局的问题',
    color: '#264de4',
    created_at: new Date(Date.now() - 86400000 * 15), // 15天前
    last_used: new Date(Date.now() - 86400000 * 4), // 4天前
    post_count: 23
  },
  {
    id: 5,
    name: '前端',
    description: '前端开发相关的讨论',
    color: '#e34c26',
    created_at: new Date(Date.now() - 86400000 * 10), // 10天前
    last_used: new Date(Date.now() - 86400000 * 5), // 5天前
    post_count: 19
  }
])

// 筛选后的标签
const filteredTags = computed(() => {
  if (!searchQuery.value) return tags.value
  
  const query = searchQuery.value.toLowerCase()
  return tags.value.filter(tag => 
    tag.name.toLowerCase().includes(query) || 
    (tag.description && tag.description.toLowerCase().includes(query))
  )
})

// 总帖子数
const totalPostsWithTags = computed(() => {
  return tags.value.reduce((sum, tag) => sum + tag.post_count, 0)
})

// 最热门标签
const mostPopularTag = computed(() => {
  if (tags.value.length === 0) return null
  return [...tags.value].sort((a, b) => b.post_count - a.post_count)[0]
})

// 模态框状态
const showTagModal = ref(false)
const showMergeModal = ref(false)
const isEditing = ref(false)

// 标签表单
const tagForm = reactive({
  id: 0,
  name: '',
  description: '',
  color: '#3498db'
})

// 合并表单
const mergeForm = reactive({
  targetId: ''
})

// 表单错误
const formErrors = reactive({
  name: '',
  targetId: ''
})

// 选中的标签
const selectedTag = reactive({
  id: 0,
  name: '',
  description: '',
  color: '',
  created_at: new Date(),
  last_used: null as Date | null,
  post_count: 0
})

// 格式化日期
const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 搜索处理
const handleSearch = () => {
  // 实际应用中这里可能会调用API
  console.log('搜索:', searchQuery.value)
}

// 打开添加标签模态框
const openAddModal = () => {
  isEditing.value = false
  resetForm()
  showTagModal.value = true
}

// 编辑标签
const editTag = (tag: any) => {
  isEditing.value = true
  
  // 复制标签数据到表单
  tagForm.id = tag.id
  tagForm.name = tag.name
  tagForm.description = tag.description || ''
  tagForm.color = tag.color || '#3498db'
  
  showTagModal.value = true
}

// 打开合并模态框
const openMergeModal = (tag: any) => {
  // 复制标签数据
  selectedTag.id = tag.id
  selectedTag.name = tag.name
  selectedTag.description = tag.description || ''
  selectedTag.color = tag.color || '#3498db'
  selectedTag.created_at = tag.created_at
  selectedTag.last_used = tag.last_used
  selectedTag.post_count = tag.post_count
  
  // 重置合并表单
  mergeForm.targetId = ''
  formErrors.targetId = ''
  
  showMergeModal.value = true
}

// 删除标签
const deleteTag = (tag: any) => {
  if (confirm(`确定要删除标签 "${tag.name}" 吗？\n该标签将从所有帖子中移除。`)) {
    // 实际应用中这里会调用API
    console.log('删除标签:', tag.id)
    
    // 从列表中删除
    tags.value = tags.value.filter(t => t.id !== tag.id)
  }
}

// 保存标签
const saveTag = () => {
  // 重置错误
  formErrors.name = ''
  
  // 表单验证
  let isValid = true
  
  if (!tagForm.name.trim()) {
    formErrors.name = '标签名称不能为空'
    isValid = false
  }
  
  if (!isValid) return
  
  // 实际应用中这里会调用API
  if (isEditing.value) {
    console.log('更新标签:', tagForm)
    
    // 更新列表中的标签
    const index = tags.value.findIndex(t => t.id === tagForm.id)
    if (index !== -1) {
      tags.value[index] = {
        ...tags.value[index],
        name: tagForm.name,
        description: tagForm.description,
        color: tagForm.color
      }
    }
  } else {
    console.log('添加标签:', tagForm)
    
    // 添加到列表
    tags.value.push({
      id: Math.max(0, ...tags.value.map(t => t.id)) + 1,
      name: tagForm.name,
      description: tagForm.description,
      color: tagForm.color,
      created_at: new Date(),
      last_used: null as Date | null,
      post_count: 0
    })
  }
  
  closeModal()
}

// 合并标签
const mergeTag = () => {
  // 重置错误
  formErrors.targetId = ''
  
  // 表单验证
  if (!mergeForm.targetId) {
    formErrors.targetId = '请选择目标标签'
    return
  }
  
  const targetId = parseInt(mergeForm.targetId as string)
  const targetTag = tags.value.find(t => t.id === targetId)
  
  if (!targetTag) {
    formErrors.targetId = '目标标签无效'
    return
  }
  
  // 实际应用中这里会调用API
  console.log('合并标签:', {
    sourceId: selectedTag.id,
    targetId: targetId
  })
  
  // 更新目标标签的帖子数
  const targetIndex = tags.value.findIndex(t => t.id === targetId)
  if (targetIndex !== -1) {
    tags.value[targetIndex].post_count += selectedTag.post_count
  }
  
  // 从列表中删除源标签
  tags.value = tags.value.filter(t => t.id !== selectedTag.id)
  
  closeMergeModal()
}

// 重置表单
const resetForm = () => {
  tagForm.id = 0
  tagForm.name = ''
  tagForm.description = ''
  tagForm.color = '#3498db'
  
  formErrors.name = ''
}

// 关闭模态框
const closeModal = () => {
  showTagModal.value = false
}

// 关闭合并模态框
const closeMergeModal = () => {
  showMergeModal.value = false
}

// 组件挂载时加载数据
onMounted(() => {
  // 模拟API请求
  setTimeout(() => {
    isLoading.value = false
  }, 1000)
})
</script>

<style scoped>
.tags-management {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

.top-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions h1 {
  margin: 0;
  font-size: 1.75rem;
  color: #1e293b;
  font-weight: 600;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.primary-btn:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.primary-btn:active {
  transform: translateY(0);
}

.icon {
  font-size: 1rem;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.stat-card {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
  line-height: 1;
}

.stat-label {
  font-size: 0.95rem;
  color: #64748b;
  font-weight: 500;
}

.search-section {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.search-box {
  position: relative;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.search-box input {
  width: 100%;
  padding: 0.9rem 1rem 0.9rem 3rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
  outline: none;
}

.search-btn {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.2rem;
  cursor: pointer;
}

.tags-container {
  background-color: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.loading, .empty-state {
  text-align: center;
  padding: 6rem 2rem;
  color: #64748b;
  font-size: 1.1rem;
}

.empty-state {
  font-style: italic;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.empty-state::before {
  content: '🏷️';
  font-size: 3rem;
  color: #94a3b8;
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.tag-card {
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
  height: 100%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tag-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  border-color: #cbd5e1;
}

.tag-header {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.tag-name {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-count {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
}

.tag-meta {
  padding: 0 1.5rem 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.tag-description {
  min-height: 3rem;
}

.tag-description p {
  margin: 0;
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.6;
}

.no-description {
  color: #94a3b8;
  font-style: italic;
}

.tag-dates {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.date-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.date-label {
  color: #64748b;
  min-width: 5.5rem;
}

.date-value {
  color: #334155;
  font-weight: 500;
}

.tag-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background-color: #f8fafc;
  border-top: 1px solid #f1f5f9;
}

.action-btn {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.edit {
  background-color: #e0f2fe;
  color: #0369a1;
}

.action-btn.edit:hover {
  background-color: #bae6fd;
}

.action-btn.merge {
  background-color: #f3e8ff;
  color: #7e22ce;
}

.action-btn.merge:hover {
  background-color: #e9d5ff;
}

.action-btn.delete {
  background-color: #fee2e2;
  color: #b91c1c;
}

.action-btn.delete:hover {
  background-color: #fecaca;
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
  max-width: 600px;
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
  border-bottom: 1px solid #f1f5f9;
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

.tag-form, .merge-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.merge-info {
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.merge-info p {
  margin: 0 0 0.75rem;
  color: #334155;
  line-height: 1.6;
}

.merge-info p:last-child {
  margin-bottom: 0;
}

.warning {
  color: #b91c1c;
  font-weight: 500;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #334155;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.required {
  color: #ef4444;
}

.form-group input[type="text"],
.form-group textarea,
.form-group select {
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s;
  color: #1e293b;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
  outline: none;
}

.color-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.color-selector input[type="color"] {
  width: 4rem;
  height: 2.5rem;
  padding: 0.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
}

.color-value {
  font-family: monospace;
  color: #64748b;
  font-size: 0.95rem;
  padding: 0.35rem 0.75rem;
  background-color: #f8fafc;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.error-text {
  font-size: 0.85rem;
  color: #ef4444;
  margin-top: 0.25rem;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #f1f5f9;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background-color: #f8fafc;
}

.cancel-btn {
  padding: 0.75rem 1.25rem;
  background-color: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.submit-btn {
  padding: 0.75rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.submit-btn:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.submit-btn:active {
  transform: translateY(0);
}

.submit-btn.danger {
  background-color: #ef4444;
}

.submit-btn.danger:hover {
  background-color: #dc2626;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .stats-cards {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .tags-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .tag-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .tag-name {
    max-width: 100%;
  }
}
</style> 