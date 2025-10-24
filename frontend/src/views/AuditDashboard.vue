<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">
        <i class="icon-shield"></i>
        <h1>数据智能核查助手</h1>
        <span class="version">Demo</span>
      </div>
    </header>

    <main class="main-layout">
      <aside class="left-panel">
        <div class="panel-card">
          <div class="section upload-section">
            <div class="section-header">
              <span class="section-step">01</span>
              <h2>上传数据库 Schema（SQL）</h2>
            </div>
            <div class="section-body">
              <div
                class="file-drop-area"
                @click="triggerFileUpload"
                :class="{ 'has-file': selectedFile, 'loading': loading }"
              >
                <i class="icon-upload"></i>
                <div v-if="!selectedFile" class="drop-hint">
                  <p class="hint-title">点击或拖拽文件到此处</p>
                  <p class="hint-desc">仅支持 .sql 格式文件</p>
                </div>
                <div v-if="selectedFile" class="file-info-card">
                  <div class="file-icon">
                    <i class="icon-file-text"></i>
                  </div>
                  <div class="file-meta">
                    <p class="file-name">{{ selectedFile.name }}</p>
                    <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
                  </div>
                  <button
                    class="file-remove-btn"
                    @click.stop="removeFile"
                    :disabled="loading"
                  >
                    <i class="icon-times"></i>
                  </button>
                </div>
                <input
                  type="file"
                  ref="fileInput"
                  class="file-input"
                  accept=".sql"
                  @change="handleFileChange"
                  :disabled="loading"
                >
              </div>
            </div>
          </div>

          <div class="section agent-section">
            <div class="section-header">
              <span class="section-step">02</span>
              <h2>选择核查矛盾类型</h2>
            </div>
            <div class="section-body">
              <div class="agents-list">
                <label
                  v-for="agent in agents"
                  :key="agent.value"
                  class="agent-item"
                  :class="{ 'disabled': loading }"
                >
                  <input
                    type="checkbox"
                    :value="agent.value"
                    v-model="selectedAgents"
                    :disabled="loading"
                  >
                  <span class="agent-checkmark"></span>
                  <span class="agent-label">{{ agent.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="section control-section">
            <div class="section-header">
              <span class="section-step">03</span>
              <h2>开始核查分析</h2>
            </div>
            <div class="section-body">
              <div class="control-buttons">
                <button
                  class="btn primary-btn"
                  :disabled="!canStart || loading"
                  @click="handleStart"
                >
                  <i class="icon-play" v-if="!loading"></i>
                  <i class="icon-spinner spin" v-if="loading"></i>
                  {{ loading ? '分析中...' : '开始分析' }}
                </button>
                <button
                  class="btn secondary-btn"
                  @click="handleReset"
                  :disabled="loading"
                >
                  <i class="icon-refresh"></i> 重置
                </button>
              </div>
              <p class="control-tip">可多选智能体同时运行核查</p>

              <div
                class="status-alert"
                v-if="message"
                :class="{ 'success': !message.includes('失败'), 'error': message.includes('失败') }"
              >
                <i class="icon-info-circle" v-if="!message.includes('失败')"></i>
                <i class="icon-exclamation-circle" v-if="message.includes('失败')"></i>
                <span class="alert-text">{{ message }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section class="right-panel">
        <div class="result-card">
          <div class="result-header">
            <h2>核查分析结果</h2>
            <div v-if="!loading && !isEmptyResults" class="result-stats">
              <span class="total-count">共{{ totalQuestions }}个核查项</span>
              <span class="active-agent">当前：{{ getAgentLabel(Object.keys(resultsByAgent)[activeTab] || '') }}</span>
            </div>
          </div>

          <div class="result-content">
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
              <p>正在执行核查分析，请稍候...</p>
            </div>

            <div v-else-if="isEmptyResults" class="empty-result-state">
              <div class="empty-icon">
                <i class="icon-search"></i>
              </div>
              <h3>暂无核查结果</h3>
              <p>请在左侧上传SQL文件并选择智能体，点击「开始分析」生成结果</p>
            </div>

            <div v-else class="result-container">
              <div class="agent-tabs">
                <button
                  v-for="(agent, index) in Object.keys(resultsByAgent)"
                  :key="agent"
                  class="agent-tab"
                  :class="{ 'active': activeTab === index }"
                  @click="activeTab = index"
                >
                  {{ getAgentLabel(agent) }}
                  <span class="tab-badge">{{ resultsByAgent[agent].questions?.length || 0 }}</span>
                </button>
              </div>

              <div class="agent-results">
                <div
                  v-for="(agent, index) in Object.keys(resultsByAgent)"
                  :key="agent"
                  class="result-panel"
                  :class="{ 'active': activeTab === index }"
                >
                  <div v-if="resultsByAgent[agent].status === 'error'" class="error-panel">
                    <i class="icon-exclamation-triangle"></i>
                    <div class="error-content">
                      <h4>核查失败</h4>
                      <p>{{ resultsByAgent[agent].error || '未知错误，请重试' }}</p>
                    </div>
                  </div>

                  <div v-else-if="resultsByAgent[agent].questions?.length" class="questions-container">
                    <div
                      v-for="(question, qIdx) in resultsByAgent[agent].questions"
                      :key="qIdx"
                      class="question-card"
                      @click="toggleQuestionExpand(qIdx)"
                      :class="{ 'expanded': expandedQuestion[agent] === qIdx }"
                    >
                      <div class="question-header">
                        <span class="question-index">{{ qIdx + 1 }}</span>
                        <h3 class="question-title">{{ question.title }}</h3>
                        <span class="expand-icon">
                          {{ expandedQuestion[agent] === qIdx ? '▼' : '▶' }}
                        </span>
                      </div>

                      <div class="question-desc">
                        {{ question.explanation_hint || '无风险说明' }}
                      </div>

                      <div class="question-data" v-if="expandedQuestion[agent] === qIdx">
                        <div class="rich-details-grid">

                          <div class="detail-item full-span">
                            <span class="detail-label">核查逻辑:</span>
                            <p class="detail-value logic">{{ question.logic_description }}</p>
                          </div>

                          <div class="detail-item full-span">
                            <span class="detail-label">核查建议:</span>
                            <p class="detail-value suggestion">{{ question.next_action_hint }}</p>
                          </div>

                          <div class="detail-item">
                            <span class="detail-label">主要实体:</span>
                            <p class="detail-value entity-tag primary" v-if="question.related_entities?.primary_table">
                              {{ question.related_entities.primary_table }}
                            </p>
                            <p v-else class="detail-value entity-tag secondary">无</p>
                          </div>
                          <div class="detail-item">
                            <span class="detail-label">关联实体:</span>
                            <div class="detail-value tags-container">
                              <span v-if="!question.related_entities?.secondary_tables?.length" class="entity-tag secondary">无</span>
                              <span v-else v-for="table in question.related_entities.secondary_tables" :key="table" class="entity-tag secondary">
                                {{ table }}
                              </span>
                            </div>
                          </div>

                          <div class="detail-item full-span">
                            <span class="detail-label">关键字段:</span>
                            <div class="detail-value tags-container">
                              <span v-if="!question.key_fields?.length" class="field-tag">无</span>
                              <span v-else v-for="field in question.key_fields" :key="field" class="field-tag">
                                {{ field }}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else class="no-issues-state">
                    <i class="icon-check-circle"></i>
                    <h3>未发现相关问题</h3>
                    <p>该智能体核查范围内的数据符合规范</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { analyzeSchema } from '../api.js' // 保留原有后端接口调用

// 1. 基础配置与静态数据
const agents = [
  { value: 'aggregate', label: '聚合/网络异常' },
  { value: 'binary', label: '状态矛盾' },
  { value: 'process', label: '流程/资格矛盾' },
  { value: 'quantitative', label: '数值会计不一致' },
  { value: 'temporal', label: '时间/因果矛盾' },
]

// 2. 响应式状态管理
const selectedFile = ref(null)       // 选中的SQL文件
const selectedAgents = ref([])       // 选中的智能体
const loading = ref(false)           // 分析加载状态
const message = ref('')              // 操作状态提示
const resultsByAgent = ref({})       // 按智能体分组的结果
const activeTab = ref(0)             // 右侧结果标签页激活态
const expandedQuestion = ref({})     // 问题展开状态（按智能体存储）

// 3. 计算属性
// 是否可开始分析（有文件+有选中智能体）
const canStart = computed(() => !!selectedFile.value && selectedAgents.value.length > 0)
// 是否无结果（结果对象为空）
const isEmptyResults = computed(() => Object.keys(resultsByAgent.value).length === 0)
// 总核查项数量
const totalQuestions = computed(() => {
  return Object.values(resultsByAgent.value).reduce((total, agentResult) => {
    return total + (agentResult.questions?.length || 0)
  }, 0)
})

// 4. 生命周期钩子
onMounted(() => {
  // 初始化页面布局（适配屏幕高度）
  adjustPageLayout()
  window.addEventListener('resize', adjustPageLayout)
})

onUnmounted(() => {
  window.removeEventListener('resize', adjustPageLayout)
})

// 5. 核心方法
/**
 * 调整页面布局（确保主体区域占满剩余高度）
 */
function adjustPageLayout() {
  const headerHeight = document.querySelector('.app-header').offsetHeight
  const mainLayout = document.querySelector('.main-layout')
  if (mainLayout) {
    mainLayout.style.height = `${window.innerHeight - headerHeight}px`
  }
}


/**
 * 触发文件上传（点击上传区域时调用）
 */
function triggerFileUpload() {
  if (!loading.value) {
    const fileInput = document.querySelector('.file-input')
    if (fileInput) fileInput.click()
  }
}

/**
 * 处理文件选择变化
 */
function handleFileChange(e) {
  const file = e.target.files[0]
  if (!file) return

  // 存储选中文件
  selectedFile.value = file

  // 重置之前的结果和提示
  message.value = ''
  resultsByAgent.value = {}
  // 记录日志（内部调试用）
  pushLog(`选中SQL文件：${file.name}`)

  // 重置文件输入框（允许重复选择同一文件）
  e.target.value = ''
}

/**
 * 移除选中的文件
 */
function removeFile() {
  selectedFile.value = null
  message.value = ''
  pushLog('已移除选中的SQL文件')
}

/**
 * 切换问题展开/收起状态
 */
function toggleQuestionExpand(qIdx) {
  const currentAgent = Object.keys(resultsByAgent.value)[activeTab.value]
  if (!currentAgent) return

  // 更新展开状态（同一智能体下只展开一个问题）
  expandedQuestion.value[currentAgent] = expandedQuestion.value[currentAgent] === qIdx ? -1 : qIdx
}

/**
 * 记录操作日志（内部调试用，不展示在页面）
 */
function pushLog(logMsg) {
  const time = new Date().toLocaleTimeString()
  console.log(`[${time}] ${logMsg}`)
}

/**
 * 格式化文件大小（B→KB→MB）
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

/**
 * 开始分析（调用后端接口）
 */
async function handleStart() {
  if (!canStart.value) {
    message.value = '请先上传SQL文件并选择至少一个智能体'
    return
  }

  // 初始化分析状态
  loading.value = true
  // message.value = `正在启动核查：${selectedAgents.value.map(getAgentLabel).join('、')}`
  resultsByAgent.value = {}
  expandedQuestion.value = {} // 重置问题展开状态
  pushLog(`开始分析，选中智能体：${selectedAgents.value.join(', ')}`)

  try {
    // 调用后端接口获取分析结果 (此函数来自 api.js)
    const response = await analyzeSchema(selectedFile.value, selectedAgents.value)

    // 处理后端返回结果
    // message.value = response?.message || '核查分析完成'
    const rawResults = response?.results_by_agent || {}

    // 格式化结果为前端可用结构
    const formattedResults = {}
    selectedAgents.value.forEach(agent => {
      const agentResult = rawResults[agent] || {}

      if (agentResult.status === 'success') {
        formattedResults[agent] = {
          status: 'success',
          questions: (agentResult.questions || []).map(q => ({
            id: q.id,
            title: q.title,
            logic_description: q.logic_description,
            conflict_type: q.conflict_type,
            related_entities: q.related_entities,
            key_fields: q.key_fields,
            explanation_hint: q.explanation_hint,
            next_action_hint: q.next_action_hint
          }))
        }
      } else {
        // 失败状态：记录错误信息
        formattedResults[agent] = {
          status: 'error',
          error: agentResult.error || '智能体分析失败',
          rawOutput: agentResult.raw_output,
          questions: [] // 保证 questions 数组存在
        }
      }
    })

    resultsByAgent.value = formattedResults
    pushLog('分析完成，结果已格式化')
    activeTab.value = 0 // 默认激活第一个智能体结果
  } catch (error) {
    // 捕获接口调用异常
    const errorMsg = error.detail || error.message || '网络异常，请重试'
    message.value = `分析失败：${errorMsg}`
    pushLog(`分析异常：${errorMsg}`)
  } finally {
    // 结束加载状态
    loading.value = false
  }
}

/**
 * 重置所有状态
 */
function handleReset() {
  selectedFile.value = null
  selectedAgents.value = []
  loading.value = false
  message.value = ''
  resultsByAgent.value = {}
  activeTab.value = 0
  expandedQuestion.value = {}
  pushLog('已重置所有操作状态')
}

/**
 * 根据智能体value获取label
 */
function getAgentLabel(agentValue) {
  const agent = agents.find(item => item.value === agentValue)
  return agent ? agent.label : '未知智能体'
}

</script>

<style>
/* 1. 基础样式重置与全局变量 */
:root {
  --primary: #165DFF;
  --primary-light: #E8F3FF;
  --primary-dark: #0E42D2;
  --success: #36D399;
  --error: #F87272;
  --warning: #FBBD23;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-light: #9CA3AF;
  --bg-main: #F9FAFB;
  --bg-card: #FFFFFF;
  --border-light: #E5E7EB;
  --border-dark: #D1D5DB;
  --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  --shadow-hover: 0 6px 16px rgba(0, 0, 0, 0.08);
  --transition: all 0.25s ease;
  --font-code: 'Consolas', 'Monaco', monospace;
}

/* [!!! 已修改 !!!] - 移除 body 边距 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* [!!! 已修改 !!!] - 移除 body 边距并禁止滚动 */
body {
  background-color: var(--bg-main);
  color: var(--text-primary);
  font-size: 14px;
  overflow: hidden; /* 禁止页面滚动 */
}

/* 2. 布局容器样式 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 97vh;
  margin: 0 auto; 
  overflow: hidden; /* 禁止容器滚动 */
}

/* 3. 顶部导航栏 */
.app-header {
  background-color: var(--primary);
  color: #FFFFFF;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* [!!! 已修改 !!!] - 调整图标大小以更好对齐 */
.logo .icon-shield {
  font-size: 20px;
}

.logo h1 {
  font-size: 18px;
  font-weight: 600;
  /* [!!! 已修改 !!!] - 确保h1没有奇怪的边距 */
  margin: 0;
  padding: 0;
  line-height: 1; /* 确保h1没有奇怪的行高 */
}

.logo .version {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: normal;
}

/* 4. 主体左右分栏布局 */
.main-layout {
  display: flex;
  flex: 1;
  gap: 24px;
  padding: 10px;
  height: calc(100vh - 64px); /* 撑满剩余高度 */
  overflow: hidden; /* 禁止布局滚动 */
}

/* 左侧功能操作区 */
.left-panel {
  width: 400px;
  flex-shrink: 0;
  overflow: hidden;
}

.panel-card {
  background-color: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow);
  /* [!!! 已修改 !!!] - 减小内边距和间距以“挤一挤” */
  padding: 18px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px; /* 从 28px 减小 */
  overflow: auto; /* 保留，以防万一内容还是溢出 */
}

/* 右侧结果展示区 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 500px;
}

.result-card {
  background-color: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  /* [!!! 已修改 !!!] - 确保 result-card 不会溢出 */
  overflow: hidden;
}

/* 5. 左侧功能区通用样式 */
.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-step {
  background-color: var(--primary);
  color: #FFFFFF;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.section-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 5.1 上传区域样式 */
.file-drop-area {
  border: 2px dashed var(--border-light);
  border-radius: 8px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
  background-color: var(--bg-main);
}

.file-drop-area:hover:not(.has-file):not(.loading) {
  border-color: var(--primary);
  background-color: var(--primary-light);
}

.file-drop-area.loading {
  cursor: not-allowed;
  opacity: 0.7;
}

.file-drop-area .icon-upload {
  font-size: 36px;
  color: var(--primary);
  margin-right: 16px;
}

.drop-hint {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hint-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.hint-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 选中文件后的样式 */
.file-info-card {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background-color: var(--primary-light);
  border-radius: 6px;
}

.file-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background-color: var(--primary);
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.file-icon .icon-file-text {
  font-size: 18px;
}

.file-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
}

.file-remove-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.file-remove-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--error);
}

