<template>
    <div class="emotion-prob-bar">
        <div class="prob-bars">
            <div
                v-for="(item, index) in sortedProbs"
                :key="index"
                class="prob-item"
                :title="`${item.label}: ${(item.value * 100).toFixed(1)}%`"
            >
                <div class="prob-dot" :style="{ background: item.color }"></div>
                <div class="prob-track">
                    <div
                        class="prob-fill"
                        :style="{
                            width: (item.value * 100) + '%',
                            background: item.color
                        }"
                    ></div>
                </div>
                <span class="prob-label">{{ item.label }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    probabilities: {
        type: Object,
        required: true
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

const sortedProbs = computed(() => {
    if (!props.probabilities) return []
    return Object.entries(props.probabilities)
        .map(([key, value]) => ({
            key,
            label: emotionLabels[key] || key,
            value,
            color: emotionColors[key] || '#ccc'
        }))
        .sort((a, b) => b.value - a.value)
})
</script>

<style scoped>
.emotion-prob-bar {
    min-width: 180px;
}

.prob-bars {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.prob-item {
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
}

.prob-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}

.prob-track {
    flex: 1;
    height: 6px;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 3px;
    overflow: hidden;
    min-width: 60px;
}

.prob-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
}

.prob-label {
    font-size: 10px;
    color: var(--text-secondary);
    width: 24px;
    flex-shrink: 0;
}
</style>
