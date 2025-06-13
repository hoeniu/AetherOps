import streamlit as st
import paramiko

st.title("运维工具 - SSH连接服务器")

st.markdown("""
<style>
.ssh-card {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(59,130,246,0.08);
    border: 1px solid #e0e7ef;
    max-width: 500px;
    margin-bottom: 30px;
}
.ssh-result {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 12px 16px;
    font-family: monospace;
    color: #334155;
    margin-top: 10px;
}
.ssh-btn {
    width: 100%;
    background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 100%);
    color: #fff;
    font-weight: bold;
    font-size: 18px;
    border: none;
    border-radius: 8px;
    padding: 12px 0;
    margin-top: 18px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: box-shadow 0.2s;
    box-shadow: 0 2px 8px rgba(59,130,246,0.08);
}
.ssh-btn:hover {
    box-shadow: 0 4px 16px rgba(59,130,246,0.18);
    opacity: 0.95;
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.get('ssh_connected'):
    with st.container():
        st.markdown('<div class="ssh-card">', unsafe_allow_html=True)
        st.subheader("服务器信息")
        host = st.text_input("主机地址", "127.0.0.1")
        port = st.number_input("端口", value=22, min_value=1, max_value=65535)
        username = st.text_input("用户名", "root")
        password = st.text_input("密码", type="password")
        # 兼容streamlit按钮逻辑
        if st.button("连接服务器", key="connect_btn", use_container_width=True):
            if not password:
                st.session_state['ssh_connected'] = False
                st.error("请填写密码")
            else:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(host, port=port, username=username, password=password, timeout=5)
                    st.success(f"成功连接到 {host}:{port}")
                    st.session_state['ssh_connected'] = True
                    st.session_state['ssh_info'] = {'host': host, 'port': port, 'username': username, 'password': password}
                    ssh.close()
                except Exception as e:
                    st.session_state['ssh_connected'] = False
                    st.error(f"连接失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    if st.button("断开连接", type="secondary", use_container_width=True):
        st.session_state['ssh_connected'] = False
        st.experimental_rerun()
    st.markdown('<div class="ssh-card">', unsafe_allow_html=True)
    st.subheader("远程命令执行")
    cmd = st.text_input("输入要执行的命令", "ls -l")
    if st.button("执行命令", key="exec_btn", use_container_width=True):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            info = st.session_state['ssh_info']
            ssh.connect(info['host'], port=info['port'], username=info['username'], password=info['password'], timeout=5)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result = stdout.read().decode() + stderr.read().decode()
            st.markdown(f'<div class="ssh-result">{result}</div>', unsafe_allow_html=True)
            ssh.close()
        except Exception as e:
            st.error(f"命令执行失败: {e}")
    st.markdown('</div>', unsafe_allow_html=True) 