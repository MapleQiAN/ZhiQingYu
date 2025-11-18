<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1 class="settings-title">{{ $t('settings.title') }}</h1>
    </div>

    <div class="settings-content">
      <!-- 语言设置 -->
      <n-card class="warm-card settings-card" hoverable>
        <div class="card-header">
          <div class="card-icon">🌐</div>
          <h2 class="card-title">{{ $t('settings.language') }}</h2>
        </div>
        <div class="card-content">
          <n-radio-group v-model:value="currentLocale" @update:value="handleLocaleChange">
            <n-space>
              <n-radio value="zh" label="中文" />
              <n-radio value="en" label="English" />
            </n-space>
          </n-radio-group>
        </div>
      </n-card>

      <!-- AI设置 -->
      <n-card class="warm-card settings-card" hoverable>
        <div class="card-header">
          <div class="card-icon">🤖</div>
          <h2 class="card-title">{{ $t('settings.aiSettings') }}</h2>
        </div>
        <div class="card-content">
          <p class="section-desc">{{ $t('settings.aiSettingsDesc') }}</p>
          
          <!-- 加载状态 -->
          <div v-if="loadingConfigs" class="loading-wrapper">
            <n-spin size="small" />
            <span class="loading-text">{{ $t('settings.loading') }}</span>
          </div>

          <!-- 配置列表 -->
          <div v-else-if="configs.length > 0" class="config-list">
            <div
              v-for="config in configs"
              :key="config.id"
              :class="['config-item', { active: config.is_active }]"
            >
              <div class="config-header">
                <div class="config-info">
                  <span class="config-provider">{{ getProviderLabel(config.provider) }}</span>
                  <n-tag
                    :type="config.is_active ? 'success' : 'default'"
                    size="small"
                    class="config-status"
                  >
                    {{ config.is_active ? $t('settings.active') : $t('settings.inactive') }}
                  </n-tag>
                </div>
                <div class="config-actions">
                  <n-button
                    size="small"
                    @click="handleEditConfig(config)"
                    class="action-button"
                  >
                    {{ $t('settings.updateConfig') }}
                  </n-button>
                  <n-button
                    v-if="!config.is_active"
                    type="primary"
                    size="small"
                    @click="handleActivateConfig(config.provider)"
                    :loading="activating === config.provider"
                    class="action-button"
                  >
                    {{ $t('settings.activate') }}
                  </n-button>
                </div>
              </div>
              <div class="config-details">
                <div v-if="config.model" class="config-detail">
                  <span class="detail-label">{{ $t('settings.model') }}:</span>
                  <span class="detail-value">{{ config.model }}</span>
                </div>
                <div v-if="config.base_url" class="config-detail">
                  <span class="detail-label">{{ $t('settings.baseUrl') }}:</span>
                  <span class="detail-value">{{ config.base_url }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 无配置提示 -->
          <div v-else class="no-config">
            <p>{{ $t('settings.noConfig') }}</p>
          </div>

          <!-- 创建/编辑配置表单 -->
          <n-divider />
          <n-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-placement="left"
            label-width="100"
            class="ai-config-form"
          >
            <n-form-item :label="$t('settings.provider')" path="provider">
              <n-select
                v-model:value="formData.provider"
                :options="providerOptions"
                :placeholder="$t('settings.selectProvider')"
                :disabled="!!editingConfig"
                @update:value="handleProviderChange"
              />
            </n-form-item>

            <n-form-item :label="$t('settings.apiKey')" path="api_key">
              <n-input
                v-model:value="formData.api_key"
                type="password"
                show-password-on="click"
                :placeholder="$t('settings.apiKeyPlaceholder')"
                :disabled="formData.provider === 'ollama'"
              />
              <template v-if="formData.provider === 'ollama'" #feedback>
                <span class="form-hint">{{ $t('settings.ollamaNoApiKey') }}</span>
              </template>
            </n-form-item>

            <n-form-item :label="$t('settings.baseUrl')" path="base_url">
              <n-input
                v-model:value="formData.base_url"
                :placeholder="getBaseUrlPlaceholder()"
              />
              <template #feedback>
                <span class="form-hint">{{ $t('settings.defaultBaseUrl') }}: {{ getDefaultBaseUrl() }}</span>
              </template>
            </n-form-item>

            <n-form-item :label="$t('settings.model')" path="model">
              <n-input
                v-model:value="formData.model"
                :placeholder="$t('settings.modelPlaceholder')"
              />
            </n-form-item>

            <n-form-item>
              <n-space>
                <n-button
                  type="primary"
                  @click="handleSaveConfig"
                  :loading="saving"
                >
                  {{ editingConfig ? $t('settings.updateConfig') : $t('settings.createConfig') }}
                </n-button>
                <n-button
                  v-if="editingConfig"
                  @click="handleCancelEdit"
                >
                  {{ $t('common.cancel') }}
                </n-button>
              </n-space>
            </n-form-item>
          </n-form>
        </div>
      </n-card>

      <!-- 关于 -->
      <n-card class="warm-card settings-card" hoverable>
        <div class="card-header">
          <div class="card-icon">ℹ️</div>
          <h2 class="card-title">{{ $t('settings.about') }}</h2>
        </div>
        <div class="card-content">
          <div class="about-content">
            <p class="app-name">{{ $t('common.appName') }}</p>
            <p class="app-version">{{ $t('settings.version') }}: 1.0.0</p>
            <p class="app-description">
              {{ $t('chat.welcomeDesc') }}
            </p>
          </div>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import {
  NCard,
  NRadioGroup,
  NRadio,
  NSpace,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  NTag,
  NDivider,
  NSpin,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  activateAIConfig,
  type AIConfig,
} from '@/lib/api'

const { locale, t } = useI18n()
const message = useMessage()
const currentLocale = ref(locale.value)
const formRef = ref<FormInst | null>(null)

// 同步 locale 变化
watch(() => locale.value, (newLocale) => {
  currentLocale.value = newLocale
})

const handleLocaleChange = (value: string) => {
  locale.value = value
  localStorage.setItem('locale', value)
}

// AI配置相关状态
const loadingConfigs = ref(false)
const configs = ref<AIConfig[]>([])
const activeProvider = ref<string | null>(null)
const saving = ref(false)
const activating = ref<string | null>(null)
const editingConfig = ref<AIConfig | null>(null)

const formData = ref({
  provider: '',
  api_key: '',
  base_url: '',
  model: '',
})

const formRules: FormRules = {
  provider: {
    required: true,
    message: () => t('settings.selectProvider'),
    trigger: ['blur', 'change'],
  },
  api_key: {
    validator: (rule, value) => {
      if (formData.value.provider === 'ollama') {
        return true
      }
      if (!value || value.trim() === '') {
        return new Error(t('settings.apiKeyPlaceholder'))
      }
      return true
    },
    trigger: ['blur', 'input'],
  },
}

const providerOptions = computed(() => [
  { label: t('settings.openai'), value: 'openai' },
  { label: t('settings.ollama'), value: 'ollama' },
  { label: t('settings.gemini'), value: 'gemini' },
  { label: t('settings.claude'), value: 'claude' },
  { label: t('settings.deepseek'), value: 'deepseek' },
  { label: t('settings.qwen'), value: 'qwen' },
  { label: t('settings.moonshot'), value: 'moonshot' },
  { label: t('settings.zhipu'), value: 'zhipu' },
  { label: t('settings.baidu'), value: 'baidu' },
  { label: t('settings.minimax'), value: 'minimax' },
  { label: t('settings.doubao'), value: 'doubao' },
])

// 获取提供商标签
const getProviderLabel = (provider: string) => {
  const option = providerOptions.value.find((opt) => opt.value === provider)
  return option ? option.label : provider
}

// 获取默认基础URL
const getDefaultBaseUrl = () => {
  const provider = formData.value.provider
  const urlMap: Record<string, string> = {
    openai: t('settings.openaiDefaultUrl'),
    ollama: t('settings.ollamaDefaultUrl'),
    gemini: t('settings.geminiDefaultUrl'),
    claude: t('settings.claudeDefaultUrl'),
    deepseek: t('settings.deepseekDefaultUrl'),
    qwen: t('settings.qwenDefaultUrl'),
    moonshot: t('settings.moonshotDefaultUrl'),
    zhipu: t('settings.zhipuDefaultUrl'),
    baidu: t('settings.baiduDefaultUrl'),
    minimax: t('settings.minimaxDefaultUrl'),
    doubao: t('settings.doubaoDefaultUrl'),
  }
  return urlMap[provider] || ''
}

// 获取基础URL占位符
const getBaseUrlPlaceholder = () => {
  const defaultUrl = getDefaultBaseUrl()
  return defaultUrl || t('settings.baseUrlPlaceholder')
}

// 提供商变化时设置默认URL
const handleProviderChange = (value: string) => {
  if (!formData.value.base_url) {
    formData.value.base_url = getDefaultBaseUrl()
  }
  // Ollama不需要API密钥
  if (value === 'ollama') {
    formData.value.api_key = ''
  }
}

// 加载配置列表
const loadConfigs = async () => {
  loadingConfigs.value = true
  try {
    const response = await getAIConfigs()
    if (response.error) {
      message.error(response.error.message || t('settings.saveFailed'))
      return
    }
    if (response.data) {
      configs.value = response.data.configs
      activeProvider.value = response.data.active_provider
    }
  } catch (error) {
    console.error('Failed to load configs:', error)
    message.error(t('settings.saveFailed'))
  } finally {
    loadingConfigs.value = false
  }
}

// 保存配置
const handleSaveConfig = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  saving.value = true
  try {
    if (editingConfig.value) {
      // 更新配置
      const response = await updateAIConfig(editingConfig.value.provider, {
        api_key: formData.value.api_key || null,
        base_url: formData.value.base_url || null,
        model: formData.value.model || null,
      })
      if (response.error) {
        message.error(response.error.message || t('settings.saveFailed'))
        return
      }
      message.success(t('settings.saveSuccess'))
    } else {
      // 创建配置
      const response = await createAIConfig({
        provider: formData.value.provider,
        api_key: formData.value.api_key || null,
        base_url: formData.value.base_url || null,
        model: formData.value.model || null,
      })
      if (response.error) {
        message.error(response.error.message || t('settings.saveFailed'))
        return
      }
      message.success(t('settings.saveSuccess'))
    }
    
    // 重置表单
    handleCancelEdit()
    // 重新加载配置列表
    await loadConfigs()
  } catch (error) {
    console.error('Failed to save config:', error)
    message.error(t('settings.saveFailed'))
  } finally {
    saving.value = false
  }
}

