<template>
    <div class="home">
        <!-- Hero 区域 -->
        <div class="hero-section">
            <div class="hero-bg"></div>
            <div class="hero-content">
                <div class="hero-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/>
                    </svg>
                    <span>多模态情感识别</span>
                </div>
                <h1 class="hero-title">
                    <span class="gradient-text">RoMER</span>
                    <br>
                    对话情感识别系统
                </h1>
                <p class="hero-desc">
                    基于视觉-语言-音频多模态融合的深度学习模型，
                    <br>精准识别对话中说话人的情感状态
                </p>
                <div class="hero-actions">
                    <el-button type="primary" size="large" @click="router.push('/image')">
                        <el-icon><Picture /></el-icon>
                        图片识别
                    </el-button>
                    <el-button size="large" class="btn-outline" @click="router.push('/video')">
                        <el-icon><VideoCamera /></el-icon>
                        视频识别
                    </el-button>
                </div>
            </div>
        </div>

        <!-- 特性介绍 -->
        <div class="features-section">
            <h2 class="section-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="title-icon">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z" fill="#3b82f6"/>
                </svg>
                核心功能
            </h2>
            <p class="section-desc">强大的多模态情感识别能力</p>
            <el-row :gutter="24">
                <el-col :span="8">
                    <div class="feature-card glass-card" @click="router.push('/image')">
                        <div class="feature-icon">
                            <svg viewBox="0 0 24 24" fill="none">
                                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                                <path d="M21 15L16 10L5 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <h3>图片情感识别</h3>
                        <p>上传图片，自动检测人脸并识别7种情感状态</p>
                        <ul>
                            <li>多人脸同时检测</li>
                            <li>精确情感分类</li>
                            <li>可视化标注结果</li>
                        </ul>
                        <div class="feature-link">
                            开始识别
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="feature-card glass-card" @click="router.push('/video')">
                        <div class="feature-icon">
                            <svg viewBox="0 0 24 24" fill="none">
                                <polygon points="23,7 16,12 23,17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                            </svg>
                        </div>
                        <h3>视频情感识别</h3>
                        <p>结合字幕信息，识别视频对话中的情感变化</p>
                        <ul>
                            <li>字幕驱动分析</li>
                            <li>时间线情感追踪</li>
                            <li>关键帧预览</li>
                        </ul>
                        <div class="feature-link">
                            开始识别
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                    </div>
                </el-col>
                <el-col :span="8">
                    <div class="feature-card glass-card feature-card-static">
                        <div class="feature-icon">
                            <svg viewBox="0 0 24 24" fill="none">
                                <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2"/>
                                <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <h3>可视化分析</h3>
                        <p>丰富的图表展示，深入理解情感分布和变化</p>
                        <ul>
                            <li>情感分布饼图</li>
                            <li>时间线分析</li>
                            <li>详细数据表格</li>
                        </ul>
                        <div class="feature-link">
                            了解更多
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </div>

        <!-- 情感类型展示 -->
        <div class="emotions-section glass-card">
            <h2 class="section-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="title-icon">
                    <circle cx="12" cy="12" r="10" stroke="#3b82f6" stroke-width="2"/>
                    <path d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
                    <line x1="9" y1="9" x2="9.01" y2="9" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
                    <line x1="15" y1="9" x2="15.01" y2="9" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
                </svg>
                支持的情感类型
            </h2>
            <p class="section-desc">基于 MELD 数据集训练的7种情感分类</p>
            <div class="emotions-grid">
                <div
                    v-for="(emotion, index) in emotionList"
                    :key="index"
                    class="emotion-card"
                    :style="{ '--delay': index * 0.1 + 's' }"
                >
                    <div class="emotion-icon" :style="{ background: emotion.gradient }">
                        <span class="emotion-emoji">{{ emotion.emoji }}</span>
                    </div>
                    <span class="emotion-name">{{ emotion.label }}</span>
                    <span class="emotion-en">{{ emotion.key }}</span>
                </div>
            </div>
        </div>

        <!-- 技术架构 -->
        <div class="tech-section">
            <h2 class="section-title">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="title-icon">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                技术架构
            </h2>
            <p class="section-desc">先进的多模态融合模型</p>
            <div class="tech-cards">
                <div class="tech-card glass-card">
                    <div class="tech-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12z" stroke="#3b82f6" stroke-width="2"/>
                            <circle cx="12" cy="12" r="3" stroke="#3b82f6" stroke-width="2"/>
                        </svg>
                    </div>
                    <h4>视觉编码器</h4>
                    <p>ConvNeXt + Transformer</p>
                </div>
                <div class="tech-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="tech-card glass-card">
                    <div class="tech-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="#3b82f6" stroke-width="2"/>
                            <path d="M14 2V8H20" stroke="#3b82f6" stroke-width="2"/>
                            <line x1="16" y1="13" x2="8" y2="13" stroke="#3b82f6" stroke-width="2"/>
                            <line x1="16" y1="17" x2="8" y2="17" stroke="#3b82f6" stroke-width="2"/>
                        </svg>
                    </div>
                    <h4>文本编码器</h4>
                    <p>RoBERTa</p>
                </div>
                <div class="tech-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="tech-card glass-card">
                    <div class="tech-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M12 1C12 1 12 5 12 8C12 11 9 11 9 8" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
                            <path d="M12 1C12 1 12 5 12 8C12 11 15 11 15 8" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
                            <rect x="4" y="11" width="16" height="12" rx="2" stroke="#3b82f6" stroke-width="2"/>
                            <circle cx="8" cy="17" r="2" stroke="#3b82f6" stroke-width="2"/>
                            <circle cx="16" cy="17" r="2" stroke="#3b82f6" stroke-width="2"/>
                        </svg>
                    </div>
                    <h4>音频编码器</h4>
                    <p>HuBERT</p>
                </div>
                <div class="tech-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="tech-card glass-card highlight">
                    <div class="tech-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="white" stroke-width="2"/>
                        </svg>
                    </div>
                    <h4>融合模块</h4>
                    <p>Cross-Attention</p>
                </div>
                <div class="tech-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="tech-card glass-card">
                    <div class="tech-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="#3b82f6" stroke-width="2"/>
                            <path d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
                            <line x1="9" y1="9" x2="9.01" y2="9" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
                            <line x1="15" y1="9" x2="15.01" y2="9" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <h4>情感分类</h4>
                    <p>7 类情感</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const emotionList = [
    { key: 'surprise', label: '惊讶', emoji: '😲', gradient: 'linear-gradient(135deg, #f472b6, #ec4899)' },
    { key: 'joy', label: '快乐', emoji: '😊', gradient: 'linear-gradient(135deg, #34d399, #10b981)' },
    { key: 'neutral', label: '中性', emoji: '😐', gradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)' },
    { key: 'sadness', label: '悲伤', emoji: '😢', gradient: 'linear-gradient(135deg, #a78bfa, #8b5cf6)' },
    { key: 'anger', label: '愤怒', emoji: '😠', gradient: 'linear-gradient(135deg, #fb923c, #f97316)' },
    { key: 'disgust', label: '厌恶', emoji: '🤢', gradient: 'linear-gradient(135deg, #a3e635, #84cc16)' },
    { key: 'fear', label: '恐惧', emoji: '😨', gradient: 'linear-gradient(135deg, #22d3ee, #06b6d4)' }
]
</script>

