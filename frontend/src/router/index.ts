import { createRouter, createWebHistory } from 'vue-router'
// 使用类型导入
import type { RouteRecordRaw } from 'vue-router'

// 导入视图组件
import Home from '../views/Home.vue'
import UserList from '../views/UserList.vue'
import UserProfile from '../views/UserProfile.vue'
import UserPosts from '../views/UserPosts.vue'
import UserFavorites from '../views/UserFavorites.vue'
import NotFound from '../views/NotFound.vue'
import Register from '../views/Register.vue'
import Login from '../views/Login.vue'
import PostDetail from '../views/PostDetail.vue'

// 导入仪表盘视图组件
import Dashboard from '../views/Dashboard.vue'
import DashboardPosts from '../views/DashboardPosts.vue'
import DashboardUsers from '../views/DashboardUsers.vue'
import DashboardCategories from '../views/DashboardCategories.vue'
import DashboardTags from '../views/DashboardTags.vue'

// 导入存储
import { useAuthStore } from '../stores/auth'
import { UserRole } from '../types/user'

// 定义路由
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/users',
    name: 'UserList',
    component: UserList,
    meta: { requiresAuth: true, roles: ['admin', 'super_admin'] }
  },
  {
    path: '/users/:userId',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/users/:userId/posts',
    name: 'UserPosts',
    component: UserPosts,
    meta: { requiresAuth: true }
  },
  {
    path: '/users/:userId/favorites',
    name: 'UserFavorites',
    component: UserFavorites,
    meta: { requiresAuth: true }
  },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: PostDetail
  },
  // 仪表盘路由
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { 
      requiresAuth: true, 
      roles: [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MODERATOR]
    }
  },
  {
    path: '/dashboard/posts',
    name: 'DashboardPosts',
    component: DashboardPosts,
    meta: { 
      requiresAuth: true, 
      roles: [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MODERATOR]
    }
  },
  {
    path: '/dashboard/users',
    name: 'DashboardUsers',
    component: DashboardUsers,
    meta: { 
      requiresAuth: true, 
      roles: [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    }
  },
  {
    path: '/dashboard/categories',
    name: 'DashboardCategories',
    component: DashboardCategories,
    meta: { 
      requiresAuth: true, 
      roles: [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    }
  },
  {
    path: '/dashboard/tags',
    name: 'DashboardTags',
    component: DashboardTags,
    meta: { 
      requiresAuth: true, 
      roles: [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
]

// 创建路由器实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresRole = to.matched.some(record => record.meta.roles && Array.isArray(record.meta.roles) && record.meta.roles.length > 0)
  
  console.log(`[Router] 导航到: ${to.path}, 认证状态: ${authStore.isAuthenticated}, 用户: ${authStore.user?.username || '未登录'}`)
  console.log(`[Router] 目标路由requiresAuth: ${requiresAuth}, requiresRole: ${requiresRole}`)
  
  // 检查token的健康状态
  const token = localStorage.getItem('token')
  console.log(`[Router] localStorage中token状态: ${token ? '存在' : '不存在'}`)
  
  // 如果token存在但store中未认证，尝试重新初始化store
  if (token && !authStore.isAuthenticated) {
    console.log(`[Router] 发现localStorage有token但认证状态为false，尝试重新初始化authStore`)
    // 重新初始化认证状态
    authStore.init()
    
    // 再次检查认证状态
    console.log(`[Router] 重新初始化后认证状态: ${authStore.isAuthenticated}, 用户: ${authStore.user?.username || '仍未登录'}`)
    
    // 如果重新初始化后仍未认证，清理token
    if (!authStore.isAuthenticated) {
      console.warn(`[Router] 初始化后仍未认证，token可能无效，清除token`)
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
  
  // 检查是否需要认证
  if (requiresAuth && !authStore.isAuthenticated) {
    console.log(`[Router] 需要认证但用户未登录，重定向到登录页`)
    
    // 保存目标URL，登录成功后可以重定向回来
    if (to.path !== '/login') {
      sessionStorage.setItem('returnPath', to.path)
      console.log(`[Router] 已保存返回路径: ${to.path}`)
    }
    
    next('/login')
    return
  }
  
  // 检查是否需要特定角色
  if (requiresRole) {
    const allowedRoles = to.meta.roles as string[]
    const userRole = authStore.user?.role
    
    console.log(`[Router] 验证角色，用户角色: ${userRole}, 允许角色: ${allowedRoles.join(', ')}`)
    
    if (!userRole || !allowedRoles.includes(userRole)) {
      console.log(`[Router] 用户角色不符合要求，重定向到首页`)
      next('/')
      return
    }
  }
  
  console.log(`[Router] 验证通过，继续导航到: ${to.path}`)
  next()
})

// 导出路由器
export default router