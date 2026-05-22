<template>
    <div class="app-wrapper">
        <el-container class="app-container">
            <el-header class="app-header glass-header">
                <div class="header-content">
                    <div class="logo" @click="router.push('/')">
                        <div class="logo-icon">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white" opacity="0.9"/>
                                <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <div class="logo-text">
                            <span class="title">RoMER</span>
                            <span class="subtitle">情感识别系统</span>
                        </div>
                    </div>
                    <el-menu
                        mode="horizontal"
                        :router="true"
                        :default-active="route.path"
                        class="nav-menu"
                    >
                        <el-menu-item index="/">
                            <el-icon><HomeFilled /></el-icon>
                            <span>首页</span>
                        </el-menu-item>
                        <el-menu-item index="/image">
                            <el-icon><Picture /></el-icon>
                            <span>图片识别</span>
                        </el-menu-item>
                        <el-menu-item index="/video">
                            <el-icon><VideoCamera /></el-icon>
                            <span>视频识别</span>
                        </el-menu-item>
                    </el-menu>
                </div>
            </el-header>
            <el-main class="app-main">
                <router-view v-slot="{ Component }">
                    <transition name="slide-up" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </el-main>
            <el-footer class="app-footer">
                <div class="footer-content">
                    <div class="footer-left">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
                        </svg>
                        <span>RoMER 情感识别系统 &copy; 2024</span>
                    </div>
                    <div class="footer-right">
                        <span>基于多模态融合的对话情感识别</span>
                    </div>
                </div>
            </el-footer>
        </el-container>
    </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
</script>

<style scoped>
.app-wrapper {
    min-height: 100vh;
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%);
}

.app-container {
    min-height: 100vh;
    background: transparent;
    max-width: 1400px;
    margin: 0 auto;
    box-shadow: 0 0 80px rgba(59, 130, 246, 0.12);
}

.glass-header {
    background: rgba(255, 255, 255, 0.72) !important;
    backdrop-filter: blur(24px) saturate(200%);
    -webkit-backdrop-filter: blur(24px) saturate(200%);
    border-bottom: 1px solid rgba(255, 255, 255, 0.5);
}

.app-header {
    padding: 0;
    height: 64px !important;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 24px rgba(59, 130, 246, 0.1);
}

.header-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    padding: 0 32px;
    height: 100%;
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    margin-right: 48px;
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

.logo-icon svg {
    width: 100%;
    height: 100%;
}

.logo-text {
    display: flex;
    flex-direction: column;
}

.logo-text .title {
    font-size: 18px;
    font-weight: 700;
    color: #1e40af;
    letter-spacing: 1px;
}

.logo-text .subtitle {
    font-size: 11px;
    color: #3b82f6;
    margin-top: -2px;
}

.nav-menu {
    flex: 1;
    border-bottom: none !important;
    background: transparent !important;
}

.nav-menu .el-menu-item {
    color: #374151 !important;
    border-bottom: none !important;
    font-size: 14px;
    font-weight: 500;
    height: 64px;
    line-height: 64px;
    border-radius: 8px;
    margin: 0 4px;
    transition: all 0.2s ease !important;
}

.nav-menu .el-menu-item:hover {
    background: rgba(59, 130, 246, 0.08) !important;
    color: #2563eb !important;
}

.nav-menu .el-menu-item.is-active {
    color: #2563eb !important;
    background: rgba(59, 130, 246, 0.12) !important;
    font-weight: 600;
}

.nav-menu .el-menu-item .el-icon {
    margin-right: 4px;
}

.app-main {
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px 32px;
    width: 100%;
    min-height: calc(100vh - 128px);
}

.app-footer {
    background: rgba(30, 64, 175, 0.95);
    height: auto !important;
    padding: 16px 0;
    backdrop-filter: blur(10px);
}

.footer-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 32px;
    color: rgba(255, 255, 255, 0.85);
    font-size: 12px;
}

.footer-left,
.footer-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 页面过渡动画 */
.slide-up-enter-active {
    transition: all 0.3s ease-out;
}

.slide-up-leave-active {
    transition: all 0.2s ease-in;
}

.slide-up-enter-from {
    transform: translateY(10px);
    opacity: 0;
}

.slide-up-leave-to {
    transform: translateY(-10px);
    opacity: 0;
}
</style>
