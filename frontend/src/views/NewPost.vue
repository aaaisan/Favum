<template>
  <div class="new-post-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">创建新帖子</h1>
        <p class="page-subtitle">分享您的想法、问题或经验</p>
      </div>
      
      <div class="editor-container">
        <form class="post-form" @submit.prevent="submitPost">
          <div class="form-header">
            <div class="form-group">
              <label for="post-title">标题 <span class="required">*</span></label>
              <input
                id="post-title"
                v-model="postForm.title"
                type="text"
                placeholder="输入帖子标题"
                maxlength="100"
                required
              />
              <div class="char-counter" :class="{ 'warning': postForm.title.length > 80 }">
                {{ postForm.title.length }}/100
              </div>
              <div v-if="formErrors.title" class="error-text">{{ formErrors.title }}</div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="post-category">分类 <span class="required">*</span></label>
                <select
                  id="post-category"
                  v-model="postForm.categoryId"
                  required
                >
                  <option value="" disabled selected>选择分类</option>
                  <option 
                    v-for="category in categories" 
                    :key="category.id" 
                    :value="category.id"
                  >
                    {{ category.name }}
                  </option>
                </select>
                <div v-if="formErrors.categoryId" class="error-text">{{ formErrors.categoryId }}</div>
              </div>
              
              <div class="form-group tag-group">
                <label>标签 <span class="optional">(可选)</span></label>
                <div class="tags-input-container">
                  <div class="selected-tags">
                    <div 
                      v-for="tag in selectedTags" 
                      :key="tag.id"
                      class="tag-pill"
                    >
                      <span>{{ tag.name }}</span>
                      <button 
                        type="button" 
                        class="remove-tag"
                        @click="removeTag(tag)"
                      >
                        &times;
                      </button>
                    </div>
                  </div>
                  
                  <div class="tag-search">
                    <input
                      ref="tagInput"
                      v-model="tagQuery"
                      type="text"
                      placeholder="搜索或添加标签"
                      @focus="isTagSearchActive = true"
                      @blur="handleTagBlur"
                      @keydown.enter.prevent="addNewTag"
                    />
                    
                    <div v-if="isTagSearchActive && (filteredTags.length > 0 || tagQuery)" class="tag-suggestions">
                      <div v-if="filteredTags.length > 0">
                        <div 
                          v-for="tag in filteredTags" 
                          :key="tag.id"
                          class="tag-suggestion-item"
                          @mousedown.prevent="addTag(tag)"
                        >
                          {{ tag.name }}
                        </div>
                      </div>
                      
                      <div v-else-if="tagQuery.trim()" class="tag-suggestion-create">
                        <span>创建标签 "{{ tagQuery.trim() }}"</span>
                        <button 
                          type="button" 
                          class="create-tag-btn"
                          @mousedown.prevent="createAndAddTag"
                        >
                          添加
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="tags-hint">最多添加5个标签，标签之间用逗号分隔</div>
              </div>
            </div>
          </div>
          
          <div class="form-group editor-group">
            <label for="post-content">内容 <span class="required">*</span></label>
            <div class="editor-toolbar">
              <button type="button" class="toolbar-btn" title="加粗" @click="insertFormatting('bold')">
                <span class="btn-icon">B</span>
              </button>
              <button type="button" class="toolbar-btn" title="斜体" @click="insertFormatting('italic')">
                <span class="btn-icon"><i>I</i></span>
              </button>
              <button type="button" class="toolbar-btn" title="标题" @click="insertFormatting('heading')">
                <span class="btn-icon">H</span>
              </button>
              <button type="button" class="toolbar-btn" title="链接" @click="insertFormatting('link')">
                <span class="btn-icon">🔗</span>
              </button>
              <button type="button" class="toolbar-btn" title="引用" @click="insertFormatting('quote')">
                <span class="btn-icon">❝</span>
              </button>
              <button type="button" class="toolbar-btn" title="代码" @click="insertFormatting('code')">
                <span class="btn-icon">&lt;/&gt;</span>
              </button>
              <button type="button" class="toolbar-btn" title="无序列表" @click="insertFormatting('bulletList')">
                <span class="btn-icon">•</span>
              </button>
              <button type="button" class="toolbar-btn" title="有序列表" @click="insertFormatting('numberList')">
                <span class="btn-icon">1.</span>
              </button>
              <button type="button" class="toolbar-btn" title="图片" @click="insertFormatting('image')">
                <span class="btn-icon">🖼️</span>
              </button>
            </div>
            
            <textarea
              id="post-content"
              ref="contentEditor"
              v-model="postForm.content"
              placeholder="输入帖子内容..."
              rows="12"
              required
            ></textarea>
            <div class="char-counter" :class="{ 'warning': postForm.content.length > 10000 }">
              {{ postForm.content.length }}/20000
            </div>
            <div v-if="formErrors.content" class="error-text">{{ formErrors.content }}</div>
          </div>
          
          <div class="form-group">
            <div class="preview-header">
              <label>预览</label>
              <button 
                type="button" 
                class="toggle-preview"
                @click="showPreview = !showPreview"
              >
                {{ showPreview ? '隐藏预览' : '显示预览' }}
              </button>
            </div>
            
            <div v-if="showPreview" class="content-preview">
              <h2 class="preview-title">{{ postForm.title || '帖子标题' }}</h2>
              <div class="preview-content">
                {{ postForm.content || '帖子内容将显示在这里...' }}
              </div>
            </div>
          </div>
          
          <div class="form-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="postForm.saveAsDraft" />
              <span>保存为草稿</span>
            </label>
          </div>
          
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="cancelPost">取消</button>
            <button 
              type="submit" 
              class="submit-btn" 
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="loader"></span>
              <span v-else>{{ postForm.saveAsDraft ? '保存草稿' : '发布帖子' }}</span>
            </button>
          </div>
        </form>
        
        <div class="sidebar">
          <div class="sidebar-section">
            <h3>发帖指南</h3>
            <ul class="guidelines">
              <li>请确保您的帖子内容符合社区规则</li>
              <li>添加清晰的标题，以便其他用户理解您的主题</li>
              <li>如果是提问，请提供足够的上下文信息</li>
              <li>分享代码时，请使用代码格式化工具</li>
              <li>上传的图片大小不要超过2MB</li>
            </ul>
          </div>
          
          <div class="sidebar-section">
            <h3>格式化提示</h3>
            <div class="format-tips">
              <div class="format-tip">
                <div class="tip-command">**文本**</div>
                <div class="tip-result">加粗文本</div>
              </div>
              <div class="format-tip">
                <div class="tip-command">*文本*</div>
                <div class="tip-result">斜体文本</div>
              </div>
              <div class="format-tip">
                <div class="tip-command"># 标题</div>
                <div class="tip-result">一级标题</div>
              </div>
              <div class="format-tip">
                <div class="tip-command">[链接文本](URL)</div>
                <div class="tip-result">添加超链接</div>
              </div>
              <div class="format-tip">
                <div class="tip-command">```代码```</div>
                <div class="tip-result">代码块</div>
              </div>
              <div class="format-tip">
                <div class="tip-command">> 引用文本</div>
                <div class="tip-result">添加引用</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const tagInput = ref(null)
