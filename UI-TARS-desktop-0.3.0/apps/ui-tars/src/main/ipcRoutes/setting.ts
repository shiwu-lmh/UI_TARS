/**
 * Copyright (c) 2025 Bytedance, Inc. and its affiliates.
 * SPDX-License-Identifier: Apache-2.0
 */
import { OpenAI } from 'openai';
import { initIpc } from '@ui-tars/electron-ipc/main';
import { logger } from '../logger';
import { SettingStore } from '@main/store/setting';

const t = initIpc.create();

export const settingRoute = t.router({
  recognizeScreenshot: t.procedure
    .input<{
      imageBase64: string;
      mime: string;
    }>()
    .handle(async ({ input }) => {
      const { ocrBaseUrl, ocrApiKey, ocrModelName } = SettingStore.getStore();
      if (!ocrBaseUrl?.trim()) {
        throw new Error('请先在设置中填写 PaddleOCR-VL 服务地址');
      }
      if (!ocrModelName?.trim()) {
        throw new Error('请先在设置中填写 PaddleOCR-VL 模型名称');
      }
      if (!input.imageBase64 || !/^image\/[\w.+-]+$/.test(input.mime)) {
        throw new Error('截图数据无效');
      }

      const normalizedBaseUrl = ocrBaseUrl
        .trim()
        .replace(/\/+$/, '')
        .replace(/\/chat\/completions$/i, '');
      const openai = new OpenAI({
        apiKey: ocrApiKey?.trim() || 'no-api-key',
        baseURL: normalizedBaseUrl,
      });
      const completion = await openai.chat.completions.create({
        model: ocrModelName.trim(),
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: '请识别并完整输出这张截图中的所有文字，按阅读顺序分行或分段输出。相邻截图可能有重复内容，请完整识别，不要自行删减。',
              },
              {
                type: 'image_url',
                image_url: {
                  url: `data:${input.mime};base64,${input.imageBase64}`,
                },
              },
            ],
          },
        ],
        stream: false,
      });
      return completion.choices[0]?.message.content ?? '';
    }),
  checkVLMResponseApiSupport: t.procedure
    .input<{
      baseUrl: string;
      apiKey: string;
      modelName: string;
    }>()
    .handle(async ({ input }) => {
      try {
        const openai = new OpenAI({
          apiKey: input.apiKey,
          baseURL: input.baseUrl,
        });
        const result = await openai.responses.create({
          model: input.modelName,
          input: 'return 1+1=?',
          stream: false,
        });
        return Boolean(result?.id || result?.previous_response_id);
      } catch (e) {
        logger.warn('[checkVLMResponseApiSupport] failed:', e);
        return false;
      }
    }),
  checkModelAvailability: t.procedure
    .input<{
      baseUrl: string;
      apiKey: string;
      modelName: string;
    }>()
    .handle(async ({ input }) => {
      const openai = new OpenAI({
        apiKey: input.apiKey,
        baseURL: input.baseUrl,
      });
      const completion = await openai.chat.completions.create({
        model: input.modelName,
        messages: [{ role: 'user', content: 'return 1+1=?' }],
        stream: false,
      });

      return Boolean(completion?.id || completion.choices[0].message.content);
    }),
});
