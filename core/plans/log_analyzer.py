import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import re
import time
import concurrent.futures

from core.base_processor import BaseDocProcessor
from core.prompts.log_analysis import (
    LOG_ANALYSIS_PROMPT,
    LOG_SUMMARY_PROMPT,
    ERROR_ANALYSIS_PROMPT,
    PERFORMANCE_ANALYSIS_PROMPT,
    SECURITY_ANALYSIS_PROMPT,
    BUSINESS_ANALYSIS_PROMPT,
    SYSTEM_STATUS_PROMPT
)
from kbx.common.logging import logger

CHINA_TZ = pytz.timezone('Asia/Shanghai')

class AIModelLogAnalyzer(BaseDocProcessor):
    """
    AI大模型日志分析器
    
    提供以下功能：
    1. 性能指标分析（延迟、吞吐量、资源使用等）
    2. 错误和异常分析
    3. 请求模式分析
    4. 成本分析
    5. 资源使用监控
    6. 可视化报告生成
    """
    
    def __init__(self, kb_name: str = "AI模型日志知识库",
                 kb_description: str = "这是一个AI大模型日志分析知识库",
                 llm_model: str = 'deepseek-v3'):
        super().__init__(kb_name=kb_name,
                        kb_description=kb_description,
                        llm_model=llm_model)
        
    def analyze_logs(self, log_file_path: str, max_workers: int = None, chunk_size: int = None) -> Dict[str, Any]:
        """
        分析AI模型日志文件并生成分析报告
        
        Args:
            log_file_path: 日志文件路径
            max_workers: 最大工作线程数
            chunk_size: 日志分块大小
            
        Returns:
            包含分析结果的字典
        """
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在：{log_file_path}")
            
        # 解析和分割日志
        docdata, self.all_chunks = self.parse_and_split(log_file_path, chunk_size)
        if not self.all_chunks:
            logger.warning("没有找到任何日志内容")
            return {}
            
        # 提取日志标签
        log_tags = self._extract_log_tags(max_workers)
        
        # 生成分析报告
        report = self._generate_analysis_report(log_tags)
        
        # 生成可视化图表
        self._generate_visualizations(report)
        
        return report
        
    def _extract_log_tags(self, max_workers: int = None) -> List[Dict[str, Any]]:
        """从日志中提取标签"""
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            chunk_futures = {executor.submit(self._process_log_chunk, chunk): i 
                           for i, chunk in enumerate(self.all_chunks)}
            
            all_results = [None] * len(self.all_chunks)
            completed = 0
            total = len(chunk_futures)
            
            for future in concurrent.futures.as_completed(chunk_futures):
                chunk_index = chunk_futures[future]
                try:
                    chunk_results = future.result()
                    all_results[chunk_index] = chunk_results or []
                    
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        logger.info(f"进度: {completed}/{total} 块已处理 ({completed/total*100:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"处理日志块 {chunk_index} 时出错: {e}")
                    all_results[chunk_index] = []
                    
        all_results = [result for results in all_results if results for result in results]
        unique_results = self._deduplicate_results(all_results)
        
        total_time = time.time() - start_time
        logger.info(f"日志标签提取总耗时: {total_time:.2f}秒")
        
        return unique_results
        
    def _process_log_chunk(self, chunk: Any) -> List[Dict[str, Any]]:
        """处理单个日志块"""
        try:
            # 准备数据
            user_input = json.dumps({
                'text': chunk.text,
                'log_patterns': {
                    'performance': r'(latency|throughput|gpu_usage|memory_usage)',
                    'error': r'(error|exception|failed|timeout)',
                    'request': r'(request|query|prompt|completion)',
                    'cost': r'(cost|token|price)',
                    'resource': r'(gpu|memory|cpu|disk)'
                }
            }, ensure_ascii=False)
            
            # 调用LLM进行标签提取
            response = self.call_llm(
                system_prompt=LOG_ANALYSIS_PROMPT,
                user_input=user_input
            )
            
            # 解析响应
            cleaned_response = self._clean_json_string(response)
            results = json.loads(cleaned_response)
            
            return results
            
        except Exception as e:
            logger.error(f"处理日志块失败: {e}")
            return []
            
    def _generate_analysis_report(self, log_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成日志分析报告"""
        # 按标签类型分组
        grouped_tags = self._group_tags_by_type(log_tags)
        
        # 生成各部分分析报告
        report = {
            'summary': self._generate_summary(grouped_tags),
            'performance_analysis': self._analyze_performance(grouped_tags.get('性能指标', [])),
            'error_analysis': self._analyze_errors(grouped_tags.get('错误', [])),
            'request_analysis': self._analyze_requests(grouped_tags.get('请求', [])),
            'cost_analysis': self._analyze_costs(grouped_tags.get('成本', [])),
            'resource_analysis': self._analyze_resources(grouped_tags.get('资源', []))
        }
        
        return report
        
    def _generate_visualizations(self, report: Dict[str, Any]) -> None:
        """生成可视化图表"""
        plt.style.use('seaborn')
        
        # 1. 性能指标趋势图
        if 'performance_analysis' in report:
            perf_data = report['performance_analysis'].get('metrics', {})
            if perf_data:
                plt.figure(figsize=(12, 6))
                for metric, values in perf_data.items():
                    plt.plot(values, label=metric)
                plt.title('AI模型性能指标趋势')
                plt.legend()
                plt.savefig('performance_trends.png')
                plt.close()
                
        # 2. 错误分布饼图
        if 'error_analysis' in report:
            error_data = report['error_analysis'].get('error_types', {})
            if error_data:
                plt.figure(figsize=(10, 6))
                plt.pie(error_data.values(), labels=error_data.keys(), autopct='%1.1f%%')
                plt.title('AI模型错误分布')
                plt.savefig('error_distribution.png')
                plt.close()
                
        # 3. 请求模式热力图
        if 'request_analysis' in report:
            request_data = report['request_analysis'].get('patterns', {})
            if request_data:
                plt.figure(figsize=(10, 6))
                sns.heatmap(pd.DataFrame(request_data).T, annot=True, cmap='YlOrRd')
                plt.title('请求模式分布')
                plt.savefig('request_patterns.png')
                plt.close()
                
        # 4. 成本分析柱状图
        if 'cost_analysis' in report:
            cost_data = report['cost_analysis'].get('costs', {})
            if cost_data:
                plt.figure(figsize=(10, 6))
                plt.bar(cost_data.keys(), cost_data.values())
                plt.title('AI模型成本分析')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig('cost_analysis.png')
                plt.close()
                
        # 5. 资源使用仪表盘
        if 'resource_analysis' in report:
            resource_data = report['resource_analysis'].get('usage', {})
            if resource_data:
                plt.figure(figsize=(8, 8))
                plt.pie([resource_data.get('used', 0), 100-resource_data.get('used', 0)], 
                       labels=['已使用', '未使用'], colors=['red', 'green'], autopct='%1.1f%%')
                plt.title('资源使用情况')
                plt.savefig('resource_usage.png')
                plt.close()
                
    def _analyze_performance(self, perf_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能指标"""
        perf_input = json.dumps(perf_tags, ensure_ascii=False)
        response = self.call_llm(
            system_prompt=PERFORMANCE_ANALYSIS_PROMPT,
            user_input=perf_input
        )
        return json.loads(response)
        
    def _analyze_errors(self, error_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析错误日志"""
        error_input = json.dumps(error_tags, ensure_ascii=False)
        response = self.call_llm(
            system_prompt=ERROR_ANALYSIS_PROMPT,
            user_input=error_input
        )
        return json.loads(response)
        
    def _analyze_requests(self, request_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析请求模式"""
        request_input = json.dumps(request_tags, ensure_ascii=False)
        response = self.call_llm(
            system_prompt=BUSINESS_ANALYSIS_PROMPT,
            user_input=request_input
        )
        return json.loads(response)
        
    def _analyze_costs(self, cost_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析成本"""
        cost_input = json.dumps(cost_tags, ensure_ascii=False)
        response = self.call_llm(
            system_prompt=BUSINESS_ANALYSIS_PROMPT,
            user_input=cost_input
        )
        return json.loads(response)
        
    def _analyze_resources(self, resource_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析资源使用"""
        resource_input = json.dumps(resource_tags, ensure_ascii=False)
        response = self.call_llm(
            system_prompt=SYSTEM_STATUS_PROMPT,
            user_input=resource_input
        )
        return json.loads(response)
        
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        json_str = json_str.strip()
        json_str = json_str.lstrip('```json').rstrip('```')
        json_str = json_str.strip()
        json_str = re.sub(r'\[\s+', '[', json_str)
        json_str = re.sub(r'\s+\]', ']', json_str)
        json_str = re.sub(r'{\s+', '{', json_str)
        json_str = re.sub(r'\s+}', '}', json_str)
        json_str = re.sub(r'\n\s*\n', '\n', json_str)
        return json_str
        
    def _group_tags_by_type(self, log_tags: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按标签类型分组"""
        grouped = {}
        for tag in log_tags:
            tag_type = tag.get('type')
            if tag_type:
                if tag_type not in grouped:
                    grouped[tag_type] = []
                grouped[tag_type].append(tag)
        return grouped
        
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重结果"""
        if not results:
            return []
            
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.get('type'), result.get('content'))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                
        return unique_results
