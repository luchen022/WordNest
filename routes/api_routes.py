"""
API路由
提供RESTful API接口
"""
from flask import Blueprint, jsonify, request, current_app
from services import GraphService


api_bp = Blueprint('api', __name__)


@api_bp.route('/graph_data')
def graph_data():
    """API接口，返回知识图谱的JSON数据供前端异步加载"""
    try:
        # 获取URL参数
        focus_word = request.args.get('word', '')
        relation_type = request.args.get('type', 'all')
        depth = int(request.args.get('depth', 2))
        
        # 验证参数
        if not focus_word:
            return jsonify({'error': '缺少必要的word参数'}), 400
        
        current_app.logger.info(
            f"API请求知识图谱数据: 单词={focus_word}, 关系类型={relation_type}, 深度={depth}"
        )
        
        # 获取图谱数据
        graph_data = GraphService.generate_word_relations_using_deepseek(
            focus_word, relation_type, depth
        )
        
        # 创建节点和边的数据结构
        graph_structure = GraphService.build_graph_data(focus_word, graph_data)
        nodes = graph_structure['nodes']
        edges = graph_structure['edges']
        
        current_app.logger.info(f"API: 生成的图谱数据: 节点数={len(nodes)}, 边数={len(edges)}")
        
        return jsonify({'nodes': nodes, 'edges': edges})
        
    except Exception as e:
        current_app.logger.error(f"API生成知识图谱数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'nodes': [],
            'edges': []
        }), 500


@api_bp.route('/settings/ai', methods=['GET'])
def get_ai_settings():
    """获取当前 AI 大模型配置（API Key 脱敏）"""
    from utils import get_masked_ai_config
    return jsonify({
        'success': True,
        'config': get_masked_ai_config()
    })


@api_bp.route('/settings/ai', methods=['POST'])
def update_ai_settings():
    """更新并保存 AI 大模型配置"""
    from utils import save_ai_config
    try:
        data = request.get_json(silent=True) or {}
        base_url = data.get('base_url', '').strip()
        model = data.get('model', '').strip()
        api_key = data.get('api_key', '').strip()
        
        if not base_url:
            return jsonify({'success': False, 'error': 'Base URL 不能为空'}), 400
        if not model:
            return jsonify({'success': False, 'error': '模型 ID 不能为空'}), 400
            
        saved = save_ai_config(base_url=base_url, api_key=api_key, model=model)
        current_app.logger.info(f"AI 配置已更新: base_url={saved['base_url']}, model={saved['model']}")
        
        return jsonify({
            'success': True,
            'message': 'AI 配置已保存成功！'
        })
    except Exception as e:
        current_app.logger.error(f"保存 AI 配置失败: {str(e)}")
        return jsonify({'success': False, 'error': f'保存失败: {str(e)}'}), 500


@api_bp.route('/settings/ai/test', methods=['POST'])
def test_ai_settings():
    """测试 AI 大模型连接连通性"""
    import requests
    from utils import get_ai_config, build_chat_completions_url
    
    try:
        data = request.get_json(silent=True) or {}
        current_config = get_ai_config()
        
        base_url = data.get('base_url', '').strip() or current_config.get('base_url', '')
        model = data.get('model', '').strip() or current_config.get('model', '')
        api_key_input = data.get('api_key', '').strip()
        
        # 处理 API Key：如果输入为空或包含*号，则使用当前已存的 Key
        if not api_key_input or '*' in api_key_input:
            api_key = current_config.get('api_key', '')
        else:
            api_key = api_key_input
            
        if not base_url:
            return jsonify({'success': False, 'error': 'Base URL 不能为空'}), 400
        if not model:
            return jsonify({'success': False, 'error': '模型 ID 不能为空'}), 400
            
        url = build_chat_completions_url(base_url)
        headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            
        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': 'Hello, reply with only the word "OK" to test the connection.'}
            ],
            'max_tokens': 15,
            'temperature': 0.1
        }
        
        current_app.logger.info(f"正在测试大模型连接: URL={url}, Model={model}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
            proxies={"http": None, "https": None}
        )
        
        if response.status_code == 200:
            result = response.json()
            reply_text = ''
            if 'choices' in result and len(result['choices']) > 0:
                reply_text = result['choices'][0].get('message', {}).get('content', '').strip()
            return jsonify({
                'success': True,
                'message': f'连接成功！模型 "{model}" 响应正常。',
                'reply': reply_text
            })
        elif response.status_code in (401, 403):
            return jsonify({
                'success': False,
                'error': f'认证失败 (HTTP {response.status_code})：请检查 API Key 是否有效。'
            }), 400
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': f'接口未找到 (HTTP 404)：请求地址为 {url}，请检查 Base URL 是否正确。'
            }), 400
        else:
            error_body = response.text[:200]
            return jsonify({
                'success': False,
                'error': f'请求返回 HTTP {response.status_code}: {error_body}'
            }), 400
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': '请求超时 (15秒)：请检查网络是否通畅或 Base URL 是否正确。'
        }), 400
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'success': False,
            'error': f'无法连接到服务器：请检查 Base URL 是否有效且服务已启动 ({str(e)})'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500

