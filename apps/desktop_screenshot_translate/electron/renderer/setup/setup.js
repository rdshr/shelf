const state = {
  displayName: 'AiTrans 截图翻译',
  configured: false,
};

function setStatus(message, tone = 'info') {
  const status = document.getElementById('status');
  status.textContent = message;
  status.dataset.tone = tone;
}

function setHint(message) {
  document.getElementById('hint').textContent = message;
}

function syncForm(guide) {
  const baseUrlInput = document.getElementById('baseUrl');
  const apiKeyInput = document.getElementById('apiKey');
  const runtimeDraft = guide?.runtimeDraft || {};

  if (document.activeElement !== baseUrlInput) {
    baseUrlInput.value = runtimeDraft.baseUrl || '';
  }
  if (document.activeElement !== apiKeyInput && !runtimeDraft.apiKeyPresent) {
    apiKeyInput.value = '';
  }
}

function render(payload) {
  const displayName = payload?.product?.displayName || state.displayName;
  const guide = payload?.guide || {};
  const configured = Boolean(guide.configured);

  state.displayName = displayName;
  state.configured = configured;

  document.getElementById('displayName').textContent = displayName;
  document.getElementById('configPath').textContent = guide.runtimeOverridesPath || '未检测到配置路径';

  syncForm(guide);

  if (configured) {
    setStatus('翻译端点已可用，可以直接开始截图', 'success');
    setHint('保存后立即生效，不需要重新安装。你可以直接回到托盘开始截图。');
  } else {
    setStatus('尚未完成翻译端点配置，请先填写并保存 base_url / api_key', 'warning');
    setHint('优先通过本窗口完成配置；只有在高级排障时才需要手动打开配置文件。');
  }
}

async function refreshGuide() {
  const guide = await window.aitransDesktop.getSetupGuideState();
  render({
    product: {
      displayName: state.displayName,
    },
    guide,
  });
}

window.aitransDesktop.onSetupData((payload) => {
  render(payload);
});

document.getElementById('setupForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const saveButton = document.getElementById('save');
  const baseUrl = document.getElementById('baseUrl').value.trim();
  const apiKey = document.getElementById('apiKey').value.trim();

  saveButton.disabled = true;
  setStatus('正在保存配置…', 'info');

  try {
    const result = await window.aitransDesktop.saveSetupConfig({ baseUrl, apiKey });
    if (!result?.ok) {
      setStatus(result?.error || '保存配置失败', 'error');
      return;
    }
    render({
      product: {
        displayName: state.displayName,
      },
      guide: result.guide || {},
    });
    setStatus('配置已保存，可以直接开始截图翻译', 'success');
  } finally {
    saveButton.disabled = false;
  }
});

document.getElementById('openFile').addEventListener('click', async () => {
  await window.aitransDesktop.openConfigFile();
});

document.getElementById('openDir').addEventListener('click', async () => {
  await window.aitransDesktop.openConfigDirectory();
});

document.getElementById('copyPath').addEventListener('click', async () => {
  await window.aitransDesktop.copyConfigPath();
});

document.getElementById('refresh').addEventListener('click', async () => {
  await refreshGuide();
});

document.getElementById('close').addEventListener('click', async () => {
  await window.aitransDesktop.closeSetupGuide();
});

refreshGuide();