.file-input {
  display: none;
}

/* 5.2 智能体选择样式 */
.agents-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: var(--transition);
}

.agent-item:hover:not(.disabled) {
  background-color: var(--primary-light);
}

.agent-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.agent-item input {
  display: none;
}

.agent-checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-dark);
  border-radius: 4px;
  display: inline-block;
  position: relative;
  transition: var(--transition);
}

.agent-item input:checked + .agent-checkmark {
  background-color: var(--primary);
  border-color: var(--primary);
}

.agent-item input:checked + .agent-checkmark::after {
  content: '✓';
  position: absolute;
  color: #FFFFFF;
  font-size: 12px;
  top: -2px;
  left: 2px;
}

.agent-label {
  font-size: 14px;
  color: var(--text-primary);
  flex: 1;
}

/* 5.3 操作控制样式 */
.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn {
  padding: 12px 16px;
  border-radius: 6px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: var(--transition);
}

.primary-btn {
  background-color: var(--primary);
  color: #FFFFFF;
}

.primary-btn:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.primary-btn:disabled {
  background-color: var(--border-light);
  cursor: not-allowed;
}

.secondary-btn {
  background-color: #FFFFFF;
  color: var(--text-primary);
  border: 1px solid var(--border-light);
}

.secondary-btn:hover:not(:disabled) {
  background-color: var(--bg-main);
  border-color: var(--border-dark);
}

