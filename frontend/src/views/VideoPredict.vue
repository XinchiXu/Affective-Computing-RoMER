<template>
    <div class="video-predict">
        <el-card class="upload-card glass-card">
            <template #header>
                <div class="card-header">
                    <div>
                        <h3>视频情感识别</h3>
                        <p>上传视频文件和对应的字幕文件（.srt），系统将识别对话中说话人的情感</p>
                    </div>
                </div>
            </template>

            <el-form :model="form" label-width="100px">
                <el-form-item label="视频文件">
                    <el-upload
                        ref="videoUploadRef"
                        class="upload-area"
                        drag
                        :auto-upload="false"
                        :on-change="handleVideoChange"
                        :on-remove="handleVideoRemove"
                        :limit="1"
                        :on-exceed="handleVideoExceed"
                        accept="video/*"
                    >
                        <el-icon class="el-icon--upload"><VideoCamera /></el-icon>
                        <div class="el-upload__text">
                            拖拽视频文件到此处，或 <em>点击上传</em>
                        </div>
                        <template #tip>
                            <div class="el-upload__tip">
                                支持 mp4/avi/mov 格式
                            </div>
                        </template>
                    </el-upload>
                </el-form-item>

                <el-form-item label="字幕文件">
                    <el-upload
                        ref="subtitleUploadRef"
                        class="upload-area"
                        drag
                        :auto-upload="false"
                        :on-change="handleSubtitleChange"
                        :on-remove="handleSubtitleRemove"
                        :limit="1"
                        :on-exceed="handleSubtitleExceed"
                        accept=".srt"
                    >
                        <el-icon class="el-icon--upload"><Document /></el-icon>
                        <div class="el-upload__text">
                            拖拽字幕文件到此处，或 <em>点击上传</em>
                        </div>
                        <template #tip>
                            <div class="el-upload__tip">
                                仅支持 srt 格式的字幕文件
                            </div>
                        </template>
                    </el-upload>
                </el-form-item>
            </el-form>

            <div class="action-bar">
                <el-button
                    type="primary"
                    size="large"
                    :loading="loading"
                    :disabled="!canSubmit"
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
                    :stroke-width="12"
                    :format="progressFormat"
                    striped
                    :striped-flow="progress.status === 'running'"
                />
                <div class="progress-info">
                    <div class="progress-step">
                        <el-icon><Promotion /></el-icon>
                        <span>当前步骤：{{ progress.current_step }}</span>
                    </div>
                    <div class="progress-message">
                        {{ progress.message }}
                    </div>
                </div>
                <div class="progress-steps">
                    <div
                        v-for="(step, index) in progressSteps"
                        :key="index"
                        class="step-item"
                        :class="{
                            'active': progress.progress >= step.threshold,
                            'current': isCurrentStep(step.threshold)
                        }"
                    >
                        <div class="step-icon">
                            <el-icon v-if="progress.progress >= step.threshold"><Check /></el-icon>
                            <span v-else>{{ index + 1 }}</span>
                        </div>
                        <div class="step-label">{{ step.label }}</div>
                    </div>
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

        <!-- 关键帧预览 -->
        <el-card v-if="keyframes.length" class="keyframes-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>关键帧预览</h3>
                    <span class="tip">点击可放大查看</span>
                </div>
            </template>
            <div class="keyframes-grid">
                <div
                    v-for="(frame, index) in keyframes"
                    :key="index"
                    class="keyframe-item"
                    @click="previewKeyframe(frame)"
                >
                    <img :src="frame.url" :alt="`关键帧 ${index + 1}`" />
                    <div class="keyframe-time">{{ frame.time }}s</div>
                </div>
            </div>
        </el-card>

        <!-- 结果视频 -->
        <el-card v-if="result" class="result-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <polygon points="23,7 16,12 23,17" stroke="#3b82f6" stroke-width="2"/>
                            <rect x="1" y="5" width="15" height="14" rx="2" stroke="#3b82f6" stroke-width="2"/>
                        </svg>
                        识别结果
                    </h3>
                    <el-button type="primary" @click="downloadResult">
                        <el-icon><Download /></el-icon>
                        下载视频
                    </el-button>
                </div>
            </template>

            <div class="video-container">
                <video
                    ref="videoPlayer"
                    :src="videoUrl"
                    controls
                    preload="auto"
                    class="result-video"
                    @error="handleVideoError"
                    @loadeddata="handleVideoLoaded"
                >
                    您的浏览器不支持视频播放
                </video>
            </div>
            <div class="result-info">
                <span>文件名：{{ result.filename }}</span>
                <span v-if="videoLoaded" class="video-status">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="#10b981" stroke-width="2"/>
                        <polyline points="22,4 12,14.01 9,11.01" stroke="#10b981" stroke-width="2"/>
                    </svg>
                    可播放
                </span>
            </div>
        </el-card>

        <!-- 可视化图表 -->
        <el-card v-if="summary" class="chart-card glass-card">
            <template #header>
                <div class="card-header">
                    <h3>情感分析</h3>
                    <el-radio-group v-model="chartType" size="small">
                        <el-radio-button label="pie">饼图</el-radio-button>
                        <el-radio-button label="bar">柱状图</el-radio-button>
                    </el-radio-group>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="12">
                    <EmotionChart :data="summary.emotion_counts" :type="chartType" />
                </el-col>
                <el-col :span="12">
                    <EmotionTimeline v-if="segments.length" :segments="segments" />
                </el-col>
            </el-row>
        </el-card>

        <!-- 详情表格 -->
        <el-card v-if="segments.length" class="detail-card glass-card">
            <template #header>
                <h3>片段详情</h3>
            </template>
            <EmotionDetail :segments="segments" />
        </el-card>

        <!-- 使用说明 -->
        <el-card class="info-card glass-card">
            <template #header>
                <h3>使用说明</h3>
            </template>
            <el-steps :active="1" direction="vertical" :space="60">
                <el-step title="准备文件" description="准备好视频文件（.mp4）和对应的字幕文件（.srt）" />
                <el-step title="上传文件" description="将视频和字幕文件分别拖拽到对应区域" />
                <el-step title="开始识别" description="点击「开始识别」按钮，等待处理完成" />
                <el-step title="查看结果" description="识别完成后可在线预览并下载标注后的视频" />
            </el-steps>
        </el-card>

        <!-- 图片预览弹窗 -->
        <el-dialog v-model="previewVisible" title="关键帧预览" width="80%">
            <img :src="previewFrame?.url" style="width: 100%" />
            <template #footer>
                <span>时间点：{{ previewFrame?.time }}s</span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import EmotionChart from '../components/EmotionChart.vue'
