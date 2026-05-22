<template>
    <div class="emotion-timeline">
        <div ref="chartRef" class="chart-container"></div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
    segments: {
        type: Array,
        required: true
    }
})

const chartRef = ref(null)
let chart = null

const emotionLabels = {
    surprise: '惊讶', joy: '快乐', neutral: '中性',
    sadness: '悲伤', anger: '愤怒', disgust: '厌恶', fear: '恐惧'
}

const emotionColors = {
    surprise: '#f986a8', joy: '#9adbc5', neutral: '#fbf1d7',
    sadness: '#8477c6', anger: '#fe8d6f', disgust: '#b2cf98', fear: '#72bcec'
}

const initChart = () => {
    if (!chartRef.value) return
    chart = echarts.init(chartRef.value)
    updateChart()
}

const updateChart = () => {
    if (!chart || !props.segments.length) return

    const categories = props.segments.map(s => `片段 ${s.id}`)
    const data = props.segments.map(s => ({
        value: s.duration,
        itemStyle: { color: emotionColors[s.emotion] || '#ccc' }
    }))

    const option = {
        title: {
            text: '各片段情感分布',
            left: 'center',
            textStyle: { fontSize: 16 }
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                const idx = params[0].dataIndex
                const seg = props.segments[idx]
                return `片段 ${seg.id}<br/>` +
                    `时间: ${seg.start}s - ${seg.end}s<br/>` +
                    `情感: ${emotionLabels[seg.emotion]}<br/>` +
                    `置信度: ${(seg.confidence * 100).toFixed(1)}%<br/>` +
                    `字幕: ${seg.text?.substring(0, 30) || '无'}...`
            }
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: { rotate: 45 }
        },
        yAxis: {
            type: 'value',
            name: '时长(秒)'
        },
        series: [{
            type: 'bar',
            data: data,
            barWidth: '60%',
            itemStyle: {
                borderRadius: [4, 4, 0, 0]
            },
            label: {
                show: true,
                position: 'top',
                formatter: function(params) {
                    const seg = props.segments[params.dataIndex]
                    return emotionLabels[seg.emotion]
                }
            }
        }]
    }

    chart.setOption(option)
}

watch(() => props.segments, () => {
    nextTick(updateChart)
}, { deep: true })

onMounted(() => {
    initChart()
    window.addEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.chart-container {
    width: 100%;
    height: 350px;
}
</style>
