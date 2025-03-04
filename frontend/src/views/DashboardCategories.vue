<template>
  <DashboardLayout>
    <div class="categories-management">
      <div class="top-actions">
        <button class="primary-btn" @click="openAddModal">
          <i class="icon">➕</i> 添加分类
        </button>
      </div>
      
      <div class="categories-container">
        <div v-if="isLoading" class="loading">加载中...</div>
        <div v-else-if="categories.length === 0" class="empty-state">
          暂无分类，点击"添加分类"按钮创建第一个分类
        </div>
        <div v-else class="categories-grid">
          <div v-for="category in categories" :key="category.id" class="category-card">
            <div class="category-header">
              <div class="category-icon" :style="{ backgroundColor: category.color }">
                {{ getCategoryIcon(category) }}
              </div>
              <div class="category-title">
                <h3>{{ category.name }}</h3>
                <span class="post-count">{{ category.post_count }} 篇帖子</span>
              </div>
            </div>
            
            <div class="category-description">
              <p>{{ category.description }}</p>
            </div>
            
            <div class="category-meta">
              <span class="category-order">排序: {{ category.order }}</span>
              <span class="category-status" :class="{ 'active': category.is_active }">
                {{ category.is_active ? '启用' : '禁用' }}
              </span>
            </div>
            
            <div class="category-actions">
              <button class="action-btn edit" @click="editCategory(category)">编辑</button>
              <button 
                v-if="category.is_active" 
                class="action-btn disable" 
                @click="toggleCategoryStatus(category)"
              >
                禁用
              </button>
              <button 
                v-else 
                class="action-btn enable" 
                @click="toggleCategoryStatus(category)"
              >
                启用
              </button>
              <button class="action-btn delete" @click="deleteCategory(category)">删除</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 添加/编辑分类模态框 -->
      <div v-if="showCategoryModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ isEditing ? '编辑分类' : '添加分类' }}</h2>
            <button class="close-btn" @click="closeModal">×</button>
          </div>
          
          <div class="modal-body">
            <form class="category-form" @submit.prevent="saveCategory">
              <div class="form-group">
                <label for="category-name">分类名称 <span class="required">*</span></label>
                <input
                  id="category-name"
                  v-model="categoryForm.name"
                  type="text"
                  required
                  placeholder="输入分类名称"
                  maxlength="50"
                />
                <div v-if="formErrors.name" class="error-text">{{ formErrors.name }}</div>
              </div>
              
              <div class="form-group">
                <label for="category-slug">分类别名 <span class="required">*</span></label>
                <input
                  id="category-slug"
                  v-model="categoryForm.slug"
                  type="text"
                  required
                  placeholder="输入分类别名（用于URL）"
                  maxlength="50"
                />
                <div v-if="formErrors.slug" class="error-text">{{ formErrors.slug }}</div>
                <div class="form-hint">别名只能包含小写字母、数字和连字符</div>
              </div>
              
              <div class="form-group">
                <label for="category-description">分类描述</label>
                <textarea
                  id="category-description"
                  v-model="categoryForm.description"
                  placeholder="输入分类描述"
                  rows="3"
                  maxlength="200"
                ></textarea>
              </div>
              
              <div class="form-group">
                <label for="category-color">分类颜色</label>
                <div class="color-selector">
                  <input
                    id="category-color"
                    v-model="categoryForm.color"
                    type="color"
                  />
                  <span class="color-value">{{ categoryForm.color }}</span>
                </div>
              </div>
              
              <div class="form-group">
                <label for="category-icon">分类图标</label>
                <input
                  id="category-icon"
                  v-model="categoryForm.icon"
                  type="text"
                  placeholder="输入图标 emoji 或代码"
                  maxlength="10"
                />
              </div>
              
              <div class="form-group">
                <label for="category-order">排序顺序</label>
                <input
                  id="category-order"
                  v-model.number="categoryForm.order"
                  type="number"
                  min="0"
                  step="1"
                />
                <div class="form-hint">数字越小排序越靠前</div>
              </div>
              
              <div class="form-group checkbox">
                <input
                  id="category-active"
                  v-model="categoryForm.is_active"
                  type="checkbox"
                />
                <label for="category-active">启用分类</label>
              </div>
            </form>
          </div>
          
          <div class="modal-footer">
            <button class="cancel-btn" @click="closeModal">取消</button>
            <button class="submit-btn" @click="saveCategory">保存</button>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import DashboardLayout from '../components/DashboardLayout.vue'

