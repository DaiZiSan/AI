import os
import shutil
from datetime import datetime
from .base_agent import Agent
import logging

logger = logging.getLogger(__name__)

class FileOrganizerAgent(Agent):
    """文件整理员，负责管理和组织用户文件"""
    
    def __init__(self):
        super().__init__("file_organizer", "文件整理员")
        self.system_prompt = """你是一位专业的文件整理员，负责管理和组织用户的文件系统。
你的任务是：
1. 浏览文件系统
2. 整理和分类文件
3. 创建文件夹结构
4. 重命名和移动文件
5. 生成文件报告"""

    def browse_directory(self, path='.'):
        """浏览目录"""
        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                item_info = {
                    'name': item,
                    'path': full_path,
                    'type': 'directory' if os.path.isdir(full_path) else 'file',
                    'size': os.path.getsize(full_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(full_path))
                }
                items.append(item_info)
            return items
        except Exception as e:
            logger.error(f"浏览目录失败: {str(e)}")
            return []

    def organize_files(self, path, pattern=None):
        """整理文件"""
        try:
            # 按文件类型分类
            extensions = {
                'documents': ['.pdf', '.doc', '.docx', '.txt', '.md'],
                'images': ['.jpg', '.jpeg', '.png', '.gif'],
                'audio': ['.mp3', '.wav', '.flac'],
                'video': ['.mp4', '.avi', '.mkv'],
                'code': ['.py', '.js', '.html', '.css', '.json']
            }
            
            # 创建分类目录
            for category in extensions:
                os.makedirs(os.path.join(path, category), exist_ok=True)
            
            # 移动文件
            moved_files = []
            for item in os.listdir(path):
                if os.path.isfile(os.path.join(path, item)):
                    ext = os.path.splitext(item)[1].lower()
                    for category, exts in extensions.items():
                        if ext in exts:
                            src = os.path.join(path, item)
                            dst = os.path.join(path, category, item)
                            shutil.move(src, dst)
                            moved_files.append((item, category))
                            break
            
            return moved_files
        except Exception as e:
            logger.error(f"整理文件失败: {str(e)}")
            return []

    def generate_response(self, user_input):
        """生成响应"""
        if "浏览" in user_input:
            path = user_input.split("浏览")[-1].strip() or '.'
            items = self.browse_directory(path)
            
            response = f"## 目录内容: {path}\n\n"
            for item in items:
                icon = "📁" if item['type'] == 'directory' else "📄"
                size = f"{item['size'] / 1024:.1f} KB"
                modified = item['modified'].strftime("%Y-%m-%d %H:%M")
                response += f"{icon} {item['name']}\n"
                response += f"大小: {size} | 修改时间: {modified}\n\n"
            
        elif "整理" in user_input:
            path = user_input.split("整理")[-1].strip() or '.'
            moved_files = self.organize_files(path)
            
            response = f"## 文件整理报告\n\n"
            if moved_files:
                for file, category in moved_files:
                    response += f"- 已将 {file} 移动到 {category} 目录\n"
            else:
                response += "没有找到需要整理的文件。\n"
                
        else:
            response = "我可以帮您:\n"
            response += "1. 浏览目录内容 (例如: '浏览 /path/to/directory')\n"
            response += "2. 整理文件 (例如: '整理 /path/to/directory')\n"
            
        return response