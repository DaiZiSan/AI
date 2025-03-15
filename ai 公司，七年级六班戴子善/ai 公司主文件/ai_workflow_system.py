# File: ai_workflow_system.py
# 多智能体工作流系统后端实现
# 整合了项目工具和智能体工作流功能

import json
import requests
import os
import sys
import re
import webbrowser
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AI-Workflow-System")

# API 配置
DEEPSEEK_API_KEY = "sk-hzsahrutepvtipkgejivnxfeyevchbpnvzsaoxuxuehetiaf"
if not DEEPSEEK_API_KEY:
    raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# ============ 项目工具函数 ============

class ProjectUtils:
    """项目工具类，提供项目创建和搜索相关功能"""
    
    @staticmethod
    def generate_ai_project_name(user_request: str) -> str:
        """
        使用 DeepSeek API 智能生成项目名称。

        Args:
            user_request (str): 用户的初始创作需求，作为生成项目名称的上下文。

        Returns:
            str: AI 生成的项目名称。如果生成失败，则返回 "default_project_name"。
        """
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        system_prompt = """您是一个专业的命名专家，擅长根据用户提供的项目描述，创作富有创意、привлекательным 和容易记住的项目名称。请根据用户的创作需求，生成一个不超过 15 个字的项目名称。名称应该简洁明了，能够准确概括项目的主题或内容，并且有一定的吸引力。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户创作需求: {user_request}\n\n请生成项目名称:"}
        ]

        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",
            "messages": messages,
            "max_tokens": 50,
            "temperature": 0.8
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            json_response = response.json()
            if 'choices' in json_response and json_response['choices']:
                project_name = json_response['choices'][0]['message']['content'].strip()
                project_name = project_name.strip()[:30]

                if project_name:
                    return project_name
                else:
                    logger.warning(f"AI 生成项目名称为空，将使用默认名称 'default_project_name'。用户需求：{user_request}")
                    return "default_project_name"
            else:
                logger.warning(f"API 返回内容格式错误，无法解析项目名称，将使用默认名称 'default_project_name'。API 响应内容：{json_response}")
                return "default_project_name"

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败，无法生成项目名称，错误信息: {e}，将使用默认名称 'default_project_name'。用户需求：{user_request}")
            return "default_project_name"
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误，无法解析项目名称，错误信息: {e}，将使用默认名称 'default_project_name'。API 响应内容：{response.text}")
            return "default_project_name"

    @staticmethod
    def create_project_folder(user_request: str, base_path=None) -> str:
        """
        在用户电脑上创建项目文件夹，并使用 AI 智能生成项目名称。
        
        Args:
            user_request (str): 用户的创作需求
            base_path (str, optional): 项目基础路径。默认为用户主目录。
            
        Returns:
            str: 创建的项目文件夹路径，失败则返回None
        """
        if base_path is None:
            base_path = os.path.expanduser("~")

        ai_project_name = ProjectUtils.generate_ai_project_name(user_request)
        project_folder_name = f"ai_project_{ai_project_name.replace(' ', '_')}"
        project_path = os.path.join(base_path, project_folder_name)

        try:
            os.makedirs(project_path, exist_ok=True)
            logger.info(f"项目文件夹创建成功: {project_path}")
            return project_path
        except OSError as e:
            logger.error(f"无法创建项目文件夹，错误信息: {e}，路径：{project_path}")
            return None

    @staticmethod
    def suggest_search_queries(keywords: List[str]) -> List[str]:
        """
        使用 DeepSeek API 智能生成更丰富的搜索查询建议。
        
        Args:
            keywords (List[str]): 关键词列表
            
        Returns:
            List[str]: 搜索查询建议列表
        """
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        system_prompt = """您是一个专业的搜索查询专家，擅长根据关键词列表，生成更丰富、更有效的搜索查询建议。请针对以下关键词，生成 3-5 条不同的搜索查询，以便用户更有效地在互联网上找到相关信息。查询建议应该具体、实用，并覆盖关键词的不同方面。"""

        query_prompt = "关键词列表: " + ", ".join(keywords) + "\n\n请生成搜索查询建议 (每行一条):"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query_prompt}
        ]

        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }

        search_queries = []
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            json_response = response.json()
            if 'choices' in json_response and json_response['choices']:
                suggestions_text = json_response['choices'][0]['message']['content'].strip()
                search_queries = [line.strip() for line in suggestions_text.splitlines() if line.strip()]
                if not search_queries:
                    logger.warning(f"AI 生成搜索查询为空，将使用默认示例查询。关键词: {keywords}")
                    return [f"在浏览器中搜索： {keyword}" for keyword in keywords]
                return search_queries
            else:
                logger.warning(f"API 返回内容格式错误，无法解析搜索查询建议，将使用默认示例查询。API 响应内容: {json_response}")
                return [f"在浏览器中搜索： {keyword}" for keyword in keywords]

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败，无法生成搜索查询建议，错误信息: {e}，将使用默认示例查询。关键词: {keywords}")
            return [f"在浏览器中搜索： {keyword}" for keyword in keywords]
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误，无法解析搜索查询建议，错误信息: {e}，将使用默认示例查询。API 响应内容: {response.text}")
            return [f"在浏览器中搜索： {keyword}" for keyword in keywords]

    @staticmethod
    def suggest_urls_for_queries(search_queries: List[str]) -> List[str]:
        """
        根据搜索查询生成建议的 URL (当前版本仅为示例 URL)。
        
        Args:
            search_queries (List[str]): 搜索查询列表
            
        Returns:
            List[str]: 建议的URL列表
        """
        suggested_urls = []
        for query in search_queries:
            suggested_urls.append(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return suggested_urls

    @staticmethod
    def open_url_in_browser(url: str) -> None:
        """
        在用户默认浏览器中打开 URL。
        
        Args:
            url (str): 要打开的URL
        """
        try:
            webbrowser.open(url)
            logger.info(f"已在浏览器中打开URL: {url}")
        except Exception as e:
            logger.error(f"无法在浏览器中打开URL: {url}, 错误信息: {e}")
            print(f"\n[浏览器提示] 建议您在浏览器中手动打开以下URL以获取更多信息:\n{url}")


# ============ 智能体系统 ============

class Agent:
    """
    Agent 类，代表一个具有特定角色和系统提示的智能体。
    """
    def __init__(self, name: str, system_prompt: str):
        """
        初始化 Agent 对象。

        Args:
            name (str): Agent 的名称。
            system_prompt (str): Agent 的系统提示，用于指导其行为。
        """
        self.name = name
        self.system_prompt = system_prompt
        self.conversation_history = []

    def generate_response(self, user_input: str) -> str:
        """
        调用 DeepSeek API 生成回复。

        Args:
            user_input (str): 用户输入的内容。

        Returns:
            str: Agent 生成的完整回复文本，或错误标识。
        """
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        payload = {
            "model": "Pro/deepseek-ai/DeepSeek-V3",
            "messages": messages,
            "stream": True,
            "temperature": 0.7
        }

        full_response = ""
        try:
            response = requests.post(API_URL, headers=headers, json=payload, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data:'):
                            json_str = decoded_line[5:].strip()
                            if json_str == "[DONE]":
                                continue
                            try:
                                json_data = json.loads(json_str)
                                if 'choices' in json_data and json_data['choices']:
                                    content = json_data['choices'][0]['delta'].get('content', '')
                                    print(content, end='', flush=True)
                                    full_response += content

                                    if self.name == "首席执行官":
                                        mentions = AgentUtils.parse_mentions_realtime(content)
                                        if mentions:
                                            AgentUtils.display_popup(mentions)

                            except json.JSONDecodeError as e:
                                logger.error(f"解析 JSON 失败: {e}")
                                continue
                    except Exception as e:
                        logger.error(f"处理数据流时发生错误: {e}")
                        continue
            print("\n")

            # 保存对话历史
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            return "[API_ERROR]"

        return full_response


class Task:
    """
    任务类，表示待办事项列表中的一个任务项。
    """
    def __init__(self, agent: str, description: str, status: str = "待处理"):
        """
        初始化任务对象
        
        Args:
            agent (str): 负责任务的智能体名称
            description (str): 任务描述
            status (str, optional): 任务状态。默认为"待处理"
        """
        self.agent = agent
        self.description = description
        self.status = status
        self.created_at = AgentUtils.get_current_timestamp()
        self.completed_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典格式"""
        return {
            "agent": self.agent,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }
        
    def complete(self) -> None:
        """将任务标记为已完成"""
        self.status = "已完成"
        self.completed_at = AgentUtils.get_current_timestamp()
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务对象"""
        task = cls(
            agent=data["agent"],
            description=data["description"],
            status=data.get("status", "待处理")
        )
        task.created_at = data.get("created_at", AgentUtils.get_current_timestamp())
        task.completed_at = data.get("completed_at")
        return task


class TodoList:
    """
    待办事项列表类，管理工作流中的任务。
    """
    def __init__(self):
        """初始化待办事项列表"""
        self.tasks = []  # 修复这里的缩进错误
        self.task_history = []
        
    def add_task(self, agent: str, description: str) -> None:
        """
        添加新任务到待办事项列表
        
        Args:
            agent (str): 负责任务的智能体名称
            description (str): 任务描述
        """
        self.tasks.append(Task(agent, description))
        logger.info(f"已添加新任务给 {agent}: {description}")
        
    def complete_task(self, index: int) -> bool:
        """
        将指定索引的任务标记为已完成
        
        Args:
            index (int): 任务索引
            
        Returns:
            bool: 操作是否成功
        """
        if 0 <= index < len(self.tasks):
            self.tasks[index].complete()
            logger.info(f"已将任务 #{index+1} 标记为完成: {self.tasks[index].description}")
            return True
        logger.warning(f"无法完成任务: 索引 {index} 超出范围")
        return False
        
    def remove_completed_tasks(self) -> List[Task]:
        """
        移除所有已完成的任务，并返回它们
        
        Returns:
            List[Task]: 已完成的任务列表
        """
        completed = [task for task in self.tasks if task.status == "已完成"]
        self.task_history.extend(completed)
        self.tasks = [task for task in self.tasks if task.status != "已完成"]
        logger.info(f"已移除 {len(completed)} 个已完成的任务")
        return completed
        
    def find_task_for_agent(self, agent: str) -> Optional[int]:
        """
        查找指定智能体的待处理任务
        
        Args:
            agent (str): 智能体名称
            
        Returns:
            Optional[int]: 任务索引，如果没有找到则返回None
        """
        for i, task in enumerate(self.tasks):
            if task.agent == agent and task.status == "待处理":
                return i
        return None
        
    def display(self) -> None:
        """打印待办事项列表"""
        if not self.tasks:
            print("\n---- To-Do List (空) ----\n")
            return

        print("\n---- To-Do List ----")
        print("| 任务 # | 指派给 | 任务描述                     | 状态     |")
        print("|------|--------|--------------------------|----------|")
        for index, task in enumerate(self.tasks):
            print(f"| {index+1:<6} | {task.agent:<6} | {task.description:<24} | {task.status:<8} |")
        print("--------------------\n")
    
    def to_dict(self) -> Dict[str, Any]:
        """将待办事项列表转换为字典格式"""
        return {
            "active_tasks": [task.to_dict() for task in self.tasks],
            "task_history": [task.to_dict() for task in self.task_history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoList':
        """从字典创建待办事项列表对象"""
        todo_list = cls()
        todo_list.tasks = [Task.from_dict(task_data) for task_data in data.get("active_tasks", [])]
        todo_list.task_history = [Task.from_dict(task_data) for task_data in data.get("task_history", [])]
        return todo_list


class AgentUtils:
    """智能体工具类，提供智能体相关的工具函数"""
    
    @staticmethod
    def parse_mentions_realtime(text: str) -> List[str]:
        """
        实时检测文本中的智能体提及 (不区分大小写)。
        
        Args:
            text (str): 要检测的文本
            
        Returns:
            List[str]: 提及的智能体列表
        """
        mentions = []
        agents_to_check = ["writer", "programmer", "reviewer", "analyst", "ceo"]
        
        for agent in agents_to_check:
            if f"@{agent}" in text.lower():
                mentions.append(agent)
                
        return mentions

    @staticmethod
    def display_popup(mentions: List[str]) -> None:
        """
        模拟弹窗显示提及的智能体。
        
        Args:
            mentions (List[str]): 提及的智能体列表
        """
        popup_message = "---- [智能体提及] ----\n"
        for agent_name in mentions:
            popup_message += f"  @ {agent_name.upper()}  \n"
        popup_message += "----------------------"
        print("\n" + popup_message + "\n")

    @staticmethod
    def parse_mentions(response: str) -> List[Union[str, None]]:
        """
        解析整个回复文本，提取智能体提及 (用于工作流跳转)。
        
        Args:
            response (str): 回复文本
            
        Returns:
            List[Union[str, None]]: 提及的智能体列表，如果没有提及则包含None
        """
        mentions = []
        agents_to_check = ["ceo", "analyst", "writer", "programmer", "reviewer"]
        
        for agent in agents_to_check:
            if f"@{agent}" in response.lower():
                mentions.append(agent)

        if "ceo" in mentions:
            mentions.remove("ceo")

        return mentions if mentions else [None]

    @staticmethod
    def parse_task_number_from_ceo_response(response: str) -> Optional[int]:
        """
        从CEO回复中解析任务编号。
        
        Args:
            response (str): CEO的回复文本
            
        Returns:
            Optional[int]: 任务编号，如果没有找到则返回None
        """
        try:
            match = re.search(r'\[TASK_DONE\]\s+任务\s+#(\d+)', response, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return None
        except Exception as e:
            logger.error(f"解析任务编号时出错: {e}")
            return None
    
    @staticmethod
    def get_current_timestamp() -> int:
        """
        获取当前时间戳
        
        Returns:
            int: 当前时间戳（秒）
        """
        import time
        return int(time.time())
    
    @staticmethod
    def read_file_content(file_path: str) -> str:
        """
        读取本地文件内容 (目前只支持文本文件)。
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 文件内容，如果读取失败则返回空字符串
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
        except Exception as e:
            logger.error(f"无法读取文件: {file_path}, 错误信息: {e}")
            return ""
    
    @staticmethod
    def write_file_content(file_path: str, content: str) -> bool:
        """
        写入内容到本地文件
        
        Args:
            file_path (str): 文件路径
            content (str): 要写入的内容
            
        Returns:
            bool: 操作是否成功
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logger.info(f"已成功写入文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"无法写入文件: {file_path}, 错误信息: {e}")
            return False


class SystemAccessManager:
    """系统访问管理器，提供对系统资源的访问能力"""
    
    def __init__(self):
        self.admin_mode = False
        self.browser_history = []
        self.accessed_files = []
        self.executed_commands = []
        
    def request_admin_privileges(self) -> bool:
        """请求管理员权限"""
        try:
            import subprocess
            command = "osascript -e 'do shell script \"echo 权限已获取\" with administrator privileges'"
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                self.admin_mode = True
                return True
            return False
        except Exception as e:
            logger.error(f"请求管理员权限失败: {e}")
            return False
            
    def execute_system_command(self, command: str) -> Dict[str, Any]:
        """执行系统命令"""
        try:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            result = {
                'stdout': process.stdout,
                'stderr': process.stderr,
                'returncode': process.returncode
            }
            self.executed_commands.append({
                'command': command,
                'result': result,
                'timestamp': AgentUtils.get_current_timestamp()
            })
            return result
        except Exception as e:
            logger.error(f"执行系统命令失败: {e}")
            return {'error': str(e)}
            
    def browse_files(self, path: str = '/') -> List[Dict[str, Any]]:
        """浏览文件系统"""
        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                stat = os.stat(full_path)
                items.append({
                    'name': item,
                    'path': full_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'type': 'directory' if os.path.isdir(full_path) else 'file'
                })
            return items
        except Exception as e:
            logger.error(f"浏览文件系统失败: {e}")
            return []
            
    def search_files(self, pattern: str, path: str = '/') -> List[str]:
        """搜索文件"""
        try:
            result = []
            for root, dirs, files in os.walk(path):
                for name in files:
                    if pattern in name:
                        full_path = os.path.join(root, name)
                        result.append(full_path)
                        self.accessed_files.append({
                            'path': full_path,
                            'operation': 'search',
                            'timestamp': AgentUtils.get_current_timestamp()
                        })
            return result
        except Exception as e:
            logger.error(f"搜索文件失败: {e}")
            return []
            
    def read_file(self, path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.accessed_files.append({
                    'path': path,
                    'operation': 'read',
                    'timestamp': AgentUtils.get_current_timestamp()
                })
                return content
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None
            
    def write_file(self, path: str, content: str) -> bool:
        """写入文件内容"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.accessed_files.append({
                'path': path,
                'operation': 'write',
                'timestamp': AgentUtils.get_current_timestamp()
            })
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return False
            
    def open_browser(self, url: str) -> bool:
        """打开浏览器访问URL"""
        try:
            import webbrowser
            success = webbrowser.open(url)
            if success:
                self.browser_history.append({
                    'url': url,
                    'timestamp': AgentUtils.get_current_timestamp()
                })
            return success
        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")
            return False