import EmotionTimeline from '../components/EmotionTimeline.vue'
import EmotionDetail from '../components/EmotionDetail.vue'
import EmotionStats from '../components/EmotionStats.vue'
import EmotionProbBar from '../components/EmotionProbBar.vue'

const videoUploadRef = ref(null)
const subtitleUploadRef = ref(null)
const videoPlayer = ref(null)

const form = ref({
    video: null,
    subtitle: null
})

const loading = ref(false)
const result = ref(null)
const summary = ref(null)
const segments = ref([])
const keyframes = ref([])
const chartType = ref('pie')
const taskId = ref(null)
const progress = ref(null)
const error = ref(null)
const videoError = ref(false)
const videoLoaded = false
const previewVisible = ref(false)
const previewFrame = ref(null)

let progressTimer = null

const progressSteps = [
    { label: '预处理', threshold: 5 },
    { label: '人脸检测', threshold: 30 },
    { label: '情感识别', threshold: 60 },
    { label: '视频处理', threshold: 70 },
    { label: '关键帧', threshold: 90 },
    { label: '完成', threshold: 100 }
]

const canSubmit = computed(() => {
    return form.value.video && form.value.subtitle
})

const videoUrl = computed(() => {
    if (!result.value?.url) return ''
    return result.value.url
})

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

const isCurrentStep = (threshold) => {
    if (!progress.value) return false
    const prevThreshold = progressSteps.find(s => s.threshold > progress.value.progress)?.threshold || 100
    return progress.value.progress < threshold && progress.value.progress >= (progressSteps[progressSteps.indexOf(progressSteps.find(s => s.threshold === threshold)) - 1]?.threshold || 0)
}

const progressFormat = (percentage) => {
    return `${percentage}%`
}

const handleVideoChange = (file) => {
    form.value.video = file.raw
}

const handleVideoRemove = () => {
    form.value.video = null
}

