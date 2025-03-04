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
  const requiresRole = to.matched.some(record => record.meta.roles && record.meta.roles.length > 0)
  
  // 检查是否需要认证
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 检查是否需要特定角色
  if (requiresRole) {
    const allowedRoles = to.meta.roles as string[]
    const userRole = authStore.user?.role
    
    if (!userRole || !allowedRoles.includes(userRole)) {
      next('/')
      return
    }
  }
  
  next()
})

// 导出路由器
export default router