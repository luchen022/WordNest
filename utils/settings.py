"""
设置管理工具
"""
import json
import os
from flask import current_app


def load_settings():
    """加载系统设置"""
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'marked_only': False}
    else:
        # 默认设置
        settings = {'marked_only': False}
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return settings


def save_settings(settings):
    """保存系统设置"""
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)


def get_ai_config():
    """
    获取当前有效的大模型配置
    优先级：settings.json > 环境变量 / current_app.config > 默认值
    """
    settings = load_settings()
    
    # 1. Base URL
    base_url = (
        settings.get('ai_base_url')
        or os.environ.get('DEEPSEEK_BASE_URL')
        or os.environ.get('AI_BASE_URL')
        or (current_app.config.get('DEEPSEEK_BASE_URL') if current_app else None)
        or 'https://api.deepseek.com'
    )
    base_url = str(base_url).strip().rstrip('/')
    
    # 2. Model
    model = (
        settings.get('ai_model')
        or os.environ.get('DEEPSEEK_MODEL')
        or os.environ.get('AI_MODEL')
        or 'deepseek-chat'
    )
    model = str(model).strip()
    
    # 3. API Key
    api_key = (
        settings.get('ai_api_key')
        or os.environ.get('DEEPSEEK_API_KEY')
        or os.environ.get('AI_API_KEY')
        or (current_app.config.get('DEEPSEEK_API_KEY') if current_app else None)
        or ''
    )
    api_key = str(api_key).strip()
    
    return {
        'base_url': base_url,
        'model': model,
        'api_key': api_key
    }


def mask_api_key(api_key: str) -> str:
    """脱敏 API Key"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "******"
    return api_key[:3] + "******" + api_key[-4:]


def get_masked_ai_config():
    """获取脱敏后的 AI 配置（用于前端展示）"""
    config = get_ai_config()
    raw_key = config.get('api_key', '')
    return {
        'base_url': config.get('base_url', 'https://api.deepseek.com'),
        'model': config.get('model', 'deepseek-chat'),
        'api_key_masked': mask_api_key(raw_key),
        'has_api_key': bool(raw_key)
    }


def save_ai_config(base_url: str, api_key: str, model: str):
    """
    更新并保存 AI 配置
    如果传入的 api_key 包含星号 '*' 或为空且原有 key 存在，则保留原有 key
    """
    settings = load_settings()
    existing_config = get_ai_config()
    existing_key = existing_config.get('api_key', '')
    
    cleaned_url = (base_url or 'https://api.deepseek.com').strip().rstrip('/')
    cleaned_model = (model or 'deepseek-chat').strip()
    cleaned_key = (api_key or '').strip()
    
    # 判断是否保留原有 key
    if ('*' in cleaned_key) or (not cleaned_key and existing_key):
        final_key = existing_key
    else:
        final_key = cleaned_key
        
    settings['ai_base_url'] = cleaned_url
    settings['ai_model'] = cleaned_model
    settings['ai_api_key'] = final_key
    
    save_settings(settings)
    return {
        'base_url': cleaned_url,
        'model': cleaned_model,
        'api_key': final_key
    }


def build_chat_completions_url(base_url: str) -> str:
    """
    根据 base_url 构建标准的 chat/completions 请求地址
    兼容：
    - https://api.deepseek.com -> https://api.deepseek.com/chat/completions (或 /v1)
    - https://api.openai.com/v1 -> https://api.openai.com/v1/chat/completions
    - http://localhost:11434/v1 -> http://localhost:11434/v1/chat/completions
    - 自定义带完整路径的 url -> 直接使用
    """
    url = (base_url or '').strip().rstrip('/')
    if not url:
        url = 'https://api.deepseek.com'
    if url.endswith('/chat/completions'):
        return url
    if url.endswith('/v1'):
        return f"{url}/chat/completions"
    if '11434' in url and not url.endswith('/v1'):
        return f"{url}/v1/chat/completions"
    return f"{url}/chat/completions"

