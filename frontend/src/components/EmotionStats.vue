<template>
    <div class="emotion-stats">
        <el-row :gutter="20">
            <el-col :span="6">
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M16 4H18C19.1046 4 20 4.89543 20 6V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V6C4 4.89543 4.89543 4 6 4H8" stroke="white" stroke-width="2"/>
                            <rect x="8" y="2" width="8" height="4" rx="1" stroke="white" stroke-width="2"/>
                            <path d="M12 11V17M9 14H15" stroke="white" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ summary.total_segments || summary.total_faces || 0 }}</div>
                        <div class="stat-label">检测{{ summary.total_segments ? '片段' : '人脸' }}数</div>
                    </div>
                </div>
            </el-col>
            <el-col :span="6">
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="white" stroke-width="2"/>
                            <path d="M12 6V12L16 14" stroke="white" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ summary.total_duration || '-' }}</div>
                        <div class="stat-label">总时长(秒)</div>
                    </div>
                </div>
            </el-col>
            <el-col :span="6">
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="white" stroke-width="2"/>
                            <path d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" stroke="white" stroke-width="2" stroke-linecap="round"/>
                            <line x1="9" y1="9" x2="9.01" y2="9" stroke="white" stroke-width="3" stroke-linecap="round"/>
                            <line x1="15" y1="9" x2="15.01" y2="9" stroke="white" stroke-width="3" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ dominantEmotion }}</div>
                        <div class="stat-label">主要情感</div>
                    </div>
                </div>
            </el-col>
            <el-col :span="6">
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg viewBox="0 0 24 24" fill="none">
                            <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="white" stroke-width="2"/>
                            <path d="M12 8V16M8 12H16" stroke="white" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">{{ emotionTypes }}</div>
                        <div class="stat-label">情感种类</div>
                    </div>
                </div>
            </el-col>
        </el-row>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    summary: {
        type: Object,
        required: true
    }
})

const emotionLabels = {
    surprise: '惊讶', joy: '快乐', neutral: '中性',
    sadness: '悲伤', anger: '愤怒', disgust: '厌恶', fear: '恐惧'
}

const dominantEmotion = computed(() => {
    const counts = props.summary.emotion_counts || props.summary.emotion_distribution || {}
    let maxKey = ''
    let maxVal = 0
    for (const [key, val] of Object.entries(counts)) {
        if (val > maxVal) {
            maxVal = val
            maxKey = key
        }
    }
    return emotionLabels[maxKey] || '未知'
})

const emotionTypes = computed(() => {
    const counts = props.summary.emotion_counts || props.summary.emotion_distribution || {}
    return Object.keys(counts).length
})
</script>

<style scoped>
.emotion-stats {
    padding: 8px 0;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: rgba(59, 130, 246, 0.04);
    border-radius: 14px;
    transition: transform 0.2s ease;
    border: 1px solid rgba(59, 130, 246, 0.08);
}

.stat-item:hover {
    transform: translateY(-2px);
    background: rgba(59, 130, 246, 0.06);
}

.stat-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    flex-shrink: 0;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.stat-icon svg {
    width: 100%;
    height: 100%;
}

.stat-content {
    flex: 1;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}

.stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
}
</style>
