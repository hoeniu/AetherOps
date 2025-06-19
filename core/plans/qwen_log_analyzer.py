import os
import json
from typing import Dict, List, Any
from datetime import datetime
import pytz
import dashscope
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from qwen_agent.agents import Assistant
from qwen_agent.tools.base import BaseTool, register_tool
from qwen_agent.utils.output_beautify import typewriter_print

CHINA_TZ = pytz.timezone('Asia/Shanghai')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def configure_api_key(api_key: str = None):
    """配置API Key"""
    if api_key:
        dashscope.api_key = api_key
    elif os.getenv('DASHSCOPE_API_KEY'):
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
    else:
        raise ValueError(
            "未提供API Key。请通过以下方式之一设置API Key：\n"
            "1. 在代码中设置：dashscope.api_key = 'your_api_key'\n"
            "2. 设置环境变量：export DASHSCOPE_API_KEY='your_api_key'\n"
            "3. 使用API Key文件：dashscope.api_key_file_path='path/to/api_key_file'\n"
            "4. 设置API Key文件路径环境变量：export DASHSCOPE_API_KEY_FILE_PATH='path/to/api_key_file'"
        )

def generate_visualizations(analysis_data: Dict[str, Any], output_dir: str = "analysis_results"):
    """生成可视化图表"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 性能指标趋势图
    if 'performance_metrics' in analysis_data:
        plt.figure(figsize=(12, 6))
        metrics_df = pd.DataFrame(analysis_data['performance_metrics'])
        sns.lineplot(data=metrics_df, x='timestamp', y='value', hue='metric')
        plt.title('性能指标趋势')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'performance_trends.png'))
        plt.close()

    # 2. 错误分布饼图
    if 'error_distribution' in analysis_data:
        plt.figure(figsize=(10, 10))
        error_df = pd.DataFrame(analysis_data['error_distribution'])
        plt.pie(error_df['count'], labels=error_df['type'], autopct='%1.1f%%')
        plt.title('错误类型分布')
        plt.savefig(os.path.join(output_dir, 'error_distribution.png'))
        plt.close()

    # 3. 请求模式热力图
    if 'request_patterns' in analysis_data:
        plt.figure(figsize=(12, 8))
        request_df = pd.DataFrame(analysis_data['request_patterns'])
        sns.heatmap(request_df.pivot_table(
            values='count',
            index='hour',
            columns='type'
        ), annot=True, fmt='d', cmap='YlOrRd')
        plt.title('请求模式热力图')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'request_patterns.png'))
        plt.close()

    # 4. 资源使用堆叠图
    if 'resource_usage' in analysis_data:
        plt.figure(figsize=(12, 6))
        resource_df = pd.DataFrame(analysis_data['resource_usage'])
        resource_df.pivot_table(
            values='usage',
            index='timestamp',
            columns='resource'
        ).plot(kind='area', stacked=True)
        plt.title('资源使用趋势')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'resource_usage.png'))
        plt.close()

    # 5. 成本分析柱状图
    if 'cost_analysis' in analysis_data:
        plt.figure(figsize=(10, 6))
        cost_df = pd.DataFrame(analysis_data['cost_analysis'])
        sns.barplot(data=cost_df, x='category', y='cost')
        plt.title('成本分析')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'cost_analysis.png'))
        plt.close()

@register_tool('log_analyzer')
class LogAnalyzerTool(BaseTool):
    """日志分析工具，用于分析AI模型日志文件"""
    description = '分析AI模型日志文件，提取性能指标、错误信息、请求模式等信息'
    parameters = [{
        'name': 'log_file',
        'type': 'string',
        'description': '日志文件路径',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        try:
            log_file = json.loads(params)['log_file']
            if not os.path.exists(log_file):
                return json.dumps({
                    'error': f'日志文件不存在：{log_file}'
                }, ensure_ascii=False)

            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 返回日志内容供LLM分析
            return json.dumps({
                'content': content,
                'timestamp': datetime.now(CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'error': f'处理日志文件时出错：{str(e)}'
            }, ensure_ascii=False)

def create_log_analyzer(api_key: str = None) -> Assistant:
    """创建日志分析助手"""
    # 配置API Key
    configure_api_key(api_key)
    
    # 配置LLM
    llm_cfg = {
        'model': 'qwen2.5-72b-instruct',
        'model_type': 'qwen_dashscope',
        'generate_cfg': {
            'top_p': 0.8
        }
    }

    # 系统提示词
    system_instruction = '''你是一个专业的AI模型日志分析助手。你的任务是：
1. 分析日志文件中的性能指标（延迟、吞吐量、资源使用等）
2. 识别和分类错误和异常
3. 分析请求模式和用户行为
4. 计算成本和使用情况
5. 监控资源使用情况
6. 生成清晰的分析报告

请用中文回复，并确保分析结果准确、专业且易于理解。
分析结果需要包含以下结构化数据：
- performance_metrics: 性能指标数据
- error_distribution: 错误分布数据
- request_patterns: 请求模式数据
- resource_usage: 资源使用数据
- cost_analysis: 成本分析数据'''

    # 创建助手实例
    bot = Assistant(
        llm=llm_cfg,
        system_message=system_instruction,
        function_list=['log_analyzer', 'code_interpreter']
    )

    return bot

def analyze_logs(log_file: str, api_key: str = None, output_dir: str = "analysis_results") -> Dict[str, Any]:
    """分析日志文件并返回分析结果"""
    try:
        bot = create_log_analyzer(api_key)
        
        # 构建分析请求
        messages = [{
            'role': 'user',
            'content': f'请分析这个日志文件：{log_file}'
        }]

        # 执行分析
        response = []
        response_plain_text = ''
        print('开始分析日志...')
        
        for resp in bot.run(messages=messages):
            response_plain_text = typewriter_print(resp, response_plain_text)
            response.extend(resp)

        # 尝试解析分析结果中的结构化数据
        try:
            analysis_data = json.loads(response_plain_text)
            # 生成可视化图表
            generate_visualizations(analysis_data, output_dir)
            print(f"\n可视化图表已保存到目录：{output_dir}")
        except json.JSONDecodeError:
            print("警告：无法解析结构化数据，跳过图表生成")

        return {
            'messages': response,
            'analysis': response_plain_text
        }
    except Exception as e:
        print(f"分析过程中发生错误：{e}")
        return {
            'error': str(e),
            'messages': [],
            'analysis': ''
        }

def analyze_logs_stream(log_file: str, api_key: str = None, output_dir: str = "analysis_results"):
    """流式分析日志文件，分阶段yield分析结果"""
    try:
        bot = create_log_analyzer(api_key)
        messages = [{
            'role': 'user',
            'content': f'请分析这个日志文件：{log_file}'
        }]
        response_plain_text = ''
        # 流式获取LLM输出
        for resp in bot.run(messages=messages):
            response_plain_text = typewriter_print(resp, response_plain_text)
            # 尝试解析结构化数据
            try:
                analysis_data = json.loads(response_plain_text)
                # 每个阶段单独yield
                if 'performance_metrics' in analysis_data:
                    yield {'step': '性能指标', 'data': analysis_data['performance_metrics']}
                if 'error_distribution' in analysis_data:
                    yield {'step': '错误分析', 'data': analysis_data['error_distribution']}
                if 'request_patterns' in analysis_data:
                    yield {'step': '请求模式', 'data': analysis_data['request_patterns']}
                if 'resource_usage' in analysis_data:
                    yield {'step': '资源使用', 'data': analysis_data['resource_usage']}
                if 'cost_analysis' in analysis_data:
                    yield {'step': '成本分析', 'data': analysis_data['cost_analysis']}
                break  # 只yield一次完整结构化数据即可
            except Exception:
                # 还未到结构化数据阶段，继续流式输出文本
                yield {'step': 'llm_output', 'data': response_plain_text}
    except Exception as e:
        yield {'step': 'error', 'data': str(e)}

if __name__ == "__main__":
    # 示例用法
    log_file = "core/data/k8s-volcano-controller.log"
    output_dir = "analysis_results"
    
    # 从环境变量或命令行参数获取API Key
    api_key = os.getenv('DASHSCOPE_API_KEY')
    
    try:
        result = analyze_logs(log_file, api_key, output_dir)
        if 'error' in result:
            print(f"\n错误：{result['error']}")
        else:
            print("\n分析完成！")
            print("\n=== 分析结果 ===")
            print(result['analysis'])
            print(f"\n可视化图表已保存到：{output_dir}")
    except Exception as e:
        print(f"分析过程中发生错误：{e}") 