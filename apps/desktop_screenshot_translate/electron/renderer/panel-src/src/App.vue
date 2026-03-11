<script setup>
import { computed, reactive } from 'vue';

function createEmptyPayload() {
  return {
    product: {
      displayName: 'AiTrans 截图翻译',
      copy: {
        copy_success: '译文已复制',
        empty_translation: '完成截图后将在此显示译文。',
      },
    },
    result: {
      stageStatus: 'idle',
      errorOrigin: null,
      capturePreviewDataUrl: null,
      sourceText: '尚未捕获结果',
      translatedText: '完成截图后将在此显示译文结果。',
      selection: {
        width: 0,
        height: 0,
      },
      shortcut: 'CommandOrControl+Shift+1',
      captureMeta: null,
    },
  };
}

const appState = reactive({
  payload: createEmptyPayload(),
  copyButtonLabel: '复制译文',
  retrying: false,
});

const STAGE_LABELS = {
  idle: '待命',
  capturing: '抓取中',
  ocr_processing: '识别中',
  translation_processing: '翻译中',
  translation_ready: '已完成',
  failed: '失败',
};

const PIPELINE_STEPS = [
  { id: 'capturing', label: '截图' },
  { id: 'ocr_processing', label: '识别' },
  { id: 'translation_processing', label: '翻译' },
  { id: 'translation_ready', label: '交付' },
];

const statusText = computed(() => STAGE_LABELS[appState.payload.result.stageStatus] || '待命');
const selectionText = computed(() => {
  const selection = appState.payload.result.selection;
  return `区域：${selection.width} x ${selection.height}`;
});
const shortcutText = computed(() => `快捷键：${appState.payload.result.shortcut}`);
const providerText = computed(() => {
  const meta = appState.payload.result.captureMeta;
  if (!meta) {
    return '';
  }
  return `OCR: ${meta.ocrProvider} / TRANS: ${meta.translationProvider}`;
});
const isBusy = computed(() =>
  ['capturing', 'ocr_processing', 'translation_processing'].includes(appState.payload.result.stageStatus),
);
const canCopy = computed(() => !isBusy.value && Boolean(appState.payload.result.translatedText));
const showFailure = computed(() => appState.payload.result.stageStatus === 'failed');
const stagePills = computed(() => {
  const currentStage = appState.payload.result.stageStatus;
  const currentIndex = PIPELINE_STEPS.findIndex((item) => item.id === currentStage);
  return PIPELINE_STEPS.map((item, index) => ({
    ...item,
    active: item.id === currentStage,
    done: currentStage === 'translation_ready' ? index <= currentIndex : currentIndex >= 0 && index < currentIndex,
  }));
});
const translatedText = computed(() =>
  appState.payload.result.translatedText || appState.payload.product.copy.empty_translation,
);

async function handleCopy() {
  if (!canCopy.value) {
    return;
  }
  await window.aitransDesktop.copyTranslation(appState.payload.result.translatedText);
  appState.copyButtonLabel = appState.payload.product.copy.copy_success;
  window.setTimeout(() => {
    appState.copyButtonLabel = '复制译文';
  }, 1600);
}

async function handleClose() {
  await window.aitransDesktop.closePanel();
}

async function handleRecapture() {
  await window.aitransDesktop.recapture();
}

async function handleRetryTranslation() {
  if (isBusy.value) {
    return;
  }
  appState.retrying = true;
  try {
    await window.aitransDesktop.retryTranslation();
  } finally {
    appState.retrying = false;
  }
}

window.aitransDesktop.onPanelData((payload) => {
  appState.payload = payload;
  appState.copyButtonLabel = '复制译文';
  appState.retrying = false;
});

window.aitransDesktop.getProjectSummary().then((summary) => {
  if (appState.payload.result.stageStatus === 'idle') {
    appState.payload.result.shortcut = summary.shortcut;
  }
});
</script>

