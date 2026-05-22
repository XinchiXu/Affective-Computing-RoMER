<template>
    <div class="image-predict">
        <el-card class="upload-card glass-card">
            <template #header>
                <div class="card-header">
                    <div>
                        <h3>图片情感识别</h3>
                        <p>上传一张或多张图片，系统将自动检测人脸并识别情感</p>
                    </div>
                </div>
            </template>

            <el-upload
                ref="uploadRef"
                class="upload-area"
                drag
                multiple
                :auto-upload="false"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :file-list="fileList"
                accept="image/*"
            >
                <div class="upload-content">
                    <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                    <div class="el-upload__text">
                        拖拽文件到此处，或 <em>点击上传</em>
                    </div>
                    <div class="el-upload__tip">
                        支持 jpg/png/bmp 等图片格式，可同时上传多张
                    </div>
                </div>
            </el-upload>

            <!-- 文件列表 -->
            <div v-if="fileList.length" class="file-preview">
                <div v-for="(file, index) in fileList" :key="index" class="file-item">
                    <el-icon><Picture /></el-icon>
                    <span class="file-name">{{ file.name }}</span>
                    <el-icon class="remove-icon" @click="removeFile(index)"><Close /></el-icon>
                </div>
            </div>

            <div class="action-bar">
                <el-button
                    type="primary"
                    size="large"
                    :loading="loading"
                    :disabled="fileList.length === 0"
                    @click="handlePredict"
                >
                    <el-icon><Cpu /></el-icon>
                    开始识别
                </el-button>
                <el-button size="large" @click="handleClear">
                    <el-icon><Delete /></el-icon>
                    清空
                </el-button>
            </div>
        </el-card>

        <!-- 进度显示 -->
        <el-card v-if="taskId && progress" class="progress-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>
                        <el-icon class="loading-icon"><Loading /></el-icon>
                        识别进度
                    </h3>
                    <el-tag :type="progressStatusType" size="small">
                        {{ progressStatusText }}
                    </el-tag>
                </div>
            </template>
            <div class="progress-content">
                <el-progress
                    :percentage="progress.progress"
                    :status="progressStatus"
                    :stroke-width="10"
                    striped
                    :striped-flow="progress.status === 'running'"
                />
                <div class="progress-info">
                    <span>{{ progress.current_step }}</span>
                    <span class="progress-msg">{{ progress.message }}</span>
                </div>
            </div>
        </el-card>

        <!-- 错误提示 -->
        <el-alert
            v-if="error"
            :title="error"
            type="error"
            show-icon
            :closable="true"
            @close="error = null"
        />

        <!-- 统计概览 -->
        <el-card v-if="summary" class="stats-card glass-card">
            <template #header>
                <h3>识别统计</h3>
            </template>
            <EmotionStats :summary="summary" />
        </el-card>

        <!-- 情感分布图 -->
        <el-card v-if="summary" class="chart-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>情感分布</h3>
                    <el-radio-group v-model="chartType" size="small">
                        <el-radio-button label="pie">饼图</el-radio-button>
                        <el-radio-button label="bar">柱状图</el-radio-button>
                    </el-radio-group>
                </div>
            </template>
            <EmotionChart :data="summary.emotion_distribution" :type="chartType" />
        </el-card>

        <!-- 结果图片 -->
        <el-card v-if="results.length > 0" class="result-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>识别结果</h3>
                    <el-button type="primary" @click="downloadAll">
                        <el-icon><Download /></el-icon>
                        下载全部
                    </el-button>
                </div>
            </template>

            <el-row :gutter="20">
                <el-col v-for="(result, index) in results" :key="index" :span="8">
                    <div class="result-item">
                        <div class="result-image" @click="openPreview(result)">
                            <img :src="result.url" :alt="result.filename" />
                            <div class="image-overlay">
                                <el-icon size="24"><ZoomIn /></el-icon>
                                <span>点击放大</span>
                            </div>
                        </div>
                        <div class="result-info">
                            <span class="filename">{{ result.filename }}</span>
                            <el-button
                                type="primary"
                                size="small"
                                @click="downloadResult(result)"
                            >
                                下载
                            </el-button>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </el-card>

        <!-- 人脸详情 -->
        <el-card v-if="faceDetails.length" class="detail-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="8" r="4" stroke="#3b82f6" stroke-width="2"/>
                            <path d="M6 21V19C6 16.7909 7.79086 15 10 15H14C16.2091 15 18 16.7909 18 19V21" stroke="#3b82f6" stroke-width="2"/>
                        </svg>
                        人脸检测详情
                    </h3>
                </div>
            </template>
            <el-table :data="faceDetails" stripe style="width: 100%">
                <el-table-column prop="filename" label="文件名" width="100" />
                <el-table-column prop="face_id" label="编号" width="60" align="center" />
                <el-table-column label="情感" width="80">
                    <template #default="{ row }">
                        <el-tag :color="getEmotionColor(row.emotion)" effect="dark" round size="small">
                            {{ getEmotionLabel(row.emotion) }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="位置" width="140">
                    <template #default="{ row }">
                        <FacePosition
                            :bbox="row.bbox"
                            :imageSize="row.image_size"
                            :emotion="row.emotion"
                            :confidence="row.confidence"
                        />
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
            </el-table>
        </el-card>

        <!-- 图片预览弹窗 -->
        <el-dialog v-model="previewVisible" title="识别结果预览" width="80%">
            <img :src="previewData?.url" style="width: 100%" />
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import EmotionChart from '../components/EmotionChart.vue'
import EmotionStats from '../components/EmotionStats.vue'
import EmotionProbBar from '../components/EmotionProbBar.vue'
import FacePosition from '../components/FacePosition.vue'

const uploadRef = ref(null)
const fileList = ref([])
const loading = ref(false)
const results = ref([])
const detail = ref(null)
const chartType = ref('pie')
const taskId = ref(null)
const progress = ref(null)
const error = ref(null)
const previewVisible = ref(false)
const previewData = ref(null)

let progressTimer = null

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

const summary = computed(() => detail.value?.summary || null)
const faceDetails = computed(() => detail.value?.details || [])

const progressStatus = computed(() => {
    if (progress.value?.status === 'completed') return 'success'
    if (progress.value?.status === 'error') return 'exception'
    return undefined
})

const progressStatusType = computed(() => {
    if (progress.value?.status === 'completed') return 'success'
    if (progress.value?.status === 'error') return 'danger'
    return 'primary'
})

const progressStatusText = computed(() => {
    if (progress.value?.status === 'completed') return '已完成'
    if (progress.value?.status === 'error') return '失败'
    return '处理中'
})

const handleFileChange = (file, newFileList) => {
    fileList.value = newFileList
}

const handleFileRemove = (file, newFileList) => {
    fileList.value = newFileList
}

const removeFile = (index) => {
    fileList.value.splice(index, 1)
}

const handleClear = () => {
    fileList.value = []
    results.value = []
    detail.value = null
    taskId.value = null
    progress.value = null
    error.value = null
    uploadRef.value?.clearFiles()
    stopProgressPolling()
}

const openPreview = (result) => {
    previewData.value = result
    previewVisible.value = true
}

const startProgressPolling = () => {
    stopProgressPolling()
    progressTimer = setInterval(async () => {
        if (!taskId.value) return
        try {
            const response = await axios.get(`/api/progress/${taskId.value}`)
            progress.value = response.data

            if (response.data.status === 'completed') {
                stopProgressPolling()
                const resultData = response.data.result
                if (resultData) {
                    detail.value = resultData
                    if (resultData.details) {
                        const uniqueFiles = [...new Set(resultData.details.map(d => d.filename))]
                        results.value = uniqueFiles.map(filename => ({
                            filename,
                            url: `/api/result/image/${filename}`
                        }))
                    }
                }
                ElMessage.success(`成功识别 ${results.value.length} 张图片`)
                loading.value = false
            } else if (response.data.status === 'error') {
                stopProgressPolling()
                error.value = response.data.error || '识别失败'
                ElMessage.error('识别失败：' + error.value)
                loading.value = false
            }
        } catch (e) {
            console.error('获取进度失败:', e)
        }
    }, 300)
}

const stopProgressPolling = () => {
    if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
    }
}

