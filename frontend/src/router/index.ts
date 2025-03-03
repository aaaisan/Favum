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

// 导出路由器
export default router