# 修改 WorkflowManager 类，添加系统访问管理器
class WorkflowManager:
    def __init__(self, initial_request: str):
        """
        初始化工作流管理器
        
        Args:
            initial_request (str): 用户的初始请求
        """
        self.initial_request = initial_request
        self.agents = self._create_agents()
        self.todo_list = TodoList()
        self.current_agent = "analyst"
        self.history = []
        self.user_input = initial_request
        self.workflow_active = True
        self.project_folder_path = None
        self.local_file_paths = []
        # 添加系统访问管理器
        self.system_access = SystemAccessManager()  # 添加系统访问管理器
        
    def initialize_project(self) -> None:
        """初始化项目文件夹并设置本地文件路径"""
        self.project_folder_path = ProjectUtils.create_project_folder(user_request=self.initial_request)
        if self.project_folder_path:
            logger.info(f"已创建项目文件夹：{self.project_folder_path}")
            print(f"\n[项目初始化] 已创建项目文件夹：{self.project_folder_path}")
        else:
            logger.warning("项目文件夹创建失败，本地文件功能可能受限")
            print("\n[项目初始化] 项目文件夹创建失败，本地文件功能可能受限。")
            
        local_file_path = input("\n请输入 CEO 可以访问的本地文件路径 (可以是文件或文件夹，多个路径请用逗号分隔，留空则不使用本地文件): ").strip()
        self.local_file_paths = [path.strip() for path in local_file_path.split(',') if path.strip()]
        
        if self.local_file_paths:
            print("\n[提示] CEO 将会尝试访问以下本地文件/文件夹：")
            for path in self.local_file_paths:
                print(f"- {path}")
            print("\n请确保这些路径是您授权允许访问的，并且只包含您希望 CEO 了解的信息。\n")
    
    def get_local_file_context(self) -> str:
        """
        读取本地文件内容并格式化为上下文字符串
        
        Returns:
            str: 格式化的本地文件内容
        """
        if not self.local_file_paths:
            return ""
            
        local_file_context = ""
        for path in self.local_file_paths:
            if os.path.isfile(path):
                file_content = AgentUtils.read_file_content(path)
                if file_content:
                    local_file_context += f"\n[文件内容] {path}:\n{file_content}\n--- 文件 {path} 内容结束 ---\n"
            elif os.path.isdir(path):
                logger.info(f"暂不支持直接读取文件夹: {path}")
                print(f"\n[提示] 暂不支持直接读取文件夹: {path}，请指定文件夹内的具体文件。")
            else:
                logger.warning(f"指定路径无效: {path}")
                print(f"\n[警告] 指定路径无效: {path}")
                
        return local_file_context
    
    def prepare_user_input(self) -> str:
        """
        准备发送给当前智能体的输入，包含本地文件上下文
        
        Returns:
            str: 准备好的用户输入
        """
        if self.current_agent == "ceo":
            local_file_context = self.get_local_file_context()
            if local_file_context:
                return f"{self.user_input}\n\n[本地文件内容]\n{local_file_context}"
        
        return self.user_input
    
    def handle_ceo_task_completion(self, response: str) -> bool:
        """
        处理CEO标记任务完成的逻辑
        
        Args:
            response (str): CEO的回复
            
        Returns:
            bool: 是否处理了任务完成
        """
        if "[TASK_DONE]" not in response.upper():
            return False
            
        task_number = AgentUtils.parse_task_number_from_ceo_response(response)
        if task_number is None:
            logger.warning("CEO 回复中包含 [TASK_DONE] 标记，但无法解析任务编号")
            print("\n[警告] CEO 回复中包含 [TASK_DONE] 标记，但无法解析任务编号。请确保标记格式为 '[TASK_DONE] 任务 #任务编号 已完成'。")
            return False
            
        task_index = task_number - 1
        if not self.todo_list.complete_task(task_index):
            logger.warning(f"CEO 尝试标记任务 #{task_number} 为完成，但任务编号无效")
            print(f"\n[警告] CEO 尝试标记任务 #{task_number} 为完成，但任务编号无效，操作忽略。")
            return False
            
        logger.info(f"CEO 标记 To-Do List 中 任务 #{task_number} 已完成")
        print(f"\n[CEO 标记完成] CEO 标记 To-Do List 中 任务 #{task_number} 已完成。")
        return True
    
    def handle_agent_task_completion(self, response: str) -> bool:
        """
        处理其他智能体标记任务完成的逻辑
        
        Args:
            response (str): 智能体的回复
            
        Returns:
            bool: 是否处理了任务完成
        """
        if "[TASK_DONE]" not in response.upper() and "[DONE]" not in response.upper():
            return False
            
        task_index = self.todo_list.find_task_for_agent(self.current_agent)
        if task_index is not None:
            self.todo_list.complete_task(task_index)
            logger.info(f"@{self.current_agent} 标记 To-Do List 中 任务 #{task_index+1} 已完成")
            print(f"\n[Agent 标记完成] @{self.current_agent} 标记 To-Do List 中 任务 #{task_index+1} 已完成。")
            return True
            
        return False
    
    def process_response(self, response: str) -> None:
        """
        处理智能体响应，更新任务状态，确定下一个智能体
        
        Args:
            response (str): 智能体的回复
        """
        if response == "[API_ERROR]":
            logger.error("API 调用失败，流程中断")
            print("\n[Workflow Error] API 调用失败，流程中断。")
            self.workflow_active = False
            return
            
        self.history.append(response)
        
        if self.current_agent == "ceo":
            mentioned_agents = AgentUtils.parse_mentions(response)
            for agent in mentioned_agents:
                if agent and agent != "ceo":
                    self.todo_list.add_task(agent, "请完成 CEO 指派的任务 (具体请查看完整对话记录)")
                    
            self.handle_ceo_task_completion(response)
            completed_tasks = self.todo_list.remove_completed_tasks()
            for task in completed_tasks:
                logger.info(f"任务 '{task.description}' (指派给 @{task.agent}) 已完成，从 To-Do List 中移除")
                print(f"\n[CEO 确认] 任务 '{task.description}' (指派给 @{task.agent}) 已完成，从 To-Do List 中移除。")
        
        elif self.current_agent in ["writer", "programmer", "reviewer", "analyst"]:
            self.handle_agent_task_completion(response)
        
        next_agents = AgentUtils.parse_mentions(response)
        if next_agents and next_agents[0] in self.agents:
            self.current_agent = next_agents[0]
            logger.info(f"工作流转向 {self.agents[self.current_agent].name} (@{self.current_agent})")
        else:
            logger.info("未指定下一步 Agent，自动转交 CEO")
            print("\n[自动流转] 未指定下一步 Agent，自动转交 CEO...")
            self.current_agent = "ceo"
            self.user_input = "当前流程步骤未明确指定后续执行者，请CEO根据当前的工作进展，Review 上下文对话记录，并判断下一步应该由哪个 Agent 继续执行，或者由CEO发布新的指令。"
        
        context = response[-1000:]
        self.user_input = context
    
    def handle_user_input_during_pause(self) -> None:
        """处理工作流暂停时的用户输入"""
        prompt_message = f"\n=== 请继续指示 {self.agents[self.current_agent].name} (@{self.current_agent}) ==="
        print(prompt_message, end='', flush=True)
        user_input = input()
        
        if user_input.startswith("@"):
            self.workflow_active = True
            current_agent_from_input = user_input[1:].split(" ")[0].lower()
            if current_agent_from_input in self.agents:
                self.current_agent = current_agent_from_input
                self.history = []
                self.user_input = user_input
                logger.info(f"用户手动切换到智能体 @{current_agent_from_input}")
            else:
                logger.warning(f"未识别到智能体 @{current_agent_from_input}")
                print(f"未识别到智能体 @{current_agent_from_input}")
                self.workflow_active = False
        else:
            self.workflow_active = True
            self.history.append(user_input)
            self.user_input = user_input
    
    def _create_agents(self) -> Dict[str, Agent]:
        """
        创建并返回所有工作流中使用的智能体。
        
        Returns:
            Dict[str, Agent]: 智能体字典，键为智能体ID，值为Agent对象
        """
        return {
            "analyst": Agent("分析官", """您是需求分析专家，负责拆解用户需求并生成执行指南。请：
1. 分析故事类型、主题和风格
2. 设计主要角色设定
3. 规划章节结构
4. 列出需要代码实现的功能
**您可以使用浏览器查找网络信息，访问本地文件夹和文件，并制作新的文件。**
最后用@ceo结束"""),

            "ceo": Agent("首席执行官", """您是项目总负责人，根据分析官的报告和用户提供的本地文件：
1. 制定详细执行计划
2. **重要：请务必检查 To-Do List，确认是否有已完成的任务。对于状态为"已完成"的任务，请进行确认，并在您的回复中明确指出已完成的任务，将其从 To-Do List 中移除。**
3. 根据任务类型调用对应智能体：
   - 写作任务@writer
   - 代码任务@programmer
   - 需要审核@reviewer
**您可以使用浏览器查找网络信息，访问本地文件夹和文件，并制作新的文件。在制定计划时，请充分考虑用户提供的本地文件内容以及 To-Do List 中待处理的任务。**

**如果您认为 To-Do List 中某个任务已经完成，请在您的回复的末尾使用提示词 `[TASK_DONE] 任务 #任务编号 已完成` 来明确标记，例如 `[TASK_DONE] 任务 #1 已完成`。请务必使用正确的任务编号，编号请参考当前显示的 To-Do List 表格中的 "任务 #" 列。**

最后用@目标角色结束。"""),

            "writer": Agent("小说家", """您是专业小说作家，请：
1. 根据大纲创作故事内容
2. 保持风格统一
3. 每完成一章后@reviewer
**您可以使用浏览器查找资料，访问项目文件夹中的文件，并创建新的文稿。**
如需继续写作@writer"""),

            "programmer": Agent("程序员", """您是技术专家，负责：
1. 编写符合情节的技术实现
2. 输出完整可运行的代码
3. 添加详细注释
**您可以使用浏览器查找技术文档，访问项目文件夹中的文件，并创建新的代码文件。**
完成后@reviewer"""),

            "reviewer": Agent("审核员", """您是质量控制专家，请：
1. 检查内容是否符合要求
2. 提出3条改进建议
3. 用@ceo返回修改意见
**您可以使用浏览器进行信息核对，访问项目文件夹中的文件，辅助您进行审核工作。**""")
        }
    
    def run(self) -> None:
        """运行工作流"""
        logger.info("开始运行多智能体工作流")
        self.initialize_project()
        
        while True:
            if self.workflow_active:
                self.todo_list.display()
                
                print(f"\n=== {self.agents[self.current_agent].name} 工作中 ===")
                prepared_input = self.prepare_user_input()
                response = self.agents[self.current_agent].generate_response(prepared_input)
                
                self.process_response(response)
            else:
                self.handle_user_input_during_pause()


def main():
    """主函数"""
    print("=== 多智能体工作流系统 ===")
    print("版本: 1.0.0")
    print("说明: 本系统将协调多个AI智能体共同完成创作任务")
    print("------------------------------")
    user_request = input("请输入您的创作需求：")
    workflow_manager = WorkflowManager(user_request)
    workflow_manager.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[系统] 用户中断，程序退出")
    except Exception as e:
        logger.critical(f"程序发生未处理异常: {e}", exc_info=True)
        print(f"\n[错误] 程序发生异常: {e}")
        print("请查看日志获取详细信息")
        