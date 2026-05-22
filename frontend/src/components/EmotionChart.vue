<template>
    <div class="emotion-chart">
        <div ref="chartRef" class="chart-container"></div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
    data: {
        type: Object,
        required: true
    },
    type: {
        type: String,
        default: 'pie'
    }
})

const chartRef = ref(null)
let chart = null

const emotionLabels = {
    surprise: '惊讶', joy: '快乐', neutral: '中性',
    sadness: '悲伤', anger: '愤怒', disgust: '厌恶', fear: '恐惧'
}

const emotionColors = {
    surprise: '#f472b6', joy: '#34d399', neutral: '#fbbf24',
    sadness: '#a78bfa', anger: '#fb923c', disgust: '#a3e635', fear: '#22d3ee'
}

const initChart = () => {
    if (!chartRef.value) return
    chart = echarts.init(chartRef.value)
    updateChart()
}

const updateChart = () => {
    if (!chart) return

    let option = {}

    if (props.type === 'pie') {
        const pieData = Object.entries(props.data).map(([key, value]) => ({
            name: emotionLabels[key] || key,
            value: value,
            itemStyle: { color: emotionColors[key] || '#ccc' }
        }))

        option = {
            title: {
                text: '情感分布',
                left: 'center',
                textStyle: { fontSize: 16, fontWeight: 600, color: '#1e293b' }
            },
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                top: 'middle',
                textStyle: { fontSize: 12 }
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['60%', '55%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 8,
                    borderColor: '#fff',
                    borderWidth: 3
                },
                label: {
                    show: true,
                    formatter: '{b}\n{d}%',
                    fontSize: 12
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 14,
                        fontWeight: 'bold'
                    }
                },
                data: pieData
            }]
        }
    } else if (props.type === 'bar') {
        const categories = Object.keys(props.data).map(k => emotionLabels[k] || k)
        const values = Object.values(props.data)
        const colors = Object.keys(props.data).map(k => emotionColors[k] || '#ccc')

        option = {
            title: {
                text: '情感分布',
                left: 'center',
                textStyle: { fontSize: 16, fontWeight: 600, color: '#1e293b' }
            },
            tooltip: {
                trigger: 'axis',
                formatter: '{b}: {c}'
            },
            xAxis: {
                type: 'category',
                data: categories,
                axisLabel: { rotate: 30, fontSize: 11 }
            },
            yAxis: {
                type: 'value',
                name: '数量'
            },
            series: [{
                type: 'bar',
                data: values.map((v, i) => ({
                    value: v,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: colors[i] },
                            { offset: 1, color: colors[i] + '80' }
                        ])
                    }
                })),
                barWidth: '50%',
                itemStyle: {
                    borderRadius: [6, 6, 0, 0]
                }
            }]
        }
    }

    chart.setOption(option)
}

watch(() => props.data, () => {
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
    height: 300px;
}
</style>