const handlePredict = async () => {
    if (fileList.value.length === 0) {
        ElMessage.warning('请先上传图片')
        return
    }

    loading.value = true
    results.value = []
    detail.value = null
    error.value = null

    try {
        const formData = new FormData()
        fileList.value.forEach(file => {
            formData.append('files', file.raw)
        })

        const response = await axios.post('/api/predict/image', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        if (response.data.task_id) {
            taskId.value = response.data.task_id
            startProgressPolling()
        }
    } catch (error) {
        const msg = error.response?.data?.detail || '识别失败，请重试'
        ElMessage.error(msg)
        loading.value = false
    }
}

const downloadResult = (result) => {
    const link = document.createElement('a')
    link.href = result.url
    link.download = result.filename
    link.click()
}

const downloadAll = () => {
    results.value.forEach(result => {
        downloadResult(result)
    })
}

onUnmounted(() => {
    stopProgressPolling()
})
</script>

<style scoped>
.image-predict {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 磨砂玻璃卡片 */
.glass-card {
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08) !important;
}

.upload-card,
.result-card,
.stats-card,
.chart-card,
.detail-card,
.progress-card {
    border-radius: 16px;
    overflow: hidden;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-header h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.card-header p {
    color: var(--text-secondary);
    font-size: 13px;
    margin-top: 4px;
}

.upload-area {
    width: 100%;
}

.upload-content {
    padding: 20px;
}

/* 文件预览 */
.file-preview {
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.file-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(59, 130, 246, 0.06);
    border-radius: 8px;
    font-size: 13px;
    color: var(--text-secondary);
}

.file-name {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.remove-icon {
    cursor: pointer;
    color: var(--text-secondary);
    transition: color 0.2s;
}

.remove-icon:hover {
    color: #ef4444;
}

.action-bar {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 24px;
}

.action-bar .el-button {
    min-width: 140px;
}

/* 进度卡片 */
.progress-card {
    background: rgba(59, 130, 246, 0.06) !important;
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.loading-icon {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.progress-content {
    padding: 8px 0;
}

.progress-info {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text-secondary);
}

.progress-msg {
    color: var(--text-secondary);
}

/* 结果图片 */
.result-item {
    margin-bottom: 20px;
    border-radius: 12px;
    overflow: hidden;
    background: var(--card-bg);
    border: 1px solid rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.06);
}

.result-item:hover {
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
    transform: translateY(-4px);
}

.result-image {
    width: 100%;
    aspect-ratio: 4/3;
    overflow: hidden;
    position: relative;
    cursor: pointer;
}

.result-image img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #f5f5f5;
}

.image-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(59, 130, 246, 0.65);
    backdrop-filter: blur(4px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: white;
    opacity: 0;
    transition: opacity 0.3s;
}

.result-image:hover .image-overlay {
    opacity: 1;
}

.result-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
}

.filename {
    font-size: 13px;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.confidence-text {
    font-weight: 600;
    color: var(--primary-color);
}

.bbox-text {
    font-size: 12px;
    color: var(--text-secondary);
    font-family: monospace;
}

:deep(.el-tag) {
    border: none;
}

:deep(.el-table) {
    border-radius: 12px;
    overflow: hidden;
}

:deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, #3b82f6, #60a5fa) !important;
}
</style>
