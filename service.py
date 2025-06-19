import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json

# 设置页面配置
st.set_page_config(
    page_title="AetherOps - AI驱动的DevOps平台",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background-color: #f5f5f5;
        padding: 2rem;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: linear-gradient(180deg, #0F172A 0%, #1E1B4B 100%) !important;
        width: 220px !important;
        min-width: 220px !important;
    }
    
    /* 侧边栏内容容器 */
    .css-1siy2j7 {
        width: 220px !important;
        min-width: 220px !important;
    }
    
    /* Logo样式 */
    .logo-container {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 10px;
    }
    
    .logo-container img {
        width: 120px;
        height: 120px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .logo-container img:hover {
        transform: scale(1.05);
    }
    
    /* 标题样式 */
    .nav-title {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 24px;
        font-weight: bold;
        padding: 20px 0;
        text-align: center;
        margin-bottom: 20px;
        letter-spacing: 1px;
        position: relative;
    }
    
    .nav-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3B82F6, transparent);
    }
    
    .nav-subtitle {
        color: #94A3B8;
        font-size: 14px;
        text-align: center;
        margin-top: -15px;
        margin-bottom: 25px;
        letter-spacing: 2px;
    }
    
    /* 导航按钮样式 */
    .nav-button {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(59, 130, 246, 0.1);
        color: #94A3B8;
        padding: 12px 15px;
        margin: 6px 0;
        width: 100%;
        text-align: left;
        border-radius: 8px;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;
        position: relative;
        overflow: hidden;
    }
    
    .nav-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(59, 130, 246, 0.2),
            transparent
        );
        transition: 0.5s;
    }
    
    .nav-button:hover::before {
        left: 100%;
    }
    
    .nav-button:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #E2E8F0;
        transform: translateX(3px);
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    }
    
    .nav-button.active {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
        color: #FFFFFF;
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    
    .nav-button.active::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        50% {
            transform: scale(1);
            opacity: 0.2;
        }
        100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
    }
    
    /* 图标样式 */
    .nav-icon {
        font-size: 18px;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 2px rgba(59, 130, 246, 0.3));
    }
    
    /* 主内容区域样式 */
    .main .block-container {
        padding: 1.5rem;
        max-width: 1600px;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        border: 1px solid #E2E8F0;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 10px rgba(0,0,0,0.15);
    }
    
    /* 图表容器样式 */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 15px 0;
        border: 1px solid #E2E8F0;
    }
    
    /* 自定义滚动条 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0F172A;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3B82F6, #8B5CF6);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #2563EB, #7C3AED);
    }
    
    /* 修复历史和详情标题样式 */
    .repair-section-title {
        background: linear-gradient(90deg, #1E40AF, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 28px;
        font-weight: 800;
        padding: 10px 0;
        margin-bottom: 20px;
        text-align: left;
        position: relative;
        display: inline-block;
    }
    
    .repair-section-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #1E40AF, #7C3AED);
        border-radius: 2px;
    }
    
    .repair-history-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    
    .repair-type-auto {
        background: linear-gradient(90deg, #dbeafe 60%, #f0fdfa 100%);
        color: #2563eb;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 13px;
        margin-right: 8px;
    }
    
    .repair-type-manual {
        background: linear-gradient(90deg, #fef9c3 60%, #f3e8ff 100%);
        color: #b45309;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 13px;
        margin-right: 8px;
    }
    
    .stButton button {
        width: 100%;
        text-align: left;
        background: #fff;
        border: 1.5px solid #e0e7ef;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 12px rgba(59,130,246,0.1);
        transform: translateY(-1px);
    }
    
    .stButton button.selected {
        border-color: #3B82F6;
        background: linear-gradient(90deg, #f0f7ff 0%, #f5f3ff 100%);
        box-shadow: 0 4px 12px rgba(59,130,246,0.15);
    }
    
    .repair-process-btn {
        background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59,130,246,0.15);
    }
    
    .repair-process-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(59,130,246,0.25);
    }
</style>
""", unsafe_allow_html=True)

# 导航图标映射
nav_icons = {
    "仪表盘": "📊",
    "智能部署": "🚀",
    "系统监控": "📈",
    "AI修复中心": "🔧",
    "环境管理": "🌍",
    "知识库": "📚",
    "运维工具": "🛠️"
}

# 侧边栏
with st.sidebar:
    # 添加Logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("images/logo.png", width=120, use_container_width=False)
    
    # 导航标题
    st.markdown('<div class="nav-title" style="margin-top: 0; padding-top: 10px;">AetherOps</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-subtitle" style="margin-top: -15px;">AI驱动的DevOps平台</div>', unsafe_allow_html=True)
    
    # 创建导航按钮
    for nav_item, icon in nav_icons.items():
        if st.button(f"{icon} {nav_item}", key=nav_item, 
                    help=f"点击进入{nav_item}页面",
                    use_container_width=True):
            st.session_state.page = nav_item

# 设置默认页面
if 'page' not in st.session_state:
    st.session_state.page = "仪表盘"

# 页面内容
page = st.session_state.page

# 模拟数据生成函数
def generate_metrics():
    return {
        "系统健康度": random.randint(85, 100),
        "部署成功率": random.randint(95, 100),
        "平均响应时间": random.randint(100, 500),
        "AI修复成功率": random.randint(80, 95)
    }

def generate_deployment_data():
    dates = pd.date_range(start='2024-01-01', end='2024-03-15', freq='D')
    return pd.DataFrame({
        'date': dates,
        'deployments': [random.randint(1, 5) for _ in range(len(dates))],
        'success_rate': [random.uniform(0.95, 1.0) for _ in range(len(dates))]
    })

# 修复历史模拟数据
repair_history = [
    {
        "id": 1,
        "time": "2024-06-01 10:00",
        "type": "自动修复",
        "desc": "容器CPU异常，已自动重启docker_001",
        "status": "成功",
        "detail": {
            "root_cause": "docker_001 CPU使用率持续超标",
            "steps": [
                "检测到CPU异常",
                "自动重启docker_001",
                "监控恢复正常"
            ],
            "chain": ["异常检测", "自动修复", "验证通过"],
            "trend": [82, 85, 90, 103, 80]
        }
    },
    {
        "id": 2,
        "time": "2024-05-31 16:30",
        "type": "手动修复",
        "desc": "数据库连接超时，人工介入优化配置",
        "status": "成功",
        "detail": {
            "root_cause": "数据库连接池配置不足",
            "steps": [
                "检测到连接超时",
                "人工调整连接池参数",
                "重启数据库服务"
            ],
            "chain": ["异常检测", "人工修复", "验证通过"],
            "trend": [60, 70, 80, 65, 55]
        }
    }
]

# 仪表盘页面
if page == "仪表盘":
    st.title("AetherOps 仪表盘")
    
    # 关键指标展示
    col1, col2, col3, col4 = st.columns(4)
    metrics = generate_metrics()
    
    with col1:
        st.metric("系统健康度", f"{metrics['系统健康度']}%")
    with col2:
        st.metric("部署成功率", f"{metrics['部署成功率']}%")
    with col3:
        st.metric("平均响应时间", f"{metrics['平均响应时间']}ms")
    with col4:
        st.metric("AI修复成功率", f"{metrics['AI修复成功率']}%")
    
    # 部署趋势图
    st.subheader("部署趋势")
    df = generate_deployment_data()
    fig = px.line(df, x='date', y='deployments', title='每日部署数量')
    st.plotly_chart(fig, use_container_width=True)
    
    # 最近告警
    st.subheader("最近告警")
    alerts = [
        {"时间": "2024-03-15 10:30", "级别": "警告", "描述": "数据库连接池接近上限"},
        {"时间": "2024-03-15 09:15", "级别": "错误", "描述": "API服务响应超时"},
        {"时间": "2024-03-14 23:45", "级别": "信息", "描述": "系统更新完成"}
    ]
    st.table(pd.DataFrame(alerts))

# 智能部署页面
elif page == "智能部署":
    st.title("智能部署引擎")
    
    # 部署配置
    st.subheader("部署配置")
    col1, col2 = st.columns(2)
    with col1:
        env = st.selectbox("目标环境", ["生产环境", "预发环境", "测试环境"])
        branch = st.text_input("代码分支", "main")
    with col2:
        deploy_type = st.selectbox("部署类型", ["全量部署", "灰度发布", "金丝雀发布"])
        auto_rollback = st.checkbox("失败自动回滚", value=True)
    
    # AI部署建议
    st.subheader("AI部署建议")
    st.info("""
    AI分析结果：
    1. 检测到数据库schema变更，建议先执行数据库迁移
    2. 发现3个依赖包版本更新，建议更新依赖
    3. 配置文件有变更，需要更新环境变量
    """)
    
    if st.button("开始部署", type="primary"):
        with st.spinner("部署中..."):
            st.success("部署成功！")
            st.balloons()

# 系统监控页面
elif page == "系统监控":
    st.title("AI系统监控")
    
    # 实时监控指标
    st.subheader("实时监控指标")
    metrics = {
        "CPU使用率": random.randint(20, 80),
        "内存使用率": random.randint(30, 90),
        "磁盘使用率": random.randint(40, 85),
        "网络流量": random.randint(100, 1000)
    }
    
    # 创建仪表盘
    cols = st.columns(4)
    for i, (metric, value) in enumerate(metrics.items()):
        with cols[i]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': metric},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 80], 'color': "gray"},
                           {'range': [80, 100], 'color': "darkgray"}
                       ]}))
            st.plotly_chart(fig, use_container_width=True)
    
    # 异常检测结果
    st.subheader("AI异常检测")
    st.warning("""
    检测到潜在风险：
    1. 数据库连接池使用率持续上升
    2. API服务响应时间波动
    3. 内存使用率增长趋势异常
    """)

# AI修复中心页面
elif page == "AI修复中心":
    st.title("AI修复中心")

    # 添加修复过程按钮
    repair_url = "http://10.81.204.55:7777/chat/?scene=chat_agent&id=9b1c7f78-476c-11f0-94f9-2b96f16f267c"
    st.markdown(f'<a href="{repair_url}" target="_blank" class="repair-process-btn">进入修复过程</a>', unsafe_allow_html=True)

    # 添加日志分析部分
    st.markdown('<div class="repair-section-title">日志分析</div>', unsafe_allow_html=True)
    
    # 日志文件选择
    log_file = "core/data/k8s-volcano-controller.log"
    
    # 只保留日志预览和AI分析卡片，不再用两列布局
    st.markdown("""
    <style>
    .log-preview {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e7ef;
        max-height: 400px;
        overflow-y: auto;
        margin-bottom: 20px;
    }
    .analysis-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e7ef;
    }
    </style>
    """, unsafe_allow_html=True)

    # 日志预览卡片
    st.markdown('<div class="log-preview">', unsafe_allow_html=True)
    st.subheader("日志预览")
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            last_lines = log_content.split('\n')[-100:]
            st.text_area("日志内容", '\n'.join(last_lines), height=300)
    except Exception as e:
        st.error(f"无法读取日志文件: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

    # AI分析卡片
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.subheader("AI分析")
    api_key = st.text_input("DashScope API Key", type="password")
    if st.button("开始分析", use_container_width=True):
        if not api_key:
            st.error("请输入DashScope API Key")
        else:
            progress_placeholder = st.empty()
            markdown_placeholder = st.empty()
            markdown_blocks = []
            with st.spinner("正在分析日志..."):
                try:
                    from core.plans.qwen_log_analyzer import analyze_logs_stream
                    for step_result in analyze_logs_stream(log_file, api_key):
                        step = step_result.get('step')
                        data = step_result.get('data')
                        # 直接渲染AI真实分析内容
                        if step in ['markdown', 'llm_output']:
                            markdown_blocks.append(data)
                            markdown_placeholder.markdown("\n\n".join(markdown_blocks), unsafe_allow_html=True)
                        elif step == 'error':
                            progress_placeholder.error(f"分析过程中发生错误: {data}")
                except Exception as e:
                    if "WebSocketClosedError" not in str(e):
                        progress_placeholder.error(f"分析过程中发生错误: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# 环境管理页面
elif page == "环境管理":
    st.title("环境管理")
    
    # 环境状态
    st.subheader("环境状态")
    environments = {
        "生产环境": {"状态": "正常", "版本": "v1.2.3", "最后更新": "2024-03-15"},
        "预发环境": {"状态": "维护中", "版本": "v1.2.3-rc1", "最后更新": "2024-03-14"},
        "测试环境": {"状态": "正常", "版本": "v1.2.2", "最后更新": "2024-03-13"}
    }
    
    for env, info in environments.items():
        with st.expander(env):
            st.write(f"状态: {info['状态']}")
            st.write(f"版本: {info['版本']}")
            st.write(f"最后更新: {info['最后更新']}")
            
            if st.button(f"重建{env}", key=env):
                st.info(f"正在重建{env}...")
                st.success(f"{env}重建完成！")

# 知识库页面
elif page == "知识库":
    st.title("AI知识库")
    
    # 搜索框
    query = st.text_input("搜索运维知识", "如何优化数据库性能？")
    
    if st.button("搜索", type="primary"):
        st.subheader("AI回答")
        st.info("""
        数据库性能优化建议：
        1. 优化索引设计
        2. 合理设置连接池大小
        3. 使用查询缓存
        4. 定期维护和优化
        5. 监控慢查询
        """)
    
    # 知识库管理
    st.subheader("知识库管理")
    if st.button("上传文档"):
        st.info("支持上传PDF、Word、Markdown等格式的文档")

# 运维工具页面
elif page == "运维工具":
    import ops_tools
    # 直接调用ops_tools.py的内容（Streamlit会自动渲染）