const contentEditor = ref<HTMLTextAreaElement | null>(null)

// 表单数据
const postForm = reactive({
  title: '',
  content: '',
  categoryId: '',
  saveAsDraft: false
})

// 表单错误
const formErrors = ref<Record<string, string>>({
  title: '',
  content: '',
  categoryId: ''
})

// 提交状态
const isSubmitting = ref(false)
const showPreview = ref(false)

// 分类数据
const categories = ref([
  { id: 1, name: '技术讨论' },
  { id: 2, name: '问题求助' },
  { id: 3, name: '经验分享' },
  { id: 4, name: '资源推荐' },
  { id: 5, name: '招聘信息' }
])

// 标签相关
const tagQuery = ref('')
const isTagSearchActive = ref(false)
const selectedTags = ref<{ id: number; name: string }[]>([])

// 可用标签列表
const availableTags = ref([
  { id: 1, name: 'JavaScript' },
  { id: 2, name: 'TypeScript' },
  { id: 3, name: 'Vue' },
  { id: 4, name: 'React' },
  { id: 5, name: 'Angular' },
  { id: 6, name: 'Node.js' },
  { id: 7, name: 'CSS' },
  { id: 8, name: 'HTML' },
  { id: 9, name: '前端' },
  { id: 10, name: '后端' },
  { id: 11, name: '移动开发' },
  { id: 12, name: '数据库' },
  { id: 13, name: '性能优化' },
  { id: 14, name: '设计模式' },
  { id: 15, name: '算法' }
])