// 加载状态
const isLoading = ref(true)

// 分类列表
const categories = ref([
  {
    id: 1,
    name: '技术讨论',
    slug: 'tech-discussion',
    description: '讨论各种技术问题和解决方案',
    color: '#3498db',
    icon: '💻',
    order: 0,
    is_active: true,
    post_count: 42
  },
  {
    id: 2,
    name: '问题求助',
    slug: 'help-request',
    description: '寻求社区帮助解决问题',
    color: '#e74c3c',
    icon: '❓',
    order: 1,
    is_active: true,
    post_count: 28
  },
  {
    id: 3,
    name: '经验分享',
    slug: 'experience-sharing',
    description: '分享个人经验和教程',
    color: '#2ecc71',
    icon: '📝',
    order: 2,
    is_active: true,
    post_count: 17
  },
  {
    id: 4,
    name: '资源推荐',
    slug: 'resource-recommendation',
    description: '推荐有价值的资源和工具',
    color: '#f39c12',
    icon: '🔗',
    order: 3,
    is_active: false,
    post_count: 9
  }
])

// 模态框状态
const showCategoryModal = ref(false)
const isEditing = ref(false)

// 分类表单
const categoryForm = reactive({
  id: 0,
  name: '',
  slug: '',
  description: '',
  color: '#3498db',
  icon: '📂',
  order: 0,
  is_active: true
})

// 表单错误
const formErrors = reactive({
  name: '',
  slug: ''
})

// 获取分类图标
const getCategoryIcon = (category: any) => {
  return category.icon || '📁'
}

// 打开添加分类模态框
const openAddModal = () => {
  isEditing.value = false
  resetForm()
  showCategoryModal.value = true
}

// 编辑分类
const editCategory = (category: any) => {
  isEditing.value = true
  
  // 复制分类数据到表单
  categoryForm.id = category.id
  categoryForm.name = category.name
  categoryForm.slug = category.slug
  categoryForm.description = category.description
  categoryForm.color = category.color
  categoryForm.icon = category.icon
  categoryForm.order = category.order
  categoryForm.is_active = category.is_active
  
  showCategoryModal.value = true
}

// 切换分类状态
const toggleCategoryStatus = (category: any) => {
  // 实际应用中这里会调用API
  console.log(`${category.is_active ? '禁用' : '启用'}分类:`, category.id)
  
  // 更新分类状态
  const index = categories.value.findIndex(c => c.id === category.id)
  if (index !== -1) {
    categories.value[index].is_active = !categories.value[index].is_active
  }
}

// 删除分类
const deleteCategory = (category: any) => {
  if (confirm(`确定要删除分类 "${category.name}" 吗？\n该分类下的所有帖子将被移动到默认分类。`)) {
    // 实际应用中这里会调用API
    console.log('删除分类:', category.id)
    
    // 从列表中删除
    categories.value = categories.value.filter(c => c.id !== category.id)
  }
}

