import requests
from bs4 import BeautifulSoup
from .base_agent import Agent
import logging

logger = logging.getLogger(__name__)

class WebSearchAgent(Agent):
    """网络搜索员，负责搜索互联网信息"""
    
    def __init__(self):
        super().__init__("web_searcher", "网络搜索员")
        self.system_prompt = """你是一位专业的网络搜索员，负责在互联网上查找信息。
你的任务是：
1. 分析用户的搜索需求
2. 提供最相关、最准确的搜索结果
3. 整理信息并以清晰的格式呈现
4. 提供信息来源链接"""

    def search_web(self, query):
        """执行网络搜索"""
        try:
            # 使用DuckDuckGo搜索API
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # 处理搜索结果
                for result in data.get('RelatedTopics', [])[:5]:
                    if 'Text' in result:
                        results.append({
                            'title': result.get('Text', '').split(' - ')[0],
                            'description': result.get('Text', ''),
                            'url': result.get('FirstURL', '')
                        })
                
                return results
            else:
                logger.error(f"搜索请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"搜索出错: {str(e)}")
            return []

    def generate_response(self, user_input):
        """生成搜索响应"""
        # 执行搜索
        results = self.search_web(user_input)
        
        if not results:
            return f'抱歉，我无法找到关于"{user_input}"的搜索结果。请尝试使用不同的关键词。'
        
        for i, result in enumerate(results, 1):
            response += f"### {i}. {result['title']}\n"
            response += f"{result['description']}\n"
            if result['url']:
                response += f"[查看详情]({result['url']})\n"
            response += "\n---\n\n"
        
        return response