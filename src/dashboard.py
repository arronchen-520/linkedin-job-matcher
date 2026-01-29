import streamlit as st
from supabase import create_client
import pandas as pd
import ast


# 配置页面
st.set_page_config(page_title="CareerCopilot", layout="wide")

# 初始化 Supabase 连接
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_API_KEY"])

supabase = init_connection()

st.title("🚀 CareerCopilot: 智能职位匹配看板")

# 侧边栏：用户信息与订阅
with st.sidebar:
    st.header("账户信息")
    st.info("当前用户: Test_User")
    st.write("订阅状态: **Premium**")
    if st.button("升级/续费"):
        st.write("跳转至支付页面...")

# 从数据库获取数据
def fetch_jobs():
    response = supabase.table("MATCH_OUTPUT").select("*").order("Match Score", desc=True).execute()
    return pd.DataFrame(response.data)

df = fetch_jobs()

# 主界面：展示数据
if not df.empty:
    st.subheader("根据你的简历分析出的高匹配职位")
    
    # 核心展示表格
    cols = ["Job Title", "Company", "Match Score", "Posted Ago", "Min Salary", "Max Salary"]
    edited_df = st.data_editor(df[cols], use_container_width=True)

    # 详细分析区块
    selected_job_title = st.selectbox("选择职位查看详细 AI 分析:", df["Job Title"] + " @ " + df["Company"])
    selected_job = df[df["Job Title"] + " @ " + df["Company"] == selected_job_title].iloc[0]
    
    # 创建三列布局
    col1, col2, col3 = st.columns([1, 1.5, 0.8]) # 调整比例，中间分析区给宽一点

    with col1:
        st.metric("匹配度分数", f"{selected_job['match_score']}%")
        st.write("**💡 AI 核心建议:**")
        # 使用 info 框让文字更有质感
        st.info(selected_job['reasoning'])

    with col2:
        st.write("**🛠️ 缺失技能 (需在面试/简历中补强):**")
        
        # 既然是 list，我们可以把它们渲染成漂亮的标签
        skills = selected_job['Missing Skills']
        skills = skills.split(', ')
        if isinstance(skills, list) and len(skills) > 0:
            # 这种方式会生成一排带有背景色的漂亮标签
            skills_html = "".join([f'<span style="background-color: #ff4b4b22; color: #ff4b4b; padding: 2px 8px; border-radius: 10px; margin-right: 5px; border: 1px solid #ff4b4b; font-size: 0.8rem;">{s}</span>' for s in skills])
            st.markdown(skills_html, unsafe_allow_html=True)
            
        # # 或者更简单的列表形式（带 Emoji）
        # st.write("") 
        # for skill in skills:
        #     st.write(f"⚠️ `{skill}`")
        else:
            st.success("根据 AI 分析，你完全匹配该职位的技能要求！")

    with col3:
        st.write("**🔗 快速操作:**")
        # 获取原始 URL
        job_url = selected_job.get('URL', 'https://www.linkedin.com')
        
        # 一个显眼的按钮直接跳转
        st.link_button("🌐 查看职位原帖", job_url, type="primary", use_container_width=True)
        
        # 你甚至可以加一个“已申请”的标记功能（如果你在数据库里加了 status 字段的话）
        if st.button("✅ 标记为已申请", use_container_width=True):
            st.toast("功能开发中... 之后可以更新数据库状态！")

else:
    st.warning("目前数据库中没有职位信息，请运行本地爬虫同步数据。")