// 保存分类
const saveCategory = () => {
  // 重置错误
  formErrors.name = ''
  formErrors.slug = ''
  
  // 表单验证
  let isValid = true
  
  if (!categoryForm.name.trim()) {
    formErrors.name = '分类名称不能为空'
    isValid = false
  }
  
  if (!categoryForm.slug.trim()) {
    formErrors.slug = '分类别名不能为空'
    isValid = false
  } else if (!/^[a-z0-9-]+$/.test(categoryForm.slug)) {
    formErrors.slug = '别名只能包含小写字母、数字和连字符'
    isValid = false
  }
  
  if (!isValid) return
  
  // 实际应用中这里会调用API
  if (isEditing.value) {
    console.log('更新分类:', categoryForm)
    
    // 更新列表中的分类
    const index = categories.value.findIndex(c => c.id === categoryForm.id)
    if (index !== -1) {
      categories.value[index] = {
        ...categories.value[index],
        ...categoryForm
      }
    }
  } else {
    console.log('添加分类:', categoryForm)
    
    // 添加到列表
    categories.value.push({
      ...categoryForm,
      id: Math.max(0, ...categories.value.map(c => c.id)) + 1,
      post_count: 0
    })
  }
  
  closeModal()
}

// 重置表单
const resetForm = () => {
  categoryForm.id = 0
  categoryForm.name = ''
  categoryForm.slug = ''
  categoryForm.description = ''
  categoryForm.color = '#3498db'
  categoryForm.icon = '📂'
  categoryForm.order = categories.value.length
  categoryForm.is_active = true
  
  formErrors.name = ''
  formErrors.slug = ''
}

// 关闭模态框
const closeModal = () => {
  showCategoryModal.value = false
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
.categories-management {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

.top-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.top-actions h1 {
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

.categories-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  min-height: 500px;
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
  content: '📂';
  font-size: 3rem;
  color: #94a3b8;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.category-card {
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
  position: relative;
  height: 100%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.category-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  border-color: #cbd5e1;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 1.5rem;
}

.category-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.category-title {
  flex: 1;
}

.category-title h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
  font-weight: 600;
}

.post-count {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
  margin-top: 0.25rem;
  display: inline-block;
}

.category-description {
  padding: 0 1.5rem 1.5rem;
  flex: 1;
}

.category-description p {
  margin: 0;
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.6;
}

.category-meta {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: #64748b;
  border-top: 1px solid #f1f5f9;
  background-color: #f8fafc;
}

.category-order {
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.category-order::before {
  content: '#';
  font-size: 1rem;
  color: #94a3b8;
}

.category-status {
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 2rem;
  background-color: #f1f5f9;
  color: #64748b;
}

.category-status.active {
  background-color: #dcfce7;
  color: #166534;
}

.category-actions {
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
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.action-btn.edit {
  background-color: #e0f2fe;
  color: #0369a1;
}

.action-btn.edit:hover {
  background-color: #bae6fd;
}

.action-btn.disable {
  background-color: #fee2e2;
  color: #b91c1c;
}

.action-btn.disable:hover {
  background-color: #fecaca;
}

.action-btn.enable {
  background-color: #dcfce7;
  color: #166534;
}

.action-btn.enable:hover {
  background-color: #bbf7d0;
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
  max-width: 800px;
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

.category-form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group:nth-child(1),
.form-group:nth-child(2),
.form-group:nth-child(3) {
  grid-column: span 2;
}

.form-group.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
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
.form-group input[type="number"],
.form-group textarea {
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s;
  color: #1e293b;
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus,
.form-group textarea:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.15);
  outline: none;
}

.form-group input[type="checkbox"] {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 4px;
  cursor: pointer;
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

.form-hint {
  font-size: 0.8rem;
  color: #64748b;
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

/* Responsive adjustments */
@media (max-width: 1024px) {
  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
  
  .category-form {
    grid-template-columns: 1fr;
  }
  
  .form-group:nth-child(1),
  .form-group:nth-child(2),
  .form-group:nth-child(3) {
    grid-column: span 1;
  }
}

@media (max-width: 640px) {
  .categories-grid {
    grid-template-columns: 1fr;
  }
  
  .category-header {
    flex-direction: column;
    text-align: center;
  }
  
  .category-description p {
    text-align: center;
  }
}
</style> 