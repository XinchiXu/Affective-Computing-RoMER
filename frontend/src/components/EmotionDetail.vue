<template>
    <div class="emotion-detail">
        <el-table :data="segments" stripe style="width: 100%">
            <el-table-column prop="id" label="片段" width="70" align="center" />
            <el-table-column label="时间段" width="140">
                <template #default="{ row }">
                    <div class="time-cell">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="#94a3b8" stroke-width="2"/>
                            <path d="M12 6V12L16 14" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        {{ row.start }}s - {{ row.end }}s
                    </div>
                </template>
            </el-table-column>
            <el-table-column label="情感" width="90">
                <template #default="{ row }">
                    <el-tag :color="getEmotionColor(row.emotion)" effect="dark" round size="small">
                        {{ getEmotionLabel(row.emotion) }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column label="概率分布" min-width="220">
                <template #default="{ row }">
                    <EmotionProbBar v-if="row.probabilities" :probabilities="row.probabilities" />
                    <span v-else>-</span>
                </template>
            </el-table-column>
            <el-table-column label="置信度" width="90">
                <template #default="{ row }">
                    <span class="confidence-text">{{ (row.confidence * 100).toFixed(1) }}%</span>
                </template>
            </el-table-column>
            <el-table-column label="字幕内容" min-width="180">
                <template #default="{ row }">
                    <el-tooltip :content="row.text" placement="top" :show-after="500">
                        <span class="text-truncate">{{ row.text || '无' }}</span>
                    </el-tooltip>
                </template>
            </el-table-column>
        </el-table>
    </div>
</template>

<script setup>
import EmotionProbBar from './EmotionProbBar.vue'

defineProps({
    segments: {
        type: Array,
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

const getEmotionLabel = (emotion) => emotionLabels[emotion] || emotion
const getEmotionColor = (emotion) => emotionColors[emotion] || '#ccc'
</script>

<style scoped>
.time-cell {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
}

.confidence-text {
    font-weight: 600;
    color: var(--primary-color);
}

.text-truncate {
    display: inline-block;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
    color: var(--text-secondary);
}

:deep(.el-tag) {
    border: none;
}
</style>