.secondary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.control-tip {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 4px;
}

/* 状态提示框 */
.status-alert {
  padding: 12px 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.status-alert.success {
  background-color: rgba(54, 211, 153, 0.1);
  color: var(--success);
  border-left: 3px solid var(--success);
}

.status-alert.error {
  background-color: rgba(248, 114, 114, 0.1);
  color: var(--error);
  border-left: 3px solid var(--error);
}

.alert-text {
  flex: 1;
}

/* 6. 右侧结果区样式 */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.result-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.total-count {
  padding: 4px 8px;
  background-color: var(--primary-light);
  color: var(--primary);
  border-radius: 4px;
}

.result-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

/* 6.1 加载中状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(22, 93, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s linear infinite;
}

/* 6.2 无结果状态 */
.empty-result-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon .icon-search {
  font-size: 32px;
}

.empty-result-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 6.3 有结果状态 */
.result-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 智能体标签切换 */
.agent-tabs {
  display: flex;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
  overflow-x: auto;
  flex-shrink: 0;
}

.agent-tab {
  padding: 8px 16px;
  border-radius: 6px;
  background-color: var(--bg-main);
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 6px;
}

.agent-tab:hover:not(.active) {
  background-color: var(--primary-light);
  color: var(--primary);
}

.agent-tab.active {
  background-color: var(--primary);
  color: #FFFFFF;
}

.tab-badge {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 11px;
}

/* 智能体结果面板 */
.agent-results {
  flex: 1;
  overflow: auto;
  padding: 8px 0;
  /* 为滚动条留出空间 */
  padding-right: 8px;
}

.result-panel {
  display: none;
  height: 100%;
}

.result-panel.active {
  display: block;
}

/* 分析失败面板 */
.error-panel {
  background-color: rgba(248, 114, 114, 0.1);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.error-panel .icon-exclamation-triangle {
  font-size: 20px;
  color: var(--error);
  margin-top: 2px;
}

.error-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.error-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--error);
}