<template>
  <main class="panel-shell">
    <section class="hero-card">
      <div class="hero-brand">
        <div class="brand-mark" aria-hidden="true">
          <span class="brand-corner brand-corner--tl"></span>
          <span class="brand-corner brand-corner--tr"></span>
          <span class="brand-corner brand-corner--bl"></span>
          <span class="brand-corner brand-corner--br"></span>
          <span class="brand-line brand-line--top"></span>
          <span class="brand-line brand-line--bottom"></span>
        </div>
        <div>
          <div class="eyebrow">AiTrans · Screenshot Translate</div>
          <h1>{{ appState.payload.product.displayName }}</h1>
          <p class="hero-copy">截一块，立刻看到译文。当前主链已经接入本地 OCR 和兼容 OpenAI 的翻译端点。</p>
        </div>
      </div>
      <div class="hero-actions">
        <div class="status-badge" :data-state="appState.payload.result.stageStatus">{{ statusText }}</div>
        <button class="ghost-btn" @click="handleClose">{{ appState.payload.product.copy.close_label || '关闭' }}</button>
      </div>
    </section>

    <section class="stage-row">
      <div
        v-for="item in stagePills"
        :key="item.id"
        class="stage-pill"
        :data-active="item.active"
        :data-done="item.done"
      >
        <span class="stage-dot"></span>
        <span>{{ item.label }}</span>
      </div>
    </section>

    <section class="content-layout">
      <aside class="left-column">
        <section class="preview-card">
          <div class="card-head">
            <div class="content-label">截图预览</div>
            <div class="mini-badge">{{ selectionText }}</div>
          </div>
          <img
            v-if="appState.payload.result.capturePreviewDataUrl"
            class="preview-image"
            :src="appState.payload.result.capturePreviewDataUrl"
            alt="capture preview"
          />
          <div v-else class="preview-empty">完成截图后，这里会显示本地裁剪预览。</div>
        </section>

        <section class="meta-card">
          <div class="content-label">执行信息</div>
          <div class="meta-stack">
            <div class="meta-item">
              <span class="meta-key">入口</span>
              <span class="meta-value">{{ shortcutText }}</span>
            </div>
            <div v-if="providerText" class="meta-item">
              <span class="meta-key">Provider</span>
              <span class="meta-value">{{ providerText }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-key">状态</span>
              <span class="meta-value">{{ statusText }}</span>
            </div>
          </div>
        </section>
      </aside>

      <section class="right-column">
        <section v-if="showFailure" class="status-card status-card--error">
          <div class="status-label">{{ appState.payload.product.copy.failure_title || '翻译失败' }}</div>
          <div class="status-error">
            {{ appState.payload.result.errorOrigin || '主链执行失败，请检查 OCR、翻译端点或当前 Windows 权限状态。' }}
          </div>
        </section>

        <section class="content-grid">
          <article class="content-card">
            <div class="card-head">
              <div class="content-label">原文</div>
            </div>
            <pre class="content-body">{{ appState.payload.result.sourceText || '暂无原文' }}</pre>
          </article>
          <article class="content-card content-card--translated">
            <div class="card-head">
              <div class="content-label">译文</div>
              <div class="translation-chip">目标：{{ appState.payload.result.captureMeta?.targetLanguage || 'zh-Hans' }}</div>
            </div>
            <pre class="content-body content-body--translated">{{ translatedText }}</pre>
          </article>
        </section>

        <section class="action-row">
          <button class="primary-btn" :disabled="!canCopy" @click="handleCopy">
            {{ isBusy ? '处理中…' : appState.copyButtonLabel }}
          </button>
          <button class="secondary-btn" :disabled="isBusy || appState.retrying" @click="handleRetryTranslation">
            {{ appState.retrying ? '重试中…' : (appState.payload.product.copy.retry_label || '重试翻译') }}
          </button>
          <button class="secondary-btn secondary-btn--ghost" :disabled="isBusy" @click="handleRecapture">
            {{ appState.payload.product.copy.recapture_label || '重新截图' }}
          </button>
        </section>
      </section>
    </section>
  </main>
</template>
