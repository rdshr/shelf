const {
  resolveOpenAiApiKey,
  resolveOpenAiBaseUrl,
} = require('./provider-runtime');

const LANGUAGE_LABELS = {
  'zh-Hans': 'Simplified Chinese',
  zh: 'Chinese',
  en: 'English',
  ja: 'Japanese',
  auto: 'the detected source language',
};

function normalizeSourceText(sourceText) {
  if (typeof sourceText !== 'string') {
    return '';
  }
  return sourceText.trim();
}

function resolveTargetLanguage(productSpec) {
  const code = productSpec.pipeline.target_language;
  return LANGUAGE_LABELS[code] || code;
}

function extractResponseText(payload) {
  if (typeof payload.output_text === 'string' && payload.output_text.trim()) {
    return payload.output_text.trim();
  }
  if (!Array.isArray(payload.output)) {
    return '';
  }

  const fragments = [];
  for (const item of payload.output) {
    if (!item || !Array.isArray(item.content)) {
      continue;
    }
    for (const content of item.content) {
      if (content && typeof content.text === 'string' && content.text.trim()) {
        fragments.push(content.text.trim());
      }
    }
  }
  return fragments.join('\n').trim();
}

function extractChatCompletionText(payload) {
  const choice = Array.isArray(payload.choices) ? payload.choices[0] : null;
  const content = choice?.message?.content;
  if (typeof content === 'string' && content.trim()) {
    return content.trim();
  }
  if (!Array.isArray(content)) {
    return '';
  }

  const fragments = [];
  for (const item of content) {
    if (item && typeof item.text === 'string' && item.text.trim()) {
      fragments.push(item.text.trim());
    }
  }
  return fragments.join('\n').trim();
}

function buildOpenAiHeaders(baseUrl) {
  const headers = {
    'Content-Type': 'application/json',
  };
  const apiKey = resolveOpenAiApiKey(baseUrl);
  if (apiKey) {
    headers.Authorization = `Bearer ${apiKey}`;
  }
  return headers;
}

async function translateWithOpenAI(sourceText, productSpec, implementationConfig) {
  const controller = new AbortController();
  const timeoutMs = Math.max(1500, Math.min(productSpec.pipeline.timeout_budget_ms, 8000));
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const baseUrl = resolveOpenAiBaseUrl();
  const apiMode = implementationConfig.providers.translation_api;

  try {
    const instructions = [
      'You are a translation engine.',
      `Translate the user text into ${resolveTargetLanguage(productSpec)}.`,
      'Return only the translated text.',
      'Preserve line breaks and simple formatting where possible.',
      'Do not explain the translation.',
    ].join(' ');

    let endpoint = `${baseUrl}/responses`;
    let requestBody = {
      model: implementationConfig.providers.translation_model,
      instructions,
      input: sourceText,
    };

    if (apiMode === 'openai_compatible') {
      endpoint = `${baseUrl}/chat/completions`;
      requestBody = {
        model: implementationConfig.providers.translation_model,
        temperature: 0.2,
        messages: [
          { role: 'system', content: instructions },
          { role: 'user', content: sourceText },
        ],
      };
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: buildOpenAiHeaders(baseUrl),
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`openai_translation ${response.status}: ${errorText}`);
    }

    const payload = await response.json();
    const translatedText =
      apiMode === 'openai_compatible'
        ? extractChatCompletionText(payload)
        : extractResponseText(payload);
    if (!translatedText) {
      throw new Error('openai_translation response did not contain translated text');
    }
    return {
      provider: 'openai_translation',
      translatedText,
      diagnostics: {
        apiMode,
        baseUrl,
        model: implementationConfig.providers.translation_model,
        responseId: payload.id || null,
      },
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

async function translateWithFallbackStub(sourceText, productSpec) {
  const normalized = normalizeSourceText(sourceText);
  return {
    provider: 'fallback_stub',
    translatedText: normalized
      ? `Stub Translation (${productSpec.pipeline.target_language}): ${normalized}`
      : 'OCR 未返回可翻译文本，当前未调用远端翻译 provider。',
    diagnostics: {
      reason: normalized ? 'fallback_stub_applied' : 'empty_source_text',
    },
  };
}

async function translateText(sourceText, productSpec, implementationConfig) {
  const normalizedSourceText = normalizeSourceText(sourceText);
  if (!normalizedSourceText) {
    return translateWithFallbackStub('', productSpec);
  }

  const failures = [];

  for (const provider of implementationConfig.providers.translation_chain) {
    try {
      if (provider === 'openai_translation') {
        return await translateWithOpenAI(normalizedSourceText, productSpec, implementationConfig);
      }
      if (provider === 'fallback_stub') {
        return await translateWithFallbackStub(normalizedSourceText, productSpec);
      }
      failures.push(`${provider}: unsupported provider`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failures.push(`${provider}: ${message}`);
    }
  }

  throw new Error(`no translation provider succeeded: ${failures.join(' | ')}`);
}

module.exports = {
  translateText,
};