// 筛选标签
const filteredTags = computed(() => {
  if (!tagQuery.value) return []
  
  // Filter already selected tags and match query
  const selectedIds = selectedTags.value.map(tag => tag.id)
  const query = tagQuery.value.toLowerCase()
  
  return availableTags.value
    .filter(tag => !selectedIds.includes(tag.id) && tag.name.toLowerCase().includes(query))
    .slice(0, 5)
})

// 添加标签
const addTag = (tag: { id: number; name: string } | undefined) => {
  if (!tag) return
  
  if (selectedTags.value.length < 5 && !selectedTags.value.some(t => t.id === tag.id)) {
    selectedTags.value.push(tag)
    tagQuery.value = ''
  }
}

// 移除标签
const removeTag = (tag: { id: number; name: string }) => {
  selectedTags.value = selectedTags.value.filter(t => t.id !== tag.id)
}

// 创建并添加新标签
const createAndAddTag = () => {
  if (!tagQuery.value.trim() || selectedTags.value.length >= 5) return
  
  // 检查标签是否已存在
  const tagExists = availableTags.value.some(
    tag => tag.name.toLowerCase() === tagQuery.value.trim().toLowerCase()
  )
  
  if (tagExists) {
    const existingTag = availableTags.value.find(
      tag => tag.name.toLowerCase() === tagQuery.value.trim().toLowerCase()
    )
    if (existingTag) {
      addTag(existingTag)
    }
  } else {
    // 创建新标签（实际应用中会调用API）
    const newTag = {
      id: Date.now(), // Temporary ID until saved to backend
      name: tagQuery.value.trim()
    }
    
    // 添加到可用标签列表
    availableTags.value.push(newTag)
    
    // 添加到已选标签
    selectedTags.value.push(newTag)
    tagQuery.value = ''
  }
}

// 通过回车键添加新标签
const addNewTag = () => {
  if (filteredTags.value.length > 0) {
    // 如果有建议，选择第一个
    addTag(filteredTags.value[0])
  } else if (tagQuery.value.trim() && selectedTags.value.length < 5) {
    // 否则创建新标签
    createAndAddTag()
  }
}

// 处理标签输入框失焦
const handleTagBlur = () => {
  // 延迟隐藏下拉框，以便能够点击建议
  setTimeout(() => {
    isTagSearchActive.value = false
  }, 200)
}