.error-content p {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 问题卡片样式 */
.questions-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-card {
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: var(--transition);
}

.question-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow);
}

.question-card.expanded {
  border-color: var(--primary);
  background-color: #FBFCFF; /* 展开时一个非常淡的背景色 */
}

/* 问题标题栏 */
.question-header {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--primary);
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.question-title {
  font-size: 15px; /* 标题稍大一点 */
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.expand-icon {
  font-size: 16px;
  color: var(--primary);
  font-weight: bold;
}

/* 问题描述 */
.question-desc {
  padding: 0 16px 16px;
  padding-left: 52px; /* (24px index + 12px gap + 16px padding) */
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 展开区域 */
.question-data {
  padding: 16px;
  background-color: #FFFFFF;
  border-top: 1px solid var(--primary-light);
  padding-left: 52px;
}

.rich-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr; /* 默认两列 */
  gap: 16px 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-item.full-span {
  grid-column: 1 / -1; /* 跨越所有列 */
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.detail-value.logic,
.detail-value.suggestion {
  background-color: var(--bg-main);
  border-radius: 6px;
  padding: 10px 12px;
  font-family: var(--font-code);
  border: 1px solid var(--border-light);
}

.detail-value.suggestion {
  color: var(--primary-dark);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-tag, .field-tag {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  font-family: var(--font-code);
}

.entity-tag.primary {
  background-color: var(--primary-light);
  color: var(--primary-dark);
  border: 1px solid var(--primary);
}

.entity-tag.secondary {
  background-color: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
}

.field-tag {
  background-color: #F3F4F6;
  color: #4B5563;
  border: 1px solid var(--border-light);
  border-radius: 4px;
}


/* 无数据样式 */
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  gap: 8px;
  color: var(--text-secondary);
}

.no-data .icon-database {
  font-size: 32px;
  color: var(--border-dark);
}

.no-data p {
  font-size: 14px;
}

.data-tip {
  font-size: 12px;
  color: var(--text-light);
}

/* 预留数据表格样式 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.data-table th {
  background-color: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}

.data-table tr:hover {
  background-color: var(--bg-main);
}

/* 无问题状态 */
.no-issues-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
}

.no-issues-state .icon-check-circle {
  font-size: 48px;
  color: var(--success);
}

.no-issues-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--success);
}