// 编辑配置
const handleEditConfig = (config: AIConfig) => {
  editingConfig.value = config
  formData.value = {
    provider: config.provider,
    api_key: config.api_key || '',
    base_url: config.base_url || '',
    model: config.model || '',
  }
}

// 取消编辑
const handleCancelEdit = () => {
  editingConfig.value = null
  formData.value = {
    provider: '',
    api_key: '',
    base_url: '',
    model: '',
  }
  formRef.value?.restoreValidation()
}

// 激活配置
const handleActivateConfig = async (provider: string) => {
  activating.value = provider
  try {
    const response = await activateAIConfig(provider)
    if (response.error) {
      message.error(response.error.message || t('settings.activateFailed'))
      return
    }
    message.success(t('settings.activateSuccess'))
    // 重新加载配置列表
    await loadConfigs()
  } catch (error) {
    console.error('Failed to activate config:', error)
    message.error(t('settings.activateFailed'))
  } finally {
    activating.value = null
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 0;
}

.settings-header {
  margin-bottom: 2rem;
  text-align: center;
}

.settings-title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 50%, #E8A5C4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: 1px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.warm-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 250, 245, 0.98) 100%) !important;
  border: 1px solid rgba(255, 182, 193, 0.25) !important;
  border-radius: 24px !important;
  box-shadow: 0 4px 24px rgba(255, 182, 193, 0.12) !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

.warm-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #FFB6C1 0%, #FFA07A 50%, #FFB6C1 100%);
  background-size: 200% 100%;
  animation: shimmer 3s infinite linear;
  opacity: 0;
  transition: opacity 0.3s ease;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.warm-card:hover {
  box-shadow: 0 8px 40px rgba(255, 182, 193, 0.2) !important;
  transform: translateY(-3px);
  border-color: rgba(255, 182, 193, 0.35) !important;
}

.warm-card:hover::before {
  opacity: 1;
}

.settings-card {
  padding: 1.5rem !important;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 182, 193, 0.2);
}