<style scoped>
.home {
    max-width: 1200px;
    margin: 0 auto;
}

/* 磨砂玻璃效果 */
.glass-card {
    background: rgba(255, 255, 255, 0.68) !important;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08) !important;
}

/* Hero 区域 */
.hero-section {
    position: relative;
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #60a5fa 100%);
    border-radius: 24px;
    padding: 64px 40px;
    margin-bottom: 48px;
    overflow: hidden;
}

.hero-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.06'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.hero-content {
    position: relative;
    z-index: 1;
    text-align: center;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(10px);
    padding: 8px 20px;
    border-radius: 24px;
    color: white;
    font-size: 13px;
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

.hero-title {
    font-size: 44px;
    font-weight: 700;
    color: white;
    margin-bottom: 16px;
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.gradient-text {
    background: linear-gradient(90deg, #fff 0%, #dbeafe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 58px;
}

.hero-desc {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.92);
    line-height: 1.7;
    margin-bottom: 36px;
}

.hero-actions {
    display: flex;
    gap: 16px;
    justify-content: center;
}

.hero-actions .el-button {
    padding: 14px 32px;
    font-size: 15px;
    border-radius: 12px;
    font-weight: 600;
}

.btn-outline {
    background: transparent !important;
    border: 2px solid rgba(255, 255, 255, 0.7) !important;
    color: white !important;
    box-shadow: none !important;
}

.btn-outline:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: white !important;
}