const handleVideoExceed = () => {
    ElMessage.warning('只能上传一个视频文件')
}

const handleSubtitleChange = (file) => {
    form.value.subtitle = file.raw
}

const handleSubtitleRemove = () => {
    form.value.subtitle = null
}

const handleSubtitleExceed = () => {
    ElMessage.warning('只能上传一个字幕文件')
}

const handleClear = () => {
    form.value.video = null
    form.value.subtitle = null
    result.value = null
    summary.value = null
    segments.value = []
    keyframes.value = []
    taskId.value = null
    progress.value = null
    error.value = null
    videoError.value = false
    videoUploadRef.value?.clearFiles()
    subtitleUploadRef.value?.clearFiles()
    stopProgressPolling()
}

const handleVideoError = (e) => {
    console.warn('视频播放错误，尝试重新加载:', e)
    // 尝试重新加载视频
    if (videoPlayer.value) {
        setTimeout(() => {
            videoPlayer.value.load()
        }, 1000)
    }
}

const handleVideoLoaded = () => {
    videoLoaded.value = true
    console.log('视频加载成功')
}

const previewKeyframe = (frame) => {
    previewFrame.value = frame
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
                // 获取结果
                const resultData = response.data.result
                if (resultData) {
                    if (resultData.video_filename) {
                        result.value = {
                            filename: resultData.video_filename,
                            url: `/api/result/video/${resultData.video_filename}`
                        }
                    }
                    summary.value = resultData.summary
                    segments.value = resultData.segments || []
                    keyframes.value = resultData.keyframes || []
                }
                ElMessage.success('视频识别完成')
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
    }, 2000) // 增加到2秒，减少请求频率
}

const stopProgressPolling = () => {
    if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
    }
}

const handlePredict = async () => {
    if (!canSubmit.value) {
        ElMessage.warning('请上传视频和字幕文件')
        return
    }

    loading.value = true
    result.value = null
    summary.value = null
    segments.value = []
    keyframes.value = []
    error.value = null
    videoError.value = false

    try {
        const formData = new FormData()
        formData.append('video', form.value.video)
        formData.append('subtitle', form.value.subtitle)

        const response = await axios.post('/api/predict/video', formData, {
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

const downloadResult = () => {
    if (!result.value) return
    const link = document.createElement('a')
    link.href = result.value.url
    link.download = result.value.filename
    link.click()
}

onUnmounted(() => {
    stopProgressPolling()
})
</script>

<style scoped>
.video-predict {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 磨砂玻璃卡片 */
.glass-card {
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08) !important;
}

.upload-card,
.result-card,
.info-card,
.stats-card,
.chart-card,
.detail-card,
.progress-card,
.keyframes-card {
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

.card-header .tip {
    color: var(--text-secondary);
    font-size: 12px;
}

.upload-area {
    width: 100%;
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
    padding: 16px 0;
}

.progress-info {
    margin-top: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.progress-step {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--primary-color);
    font-weight: 500;
}

.progress-message {
    color: var(--text-secondary);
    font-size: 13px;
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
}

.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 1;
}

.step-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--bg-color);
    border: 2px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: var(--text-secondary);
    transition: all 0.3s ease;
}

.step-item.active .step-icon {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: white;
}

.step-item.current .step-icon {
    border-color: var(--primary-color);
    color: var(--primary-color);
    box-shadow: 0 0 0 4px var(--primary-bg);
}

.step-label {
    font-size: 12px;
    color: var(--text-secondary);
}

.step-item.active .step-label {
    color: var(--primary-color);
    font-weight: 500;
}

/* 关键帧预览 */
.keyframes-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.keyframe-item {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s ease;
    aspect-ratio: 16/9;
}

.keyframe-item:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-lg);
}

.keyframe-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.keyframe-time {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}

/* 视频容器 */
.video-container {
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
    border-radius: 12px;
    overflow: hidden;
    background: #000;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.result-video {
    width: 100%;
    display: block;
}

.video-error {
    text-align: center;
    padding: 40px;
    color: #fff;
}

.video-error p {
    margin: 16px 0;
    font-size: 14px;
}

.result-info {
    text-align: center;
    margin-top: 16px;
    color: var(--text-secondary);
    font-size: 13px;
}
</style>