.card-icon {
  font-size: 28px;
  filter: drop-shadow(0 2px 6px rgba(255, 182, 193, 0.4));
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-block;
}

.warm-card:hover .card-icon {
  transform: scale(1.1) rotate(5deg);
  filter: drop-shadow(0 4px 8px rgba(255, 182, 193, 0.5));
}

.card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #8B6F7E;
  margin: 0;
  background: linear-gradient(135deg, #D9779F 0%, #C97A9A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.card-content {
  padding: 0.5rem 0;
}

.about-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.app-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #D9779F;
  margin: 0;
}

.app-version {
  font-size: 1rem;
  color: #8B6F7E;
  margin: 0;
}

.app-description {
  font-size: 1rem;
  color: #A68A8A;
  line-height: 1.6;
  margin: 0;
}

/* AI设置相关样式 */
.section-desc {
  font-size: 0.95rem;
  color: #8B6F7E;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.loading-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  justify-content: center;
}

.loading-text {
  color: #8B6F7E;
  font-size: 0.9rem;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.config-item {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 182, 193, 0.2);
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.config-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #FFB6C1 0%, #FFA07A 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.config-item:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 182, 193, 0.4);
  box-shadow: 0 2px 8px rgba(255, 182, 193, 0.15);
  transform: translateX(4px);
}

.config-item:hover::before {
  transform: scaleY(1);
}

.config-item.active {
  border-color: rgba(217, 119, 159, 0.5);
  background: rgba(255, 250, 245, 0.8);
  box-shadow: 0 2px 12px rgba(217, 119, 159, 0.2);
}

.config-item.active::before {
  transform: scaleY(1);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.config-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.config-provider {
  font-size: 1.1rem;
  font-weight: 600;
  color: #D9779F;
}

.config-status {
  margin-left: 0.5rem;
}

.config-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-button {
  font-size: 0.85rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 182, 193, 0.25);
}

.action-button:active {
  transform: translateY(0);
}

.config-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 182, 193, 0.15);
}

.config-detail {
  display: flex;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.detail-label {
  color: #8B6F7E;
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: #A68A8A;
  word-break: break-all;
}

.no-config {
  padding: 2rem;
  text-align: center;
  color: #A68A8A;
  font-size: 0.95rem;
}

.ai-config-form {
  margin-top: 1rem;
}

.form-hint {
  font-size: 0.85rem;
  color: #A68A8A;
  margin-top: 0.25rem;
  display: block;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 1rem;
  }

  .settings-title {
    font-size: 2rem;
  }

  .card-title {
    font-size: 1.25rem;
  }

  .config-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .config-actions {
    width: 100%;
  }

  .action-button {
    flex: 1;
  }
}
</style>