// 插入格式化标记
const insertFormatting = (type: string) => {
  if (!contentEditor.value) return
  
  const textarea = contentEditor.value as HTMLTextAreaElement
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = postForm.content.substring(start, end)
  let replacement = ''
  
  switch (type) {
    case 'bold':
      replacement = `**${selectedText || '加粗文本'}**`
      break
    case 'italic':
      replacement = `*${selectedText || '斜体文本'}*`
      break
    case 'heading':
      replacement = `## ${selectedText || '标题'}`
      break
    case 'link':
      replacement = `[${selectedText || '链接文本'}](https://example.com)`
      break
    case 'quote':
      replacement = `> ${selectedText || '引用文本'}`
      break
    case 'code':
      replacement = selectedText ? `\`\`\`\n${selectedText}\n\`\`\`` : '```\n代码块\n```'
      break
    case 'bulletList':
      replacement = selectedText ? selectedText.split('\n').map(line => `- ${line}`).join('\n') : '- 列表项\n- 列表项\n- 列表项'
      break
    case 'numberList':
      replacement = selectedText ? selectedText.split('\n').map((line, i) => `${i+1}. ${line}`).join('\n') : '1. 列表项\n2. 列表项\n3. 列表项'
      break
    case 'image':
      replacement = `![${selectedText || '图片描述'}](https://example.com/image.jpg)`
      break
  }
  
  const newContent = postForm.content.substring(0, start) + replacement + postForm.content.substring(end)
  postForm.content = newContent
  
  // 设置光标位置
  setTimeout(() => {
    textarea.focus()
    const newPosition = start + replacement.length
    textarea.setSelectionRange(newPosition, newPosition)
  }, 0)
}

// 提交帖子
const submitPost = async () => {
  // 重置错误
  Object.keys(formErrors.value).forEach(key => {
    formErrors.value[key as keyof typeof formErrors.value] = ''
  })
  
  // 表单验证
  let isValid = true
  
  if (!postForm.title.trim()) {
    formErrors.value.title = '请输入帖子标题'
    isValid = false
  } else if (postForm.title.length > 100) {
    formErrors.value.title = '标题不能超过100个字符'
    isValid = false
  }
  
  if (!postForm.content.trim()) {
    formErrors.value.content = '请输入帖子内容'
    isValid = false
  } else if (postForm.content.length > 20000) {
    formErrors.value.content = '内容不能超过20000个字符'
    isValid = false
  }
  
  if (!postForm.categoryId) {
    formErrors.value.categoryId = '请选择帖子分类'
    isValid = false
  }
  
  if (!isValid) return
  
  // 设置提交状态
  isSubmitting.value = true
  
  try {
    // 模拟API请求
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 准备表单数据
    const formData = {
      title: postForm.title,
      content: postForm.content,
      categoryId: postForm.categoryId,
      isDraft: postForm.saveAsDraft,
      tags: selectedTags.value.map(tag => tag.id)
    }
    
    // 实际应用中这里会调用API
    console.log('提交帖子:', formData)
    
    // 提交成功，跳转到首页或帖子详情页
    router.push('/')
  } catch (error) {
    // 处理提交错误
    console.error('提交失败:', error)
    
    // 显示一般错误消息
    if (error instanceof Error) {
      formErrors.value.title = error.message
    } else {
      formErrors.value.title = '提交失败，请稍后再试'
    }
  } finally {
    // 重置提交状态
    isSubmitting.value = false
  }
}

// 取消发帖
const cancelPost = () => {
  if (postForm.title || postForm.content) {
    if (confirm('您有未保存的内容，确定要离开吗？')) {
      router.push('/')
    }
  } else {
    router.push('/')
  }
}

// 自动保存草稿
let autoSaveInterval: number | null = null

const saveAsDraft = () => {
  if (postForm.title || postForm.content) {
    // 实际应用中这里会调用API保存草稿
    console.log('自动保存草稿:', {
      title: postForm.title,
      content: postForm.content,
      categoryId: postForm.categoryId,
      tags: selectedTags.value.map(tag => tag.id)
    })
  }
}

// 离开前提示
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (postForm.title || postForm.content) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  fetchCategories()
  fetchTags()
  
  // Set up content editor reference
  nextTick(() => {
    contentEditor.value = document.getElementById('content-editor') as HTMLTextAreaElement | null
  })
  
  // Set up auto-save (commenting out for now, enable when ready)
  // autoSaveInterval = window.setInterval(saveAsDraft, 60000) as unknown as number
  
  // Set up beforeunload event
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  // 清除自动保存
  if (autoSaveInterval !== null) {
    clearInterval(autoSaveInterval)
  }
  
  // 移除离开提示
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

