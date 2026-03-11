function render(payload) {
  const displayName = payload?.product?.displayName || 'AiTrans 截图翻译';
  const guide = payload?.guide || {};
  const configured = Boolean(guide.configured);

  document.getElementById('displayName').textContent = displayName;
  document.getElementById('status').textContent = configured
    ? '翻译端点已可用，可以直接开始截图'
    : '尚未完成翻译端点配置，请先补齐 base_url / api_key';
  document.getElementById('configPath').textContent = guide.runtimeOverridesPath || '未检测到配置路径';
}

async function refreshGuide() {
  const guide = await window.aitransDesktop.getSetupGuideState();
  render({
    product: {
      displayName: 'AiTrans 截图翻译',
    },
    guide,
  });
}

window.aitransDesktop.onSetupData((payload) => {
  render(payload);
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
