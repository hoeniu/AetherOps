# AetherOps 智能 DevOps 平台

AetherOps 是面向中大型企业和技术团队的 AI 驱动 DevOps 平台，助力提升系统稳定性与运维效率。

## 产品定位
- 面向互联网、SaaS、金融、制造、能源等行业的 DevOps 团队
- 以 AI 赋能的智能部署、监控、修复与知识增强

## 核心功能
- 智能部署引擎：自动化多环境部署，支持 Docker/Kubernetes
- AI 系统监控：异常检测、根因分析、智能告警
- AI 修复中心：自动化修复建议与自愈能力
- 知识增强：支持企业自定义知识库，持续学习优化
- 多平台代码仓库集成：GitHub、GitLab、Coding

## 安装说明
1. 克隆仓库：
```bash
git clone [repository_url]
cd [repository_name]
```
2. 安装依赖：
```bash
pip install -r requirements.txt
```
3. 配置环境变量：
```bash
cp .env.example .env
```
编辑 `.env` 文件，填入相应配置信息。

## 使用方法
1. 启动应用：
```bash
streamlit run app.py
```
2. 浏览器访问 `http://localhost:8501`

## 环境要求
- Python 3.9+
- Docker
- Kubernetes (可选)
- Jenkins (可选)

## 配置说明
- `GITHUB_TOKEN`: GitHub 个人访问令牌
- `OPENAI_API_KEY`: OpenAI API 密钥
- `JENKINS_URL`: Jenkins 服务器地址
- `JENKINS_USERNAME`: Jenkins 用户名
- `JENKINS_TOKEN`: Jenkins API 令牌 