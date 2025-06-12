"""
AI运维引擎核心类
负责协调多个Agent进行智能运维
"""

from typing import Dict, List, Optional
import logging
from ..agents.sre_agent import SREAgent
from ..agents.code_agent import CodeAgent
from ..agents.report_agent import ReportAgent
from ..agents.vis_agent import VisAgent
from ..agents.data_agent import DataAgent

class AIOpsEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sre_agent = SREAgent()
        self.code_agent = CodeAgent()
        self.report_agent = ReportAgent()
        self.vis_agent = VisAgent()
        self.data_agent = DataAgent()
        
    def analyze_incident(self, incident_data: Dict) -> Dict:
        """
        分析运维事件
        
        Args:
            incident_data: 事件数据，包含日志、指标等
            
        Returns:
            Dict: 分析结果
        """
        # 1. 数据预处理
        processed_data = self.data_agent.preprocess(incident_data)
        
        # 2. SRE分析
        sre_analysis = self.sre_agent.analyze(processed_data)
        
        # 3. 代码分析
        code_analysis = self.code_agent.analyze(sre_analysis)
        
        # 4. 生成报告
        report = self.report_agent.generate_report(sre_analysis, code_analysis)
        
        # 5. 可视化
        visualization = self.vis_agent.visualize(report)
        
        return {
            "analysis": sre_analysis,
            "code_analysis": code_analysis,
            "report": report,
            "visualization": visualization
        }
    
    def handle_alert(self, alert_data: Dict) -> Dict:
        """
        处理告警
        
        Args:
            alert_data: 告警数据
            
        Returns:
            Dict: 处理结果
        """
        # 1. 告警分析
        alert_analysis = self.sre_agent.analyze_alert(alert_data)
        
        # 2. 生成处理方案
        solution = self.code_agent.generate_solution(alert_analysis)
        
        # 3. 执行处理
        result = self.sre_agent.execute_solution(solution)
        
        # 4. 生成报告
        report = self.report_agent.generate_alert_report(alert_analysis, result)
        
        return {
            "alert_analysis": alert_analysis,
            "solution": solution,
            "result": result,
            "report": report
        }
    
    def monitor_system(self, metrics: Dict) -> Dict:
        """
        系统监控
        
        Args:
            metrics: 系统指标数据
            
        Returns:
            Dict: 监控结果
        """
        # 1. 指标分析
        metrics_analysis = self.data_agent.analyze_metrics(metrics)
        
        # 2. 异常检测
        anomalies = self.sre_agent.detect_anomalies(metrics_analysis)
        
        # 3. 生成监控报告
        report = self.report_agent.generate_monitoring_report(metrics_analysis, anomalies)
        
        # 4. 可视化
        visualization = self.vis_agent.visualize_metrics(metrics_analysis, anomalies)
        
        return {
            "metrics_analysis": metrics_analysis,
            "anomalies": anomalies,
            "report": report,
            "visualization": visualization
        } 