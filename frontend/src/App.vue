<script setup lang="ts">
import { onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  console.log('[App] 组件挂载，确保Auth Store已初始化')
  authStore.init()
})
</script>

<template>
  <div id="app">
    <Navbar />
    <main class="main-content">
      <router-view/>
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f8f9fa;
  color: #333;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
