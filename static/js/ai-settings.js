/**
 * WordNest - AI 大模型设置模块
 * 支持前端自定义 Base URL, Model ID, API Key，并提供连通性测试与快速预设
 */

(function () {
    // 注入模态框 HTML
    function initAiSettingsModal() {
        if (document.getElementById('aiSettingsModal')) {
            return;
        }

        const modalHtml = `
        <div id="aiSettingsModal" class="ai-modal-backdrop hidden" role="dialog" aria-modal="true">
            <div class="ai-modal-card">
                <div class="ai-modal-header">
                    <div class="ai-modal-title-wrap">
                        <span class="ai-modal-icon">⚙️</span>
                        <h3>AI 大模型配置</h3>
                    </div>
                    <button type="button" class="ai-modal-close" id="closeAiSettingsModalBtn" title="关闭">&times;</button>
                </div>
                
                <div class="ai-modal-body">
                    <!-- 快捷预设 -->
                    <div class="ai-preset-section">
                        <span class="ai-preset-label">快速填充预设：</span>
                        <div class="ai-preset-chips">
                            <button type="button" class="ai-chip" data-url="https://api.deepseek.com" data-model="deepseek-chat" title="DeepSeek 官方接口">DeepSeek</button>
                            <button type="button" class="ai-chip" data-url="https://api.openai.com/v1" data-model="gpt-4o-mini" title="OpenAI 官方接口">OpenAI</button>
                            <button type="button" class="ai-chip" data-url="http://localhost:11434/v1" data-model="qwen2.5:3b" title="Ollama 本地大模型">Ollama(本地)</button>
                            <button type="button" class="ai-chip" data-url="https://api.siliconflow.cn/v1" data-model="deepseek-ai/DeepSeek-V3" title="硅基流动 SiliconFlow">SiliconFlow</button>
                            <button type="button" class="ai-chip" data-url="https://api.moonshot.cn/v1" data-model="moonshot-v1-8k" title="Kimi 月之暗面">Kimi</button>
                        </div>
                    </div>

                    <!-- 表单输入 -->
                    <div class="ai-form-group">
                        <label for="aiBaseUrlInput">
                            API Base URL <span class="ai-required">*</span>
                        </label>
                        <input type="text" id="aiBaseUrlInput" class="ai-input" placeholder="例如: https://api.deepseek.com" autocomplete="off" />
                        <span class="ai-field-tip">兼容所有 OpenAI 格式接口。本地 Ollama 需包含 /v1（如 http://localhost:11434/v1）</span>
                    </div>

                    <div class="ai-form-group">
                        <label for="aiModelInput">
                            模型 ID (Model ID) <span class="ai-required">*</span>
                        </label>
                        <input type="text" id="aiModelInput" class="ai-input" placeholder="例如: deepseek-chat, gpt-4o-mini, qwen2.5:3b" autocomplete="off" />
                        <span class="ai-field-tip">要调用的模型名称标识</span>
                    </div>

                    <div class="ai-form-group">
                        <label for="aiApiKeyInput">
                            API Key
                        </label>
                        <div class="ai-input-action-wrap">
                            <input type="password" id="aiApiKeyInput" class="ai-input" placeholder="请输入 API Key（本地 Ollama 可留空）" autocomplete="new-password" />
                            <button type="button" id="toggleAiKeyVisibleBtn" class="ai-action-btn" title="显示/隐藏 API Key">
                                👁️
                            </button>
                        </div>
                        <span id="aiKeyStatusHint" class="ai-field-tip ai-key-hint">正在获取当前状态...</span>
                    </div>

                    <!-- 测试与提示结果区域 -->
                    <div id="aiTestResultBox" class="ai-result-box hidden"></div>
                </div>

                <div class="ai-modal-footer">
                    <button type="button" class="ai-btn ai-btn-outline" id="testAiConnectionBtn">
                        🔌 测试连接
                    </button>
                    <div class="ai-modal-footer-right">
                        <button type="button" class="ai-btn ai-btn-cancel" id="cancelAiSettingsBtn">取消</button>
                        <button type="button" class="ai-btn ai-btn-primary" id="saveAiSettingsBtn">💾 保存设置</button>
                    </div>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        bindModalEvents();
    }

    let isOriginalKeyMasked = false;

    function bindModalEvents() {
        const modal = document.getElementById('aiSettingsModal');
        const closeBtn = document.getElementById('closeAiSettingsModalBtn');
        const cancelBtn = document.getElementById('cancelAiSettingsBtn');
        const saveBtn = document.getElementById('saveAiSettingsBtn');
        const testBtn = document.getElementById('testAiConnectionBtn');
        const toggleKeyBtn = document.getElementById('toggleAiKeyVisibleBtn');
        const apiKeyInput = document.getElementById('aiApiKeyInput');
        const baseUrlInput = document.getElementById('aiBaseUrlInput');
        const modelInput = document.getElementById('aiModelInput');
        const presetChips = document.querySelectorAll('.ai-chip');

        // 关闭事件
        function closeModal() {
            modal.classList.add('hidden');
            hideResultBox();
        }

        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeModal();
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });

        // 切换 Key 可见性
        toggleKeyBtn.addEventListener('click', function () {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
            } else {
                apiKeyInput.type = 'password';
            }
        });

        // 预设点击
        presetChips.forEach(chip => {
            chip.addEventListener('click', function () {
                const url = this.getAttribute('data-url');
                const model = this.getAttribute('data-model');
                if (url) baseUrlInput.value = url;
                if (model) modelInput.value = model;

                // 视觉高亮
                presetChips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // 用户输入 Key 时更新状态
        apiKeyInput.addEventListener('input', function () {
            isOriginalKeyMasked = false;
            const hint = document.getElementById('aiKeyStatusHint');
            if (hint) {
                hint.textContent = '✏️ 已输入新 Key（保存后生效）';
                hint.className = 'ai-field-tip ai-key-hint text-warning';
            }
        });

        // 测试连接
        testBtn.addEventListener('click', async function () {
            const baseUrl = baseUrlInput.value.trim();
            const model = modelInput.value.trim();
            const apiKey = apiKeyInput.value.trim();

            if (!baseUrl) {
                showResultBox('error', '请输入 API Base URL');
                return;
            }
            if (!model) {
                showResultBox('error', '请输入模型 ID');
                return;
            }

            testBtn.disabled = true;
            testBtn.innerHTML = '<span class="ai-spinner"></span> 正在测试...';
            hideResultBox();

            try {
                const res = await fetch('/api/settings/ai/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        base_url: baseUrl,
                        model: model,
                        api_key: apiKey
                    })
                });
                const data = await res.json();

                if (data.success) {
                    showResultBox('success', `✅ ${data.message}` + (data.reply ? ` (响应: "${data.reply}")` : ''));
                } else {
                    showResultBox('error', `❌ ${data.error || '连接失败'}`);
                }
            } catch (err) {
                showResultBox('error', `❌ 网络请求出错: ${err.message}`);
            } finally {
                testBtn.disabled = false;
                testBtn.innerHTML = '🔌 测试连接';
            }
        });

        // 保存配置
        saveBtn.addEventListener('click', async function () {
            const baseUrl = baseUrlInput.value.trim();
            const model = modelInput.value.trim();
            const apiKey = apiKeyInput.value.trim();

            if (!baseUrl) {
                showResultBox('error', 'API Base URL 不能为空');
                return;
            }
            if (!model) {
                showResultBox('error', '模型 ID 不能为空');
                return;
            }

            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="ai-spinner"></span> 正在保存...';

            try {
                const res = await fetch('/api/settings/ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        base_url: baseUrl,
                        model: model,
                        api_key: apiKey
                    })
                });
                const data = await res.json();

                if (data.success) {
                    showResultBox('success', '🎉 ' + (data.message || '配置已保存成功！'));
                    setTimeout(() => {
                        closeModal();
                    }, 1200);
                } else {
                    showResultBox('error', '❌ ' + (data.error || '保存失败'));
                }
            } catch (err) {
                showResultBox('error', `❌ 保存请求失败: ${err.message}`);
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '💾 保存设置';
            }
        });
    }

    function showResultBox(type, message) {
        const box = document.getElementById('aiTestResultBox');
        if (!box) return;
        box.className = `ai-result-box ${type === 'success' ? 'ai-result-success' : 'ai-result-error'}`;
        box.textContent = message;
        box.classList.remove('hidden');
    }

    function hideResultBox() {
        const box = document.getElementById('aiTestResultBox');
        if (box) {
            box.className = 'ai-result-box hidden';
            box.textContent = '';
        }
    }

    async function loadCurrentAiSettings() {
        const baseUrlInput = document.getElementById('aiBaseUrlInput');
        const modelInput = document.getElementById('aiModelInput');
        const apiKeyInput = document.getElementById('aiApiKeyInput');
        const hint = document.getElementById('aiKeyStatusHint');

        try {
            const res = await fetch('/api/settings/ai');
            const data = await res.json();

            if (data.success && data.config) {
                const cfg = data.config;
                if (baseUrlInput) baseUrlInput.value = cfg.base_url || 'https://api.deepseek.com';
                if (modelInput) modelInput.value = cfg.model || 'deepseek-chat';

                if (cfg.has_api_key) {
                    isOriginalKeyMasked = true;
                    if (apiKeyInput) {
                        apiKeyInput.value = cfg.api_key_masked || 'sk-******';
                    }
                    if (hint) {
                        hint.textContent = `✅ 当前已配置 Key (${cfg.api_key_masked})，如不修改可直接保留`;
                        hint.className = 'ai-field-tip ai-key-hint text-success';
                    }
                } else {
                    isOriginalKeyMasked = false;
                    if (apiKeyInput) apiKeyInput.value = '';
                    if (hint) {
                        hint.textContent = '⚠️ 尚未配置 API Key（如使用本地 Ollama 等无认证服务可留空）';
                        hint.className = 'ai-field-tip ai-key-hint text-muted';
                    }
                }
            }
        } catch (e) {
            console.error('加载当前 AI 配置失败:', e);
            if (hint) {
                hint.textContent = '无法获取当前配置，请手动输入';
                hint.className = 'ai-field-tip ai-key-hint text-error';
            }
        }
    }

    // 全局打开函数
    window.openAiSettingsModal = function () {
        initAiSettingsModal();
        const modal = document.getElementById('aiSettingsModal');
        if (modal) {
            modal.classList.remove('hidden');
            hideResultBox();
            loadCurrentAiSettings();
        }
    };

    // DOM 加载完成后自动绑定页面上的触发按钮
    document.addEventListener('DOMContentLoaded', function () {
        initAiSettingsModal();

        // 委托监听任意带有 class .ai-settings-btn 或 id #aiSettingsBtn 的元素
        document.body.addEventListener('click', function (e) {
            const btn = e.target.closest('.ai-settings-btn, #aiSettingsBtn, [data-open-ai-settings]');
            if (btn) {
                e.preventDefault();
                window.openAiSettingsModal();
            }
        });
    });
})();