// Replace mock data with actual API calls
const fetchCategories = async () => {
  try {
    const response = await fetch('/api/categories')
    if (response.ok) {
      categories.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching categories:', error)
  }
}

const fetchTags = async () => {
  try {
    const response = await fetch('/api/tags')
    if (response.ok) {
      availableTags.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching tags:', error)
  }
}
</script>

<style scoped>
.new-post-page {
  width: 100%;
  background-color: #f8fafc;
  min-height: 100vh;
  padding: 2rem 0 4rem;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.page-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  color: #64748b;
}

.editor-container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 2.5rem;
  align-items: start;
}

.post-form {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  border: 1px solid #e2e8f0;
}

.form-header {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.5rem;
}

.required {
  color: #ef4444;
  margin-left: 0.25rem;
}

.optional {
  color: #94a3b8;
  font-weight: normal;
  font-size: 0.875rem;
  margin-left: 0.25rem;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.char-counter {
  text-align: right;
  font-size: 0.825rem;
  color: #94a3b8;
  margin-top: 0.4rem;
}

.char-counter.warning {
  color: #f59e0b;
}

.error-text {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.tag-group {
  position: relative;
}

.tags-input-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: relative;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  min-height: 2rem;
  padding: 0.5rem 0;
}

.tag-pill {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.6rem;
  background-color: #eff6ff;
  color: #1d4ed8;
  border-radius: 50px;
  font-size: 0.875rem;
}

.remove-tag {
  width: 1.25rem;
  height: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  transition: all 0.2s;
}

.remove-tag:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

.tag-search {
  position: relative;
}

.tag-search input {
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
}

.tag-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 0.5rem;
}

.tag-suggestion-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-suggestion-item:hover {
  background-color: #f8fafc;
}

.tag-suggestion-create {
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f1f5f9;
}

.create-tag-btn {
  padding: 0.25rem 0.6rem;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.create-tag-btn:hover {
  background-color: #dbeafe;
}

.tags-hint {
  font-size: 0.825rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.editor-group {
  position: relative;
}

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.toolbar-btn {
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background-color: #eff6ff;
  border-color: #bfdbfe;
}

.btn-icon {
  font-size: 0.95rem;
  color: #475569;
  font-weight: 600;
}

.form-group textarea {
  min-height: 300px;
  resize: vertical;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.toggle-preview {
  padding: 0.5rem 0.75rem;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-preview:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

.content-preview {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  min-height: 200px;
}

.preview-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1rem;
}

.preview-content {
  color: #334155;
  line-height: 1.7;
  white-space: pre-wrap;
}

.form-options {
  margin-bottom: 2rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
  color: #475569;
  font-size: 0.95rem;
}

.checkbox-label input {
  width: 1rem;
  height: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 0.875rem 1.5rem;
  background-color: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
}

.submit-btn {
  padding: 0.875rem 1.5rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.loader {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.sidebar {
  position: sticky;
  top: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.sidebar-section {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.sidebar-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.guidelines {
  list-style-type: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.guidelines li {
  position: relative;
  padding-left: 1.5rem;
  color: #475569;
  line-height: 1.5;
}

.guidelines li::before {
  content: "•";
  position: absolute;
  left: 0.25rem;
  color: #3b82f6;
  font-weight: bold;
  font-size: 1.25rem;
}

.format-tips {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.format-tip {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.tip-command {
  padding: 0.4rem 0.75rem;
  background-color: #f8fafc;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.9rem;
  color: #475569;
}

.tip-result {
  font-size: 0.85rem;
  color: #64748b;
  padding-left: 0.75rem;
}

/* Responsive design */
@media (max-width: 1024px) {
  .editor-container {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    position: static;
    margin-top: 2rem;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .post-form {
    padding: 1.5rem;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .cancel-btn, .submit-btn {
    width: 100%;
  }
}
</style> 