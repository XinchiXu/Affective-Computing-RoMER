import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: () => import('./views/Home.vue')
    },
    {
        path: '/image',
        name: 'ImagePredict',
        component: () => import('./views/ImagePredict.vue')
    },
    {
        path: '/video',
        name: 'VideoPredict',
        component: () => import('./views/VideoPredict.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