/* 7. 图标样式定义 */
.icon-shield::before { content: '🛡️'; }
.icon-upload::before { content: '📤'; }
.icon-file-text::before { content: '📄'; }
.icon-times::before { content: '✕'; }
.icon-play::before { content: '▶️'; }
.icon-refresh::before { content: '🔄'; }
.icon-spinner::before { content: '⏳'; }
.icon-info-circle::before { content: 'ℹ️'; }
.icon-exclamation-circle::before { content: '❗'; }
.icon-search::before { content: '🔍'; }
.icon-check-circle::before { content: '✅'; }
.icon-exclamation-triangle::before { content: '⚠️'; }
.icon-database::before { content: '🗄️'; }
.icon-copy::before { content: '📋'; }

/* 8. 响应式适配（屏幕宽度<1200px时） */
@media (max-width: 1200px) {
  .main-layout {
    flex-direction: column;
    gap: 20px;
    padding: 16px;
    height: calc(100vh - 64px);
  }

  .left-panel {
    width: 100%;
    flex-shrink: 0; /* 防止左侧面板被过度压缩 */
  }

  .panel-card {
    height: 100%;
    overflow: auto;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .result-stats {
    width: 100%;
    justify-content: space-between;
  }

  .rich-details-grid {
    grid-template-columns: 1fr; /* 在较小屏幕上变为单列 */
  }
}

/* 屏幕宽度<768px时 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }

  .logo h1 {
    font-size: 16px;
  }

  .file-drop-area {
    flex-direction: column;
    padding: 16px;
  }

  .file-drop-area .icon-upload {
    margin-right: 0;
    margin-bottom: 12px;
  }

  .question-header {
    padding: 12px;
    gap: 8px;
  }

  .question-title {
    font-size: 14px; /* 移动端标题 */
  }

  .question-desc {
    padding-left: 44px; /* (24px index + 8px gap + 12px padding) */
  }
  .question-data {
    padding-left: 16px; /* 移动端展开时，不需要对齐 */
  }
}
</style>