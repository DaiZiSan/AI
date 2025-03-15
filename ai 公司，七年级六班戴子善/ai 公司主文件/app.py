# app.py - 多智能体工作流系统前端应用
from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
import os
import sys
import json
import logging
import subprocess
import glob
import shutil
import threading
import time
import uuid  # 添加uuid模块
from datetime import datetime  # 添加datetime模块
from concurrent.futures import ThreadPoolExecutor  # 添加ThreadPoolExecutor导入
import ai_workflow_system

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AI-Workflow-Frontend")

# 确保静态文件路径正确
app = Flask(__name__, 
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = os.urandom(24)  # 用于会话管理

# 添加一个路由来确保静态文件可以被访问
@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

# 全局变量存储当前工作流
workflow_manager = None
# 存储流式输出的响应内容
# 添加在全局变量部分
streaming_responses = {}

# 添加流式响应生成函数
# 创建一个线程池来管理线程资源
thread_pool = ThreadPoolExecutor(max_workers=3)  # 限制最大线程数为10

# 添加线程池关闭函数
# 修改线程池配置
thread_pool = ThreadPoolExecutor(max_workers=3)  # 减少最大线程数

# 修改线程池的初始化方式
thread_pool = None

def get_thread_pool():
    """获取线程池实例"""
    global thread_pool
    if thread_pool is None or thread_pool._shutdown:
        thread_pool = ThreadPoolExecutor(max_workers=3)
    return thread_pool

# 删除全局线程池变量
# thread_pool = None  # 删除这行

# 使用线程池管理类替代全局变量
class ThreadPoolManager:
    """线程池管理器"""
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self._pool = None
    
    def get_pool(self):
        """获取线程池实例"""
        if self._pool is None or self._pool._shutdown:
            self._pool = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._pool
    
    def shutdown(self):
        """关闭线程池"""
        if self._pool and not self._pool._shutdown:
            self._pool.shutdown(wait=False)
            self._pool = None

# 创建线程池管理器实例
thread_pool_manager = ThreadPoolManager(max_workers=3)

# 修改 cleanup_resources 函数
def cleanup_resources():
    """清理资源"""
    thread_pool_manager.shutdown()

# 修改使用线程池的地方，例如在 initialize_workflow 中：
@app.route('/initialize', methods=['POST'])
@app.route('/initialize_workflow', methods=['GET', 'POST'])
def initialize_workflow():
    """初始化工作流"""
    global workflow_manager
    
    try:
        # 处理POST请求
        if request.method == 'POST':
            data = request.json or {}
            auto_start = data.get('auto_start', False)
            user_request = data.get('user_request', '默认初始化请求')
        else:
            # 处理GET请求
            auto_start = request.args.get('auto_start', 'false').lower() == 'true'
            user_request = request.args.get('user_request', '默认初始化请求')
        
        # 创建工作流管理器，提供用户请求参数
        workflow_manager = ai_workflow_system.WorkflowManager(user_request)
        
        # 如果设置了自动启动，则生成初始响应
        if auto_start:
            response_id = str(uuid.uuid4())
            
            # 使用线程池管理器获取线程池实例
            thread_pool_manager.get_pool().submit(
                generate_streaming_response,
                response_id, 
                "analyst", 
                "欢迎使用多智能体工作流系统！我是分析官，请告诉我您的需求。"
            )
            
            return jsonify({
                'status': 'success',
                'message': '工作流已初始化',
                'current_agent': 'analyst',
                'response_id': response_id
            })
        
        return jsonify({
            'status': 'success',
            'message': '工作流已初始化'
        })
    except Exception as e:
        logger.error(f"初始化工作流失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'初始化失败: {str(e)}'})

# 修改generate_agent_response函数，优化资源使用
def generate_agent_response(agent_id, user_input, response_id):
    """生成智能体响应（后台线程）"""
    global workflow_manager, streaming_responses
    
    try:
        # 更新用户输入
        workflow_manager.user_input = user_input
        
        # 准备输入（包含本地文件上下文）
        prepared_input = workflow_manager.prepare_user_input()
        
        # 初始化响应数据
        streaming_responses[response_id] = {
            "complete": False, 
            "text": "",
            "chunks": []
        }
        
        # 生成响应
        full_response = workflow_manager.agents[agent_id].generate_response(prepared_input)
        
        # 流式输出 - 减少更新频率
        total_length = len(full_response)
        chunk_size = max(50, total_length // 20)  # 增大块大小，减少更新次数
        
        for i in range(0, total_length, chunk_size):
            end_idx = min(i + chunk_size, total_length)
            chunk = full_response[i:end_idx]
            
            # 更新当前文本
            streaming_responses[response_id]["text"] += chunk
            streaming_responses[response_id]["chunks"].append(chunk)
            
            # 实时保存为MD文件
            if agent_id in ['ceo', 'writer', 'programmer', 'reviewer']:
                save_response_to_md(agent_id, streaming_responses[response_id]["text"])
                
            time.sleep(0.2)  # 增加延迟，减少更新频率
        
        # 处理响应
        workflow_manager.process_response(full_response)
        
        # 标记完成
        streaming_responses[response_id]["complete"] = True
        streaming_responses[response_id]["next_agent"] = workflow_manager.current_agent
        streaming_responses[response_id]["next_agent_name"] = workflow_manager.agents[workflow_manager.current_agent].name
        
        # 获取待办事项列表
        todo_items = [
            {
                'id': idx + 1,
                'agent': task.agent,
                'description': task.description,
                'status': task.status
            }
            for idx, task in enumerate(workflow_manager.todo_list.tasks)
        ]
        streaming_responses[response_id]["todo_items"] = todo_items
        
        # 30秒后清理响应数据
        time.sleep(30)
        if response_id in streaming_responses:
            del streaming_responses[response_id]
            
    except Exception as e:
        logger.error(f"生成智能体响应失败: {e}", exc_info=True)
        if response_id in streaming_responses:
            streaming_responses[response_id]["error"] = str(e)
            streaming_responses[response_id]["complete"] = True

# 修改stream_agent_response函数，使用线程池
@app.route('/stream_agent_response', methods=['POST'])
def stream_agent_response():
    """流式获取智能体响应"""
    global workflow_manager
    
    if not workflow_manager:
        return jsonify({'status': 'error', 'message': '请先初始化工作流'})
    
    data = request.json
    user_input = data.get('user_input', '')
    
    if not user_input and not workflow_manager.user_input:
        return jsonify({'status': 'error', 'message': '请输入内容'})
    
    try:
        # 获取当前智能体
        current_agent = workflow_manager.current_agent
        agent_name = workflow_manager.agents[current_agent].name
        
        # 创建响应ID
        response_id = f"{current_agent}_{int(time.time())}"
        
        # 使用线程池启动后台任务生成响应
        # ... 其他代码保持不变 ...
        
        # 使用线程池管理器获取线程池实例
        thread_pool_manager.get_pool().submit(
            generate_agent_response,
            current_agent, 
            user_input, 
            response_id
        )
        
        return jsonify({
            'status': 'success',
            'message': '开始生成响应',
            'response_id': response_id,
            'agent': current_agent,
            'agent_name': agent_name
        })
    except Exception as e:
        logger.error(f"启动流式响应失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'启动流式响应失败: {str(e)}'})

# 添加资源清理路由
@app.route('/cleanup', methods=['POST'])
def cleanup():
    """清理资源"""
    try:
        cleanup_resources()
        return jsonify({'status': 'success', 'message': '资源已清理'})
    except Exception as e:
        logger.error(f"清理资源失败: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'清理资源失败: {str(e)}'})

# 在应用程序关闭时关闭线程池
@app.teardown_appcontext
def shutdown_thread_pool(exception=None):
    """关闭线程池"""
    global thread_pool
    if thread_pool:
        thread_pool.shutdown(wait=True)

# 修改stream_response函数，优化性能
@app.route('/stream_response/<response_id>', methods=['GET'])
def stream_response(response_id):
    """流式返回智能体响应"""
    if response_id not in streaming_responses:
        return jsonify({'error': '无效的响应ID'}), 404
        
    def generate():
        last_text_length = 0
        retry_count = 0
        max_retries = 30  # 减少最大重试次数
        
        while retry_count < max_retries:
            try:
                response_data = streaming_responses.get(response_id, {})
                current_text = response_data.get('text', '')
                
                if len(current_text) > last_text_length:
                    new_text = current_text[last_text_length:]
                    last_text_length = len(current_text)
                    yield f"data: {json.dumps({'text': new_text})}\n\n"
                
                if response_data.get('complete', False):
                    complete_data = {
                        'complete': True,
                        'next_agent': response_data.get('next_agent'),
                        'next_agent_name': response_data.get('next_agent_name'),
                        'todo_items': response_data.get('todo_items', [])
                    }
                    yield f"data: {json.dumps(complete_data)}\n\n"
                    break
                    
                time.sleep(0.5)  # 增加轮询间隔
                retry_count += 1
            except Exception as e:
                logger.error(f"流式响应生成失败: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
# 添加保存响应到MD文件的功能
def save_response_to_md(agent_id, content):
    """保存响应到MD文件"""
    filename = f"{agent_id}_response.md"
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(content)
# 主应用路由

@app.route('/', methods=['GET', 'POST'])
def index():
    """主页路由"""
    return render_template('index.html')

if __name__ == '__main__': 
    # 调试模式开关（True=开启，False=关闭）
    app.run(debug=True, host='0.0.0.0', port=5001)  # 当前已生效的端口配置

# 在应用程序关闭时关闭线程池
@app.teardown_appcontext
def shutdown_thread_pool(exception=None):
    """关闭线程池"""
    # 不在每次请求后关闭线程池
    pass

# 添加正确的应用程序退出处理
import atexit

# 修改应用程序退出处理
@atexit.register
def shutdown_resources():
    """在应用程序退出时关闭资源"""
    logger.info("正在关闭线程池...")
    thread_pool_manager.shutdown()
    logger.info("线程池已关闭")

# 删除文件末尾的这些重复定义
# 在ThreadPoolManager类定义之前添加get_agent_name函数
def get_agent_name(agent_id):
    """获取智能体名称"""
    agent_names = {
        'analyst': '分析官',
        'ceo': '首席执行官',
        'writer': '小说家',
        'programmer': '程序员',
        'reviewer': '审核员',
        'web_searcher': '网络搜索员',
        'file_organizer': '文件整理员'
    }
    return agent_names.get(agent_id, '未知智能体')

# 添加generate_streaming_response函数
def generate_streaming_response(response_id, agent_id, content):
    """生成流式响应"""
    try:
        streaming_responses[response_id] = {
            'chunks': [],
            'complete': False,
            'next_agent': agent_id,
            'next_agent_name': get_agent_name(agent_id),
            'todo_items': [],
            'text': ''
        }
        
        words = content.split()
        for i in range(0, len(words), 3):
            chunk = ' '.join(words[i:i+3])
            if chunk:
                streaming_responses[response_id]['chunks'].append(chunk + ' ')
                streaming_responses[response_id]['text'] += chunk + ' '
                time.sleep(0.1)  # 增加延迟时间
        
        streaming_responses[response_id]['complete'] = True
        
        # 减少等待时间
        time.sleep(5)
        if response_id in streaming_responses:
            del streaming_responses[response_id]
    except Exception as e:
        logger.error(f"生成流式响应失败: {e}", exc_info=True)
        if response_id in streaming_responses:
            streaming_responses[response_id]['error'] = str(e)
            streaming_responses[response_id]['complete'] = True