/* 通用段落样式 */
.section-title {
    text-align: center;
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.title-icon {
    flex-shrink: 0;
}

.section-desc {
    text-align: center;
    font-size: 15px;
    color: var(--text-secondary);
    margin-bottom: 40px;
}

/* 特性介绍 */
.features-section {
    margin-bottom: 60px;
}

.feature-card {
    border-radius: 20px;
    padding: 32px 24px;
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
}

.feature-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(59, 130, 246, 0.18) !important;
}

.feature-card-static {
    cursor: default;
}

.feature-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.25);
    padding: 12px;
}

.feature-icon svg {
    width: 100%;
    height: 100%;
}

.feature-card h3 {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
}

.feature-card p {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    line-height: 1.6;
}

.feature-card ul {
    list-style: none;
    padding: 0;
    margin-bottom: 20px;
}

.feature-card ul li {
    font-size: 13px;
    color: var(--text-secondary);
    padding: 4px 0;
    padding-left: 20px;
    position: relative;
}

.feature-card ul li::before {
    content: '';
    position: absolute;
    left: 0;
    top: 10px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #3b82f6;
}

.feature-link {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #2563eb;
    font-size: 14px;
    font-weight: 600;
}

.feature-link svg {
    transition: transform 0.2s;
}

.feature-card:hover .feature-link svg {
    transform: translateX(4px);
}

/* 情感类型 */
.emotions-section {
    margin-bottom: 60px;
    border-radius: 24px;
    padding: 48px 32px;
}

.emotions-grid {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
}

.emotion-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px 20px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    min-width: 110px;
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease forwards;
    animation-delay: var(--delay);
    opacity: 0;
    border: 1px solid rgba(255, 255, 255, 0.4);
}

@keyframes fadeInUp {
    from {
        transform: translateY(20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.emotion-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 24px rgba(59, 130, 246, 0.12);
}

.emotion-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.emotion-emoji {
    font-size: 26px;
}

.emotion-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
}

.emotion-en {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: capitalize;
}

/* 技术架构 */
.tech-section {
    margin-bottom: 60px;
}

.tech-cards {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
}

.tech-card {
    border-radius: 16px;
    padding: 24px 16px;
    text-align: center;
    min-width: 120px;
    transition: all 0.3s ease;
}

.tech-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(59, 130, 246, 0.12) !important;
}

.tech-card.highlight {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    border: none !important;
}

.tech-card.highlight h4,
.tech-card.highlight p {
    color: white;
}

.tech-icon {
    width: 40px;
    height: 40px;
    margin: 0 auto 12px;
}

.tech-icon svg {
    width: 100%;
    height: 100%;
}

.tech-card h4 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
}

.tech-card p {
    font-size: 11px;
    color: var(--text-secondary);
}

.tech-arrow {
    flex-shrink: 0;
}

.tech-arrow svg {
    opacity: 0.6;
}

/* 响应式 */
@media (max-width: 768px) {
    .hero-title {
        font-size: 28px;
    }

    .gradient-text {
        font-size: 36px;
    }

    .tech-cards {
        flex-direction: column;
    }

    .tech-arrow {
        transform: rotate(90deg);
    }
}
</style>
