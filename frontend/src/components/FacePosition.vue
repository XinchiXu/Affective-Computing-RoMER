<template>
    <div class="face-position">
        <div class="position-preview">
            <!-- 模拟图片区域 -->
            <div class="image-mock" :style="{ aspectRatio: aspectRatio }">
                <!-- 网格线 -->
                <div class="grid-lines">
                    <div class="grid-h" style="top: 25%"></div>
                    <div class="grid-h" style="top: 50%"></div>
                    <div class="grid-h" style="top: 75%"></div>
                    <div class="grid-v" style="left: 25%"></div>
                    <div class="grid-v" style="left: 50%"></div>
                    <div class="grid-v" style="left: 75%"></div>
                </div>
                <!-- 人脸框 -->
                <div
                    class="face-box"
                    :style="faceBoxStyle"
                    :title="`情感: ${emotionLabel}, 置信度: ${(confidence * 100).toFixed(1)}%`"
                >
                    <div class="face-label" :style="{ background: emotionColor }">
                        {{ emotionLabel }}
                    </div>
                </div>
            </div>
            <!-- 坐标信息 -->
            <div class="coord-info">
                <div class="coord-item">
                    <span class="coord-label">X:</span>
                    <span class="coord-value">{{ normalizedLeft }}%</span>
                </div>
                <div class="coord-item">
                    <span class="coord-label">Y:</span>
                    <span class="coord-value">{{ normalizedTop }}%</span>
                </div>
                <div class="coord-item">
                    <span class="coord-label">W:</span>
                    <span class="coord-value">{{ normalizedWidth }}%</span>
                </div>
                <div class="coord-item">
                    <span class="coord-label">H:</span>
                    <span class="coord-value">{{ normalizedHeight }}%</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    bbox: {
        type: Object,
        required: true
    },
    imageSize: {
        type: Array,
        default: () => [640, 480]
    },
    emotion: {
        type: String,
        default: 'neutral'
    },
    confidence: {
        type: Number,
        default: 0
    }
})

const emotionLabels = {
    surprise: '惊讶', joy: '快乐', neutral: '中性',
    sadness: '悲伤', anger: '愤怒', disgust: '厌恶', fear: '恐惧'
}

const emotionColors = {
    surprise: '#f472b6', joy: '#34d399', neutral: '#fbbf24',
    sadness: '#a78bfa', anger: '#fb923c', disgust: '#a3e635', fear: '#22d3ee'
}

const emotionLabel = computed(() => emotionLabels[props.emotion] || props.emotion)
const emotionColor = computed(() => emotionColors[props.emotion] || '#ccc')

const imageWidth = computed(() => props.imageSize[0] || 640)
const imageHeight = computed(() => props.imageSize[1] || 480)

const aspectRatio = computed(() => {
    return `${imageWidth.value} / ${imageHeight.value}`
})

const normalizedLeft = computed(() => {
    return Math.round((props.bbox.left / imageWidth.value) * 100)
})

const normalizedTop = computed(() => {
    return Math.round((props.bbox.top / imageHeight.value) * 100)
})

const normalizedWidth = computed(() => {
    return Math.round(((props.bbox.right - props.bbox.left) / imageWidth.value) * 100)
})

const normalizedHeight = computed(() => {
    return Math.round(((props.bbox.bottom - props.bbox.top) / imageHeight.value) * 100)
})

const faceBoxStyle = computed(() => {
    return {
        left: `${normalizedLeft.value}%`,
        top: `${normalizedTop.value}%`,
        width: `${normalizedWidth.value}%`,
        height: `${normalizedHeight.value}%`,
        borderColor: emotionColor.value
    }
})
</script>

<style scoped>
.face-position {
    min-width: 120px;
}

.position-preview {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.image-mock {
    position: relative;
    width: 100%;
    min-width: 80px;
    max-width: 120px;
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid rgba(0, 0, 0, 0.1);
}

.grid-lines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
}

.grid-h {
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background: rgba(0, 0, 0, 0.06);
}

.grid-v {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: rgba(0, 0, 0, 0.06);
}

.face-box {
    position: absolute;
    border: 2px solid;
    border-radius: 2px;
    transition: all 0.2s ease;
    min-width: 12px;
    min-height: 12px;
}

.face-box:hover {
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.2);
}

.face-label {
    position: absolute;
    top: -2px;
    left: -2px;
    padding: 1px 4px;
    font-size: 9px;
    color: white;
    border-radius: 2px 0 2px 0;
    white-space: nowrap;
    line-height: 1.2;
}

.coord-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px;
}

.coord-item {
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 10px;
}

.coord-label {
    color: var(--text-secondary);
    font-weight: 500;
}

.coord-value {
    color: var(--text-primary);
    font-family: monospace;
}
</style>
