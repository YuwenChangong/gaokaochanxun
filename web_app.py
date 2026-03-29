import streamlit as st
import pandas as pd
import os
import urllib.parse

# --- 页面基础配置 ---
st.set_page_config(page_title="2026 广东高考志愿智能预测系统", layout="wide")


# --- 1. 数据加载函数 (带缓存) ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_path, "gaokao_db.csv")

    if os.path.exists(csv_path):
        data = pd.read_csv(csv_path)
        # 强制转换位次为数字，剔除无法转换的行
        data['min_rank'] = pd.to_numeric(data['min_rank'], errors='coerce')
        return data.dropna(subset=['min_rank', 'school'])
    return None


# --- 2. 核心匹配与分析逻辑 ---
def match_logic(df, user_rank, user_subs):
    # A. 严格选科过滤逻辑
    def strict_filter(row_req, u_subs):
        row_req = str(row_req)
        # 如果要求为“不限”或空，直接通过
        if any(kw in row_req for kw in ["不限", "nan", "None", "无"]):
            return True

        # 核心校验：专业组要求的科目必须全部在用户的选科组合中
        target_subs = ["物理", "化学", "生物", "历史", "地理", "政治"]
        for s in target_subs:
            if s in row_req and s not in u_subs:
                return False
        return True

    # 执行过滤
    matched = df[df['subject_req'].apply(lambda x: strict_filter(x, user_subs))].copy()

    # B. 位次区间过滤：涵盖“冲、稳、保”三类学校（位次在用户 85% 到 250% 之间）
    matched = matched[(matched['min_rank'] >= user_rank * 0.85) & (matched['min_rank'] <= user_rank * 2.5)]

    # C. 专业档次与填报建议预测 (算法模型)
    def predict_details(row_rank, u_rank):
        margin = row_rank - u_rank  # 领先位次

        # 1. 填报建议分类
        if margin < -u_rank * 0.1:
            analysis = "🔥 冲一冲"
        elif -u_rank * 0.1 <= margin <= u_rank * 0.2:
            analysis = "💎 稳一稳"
        else:
            analysis = "✅ 保一保"

        # 2. 最好专业预测 (基于位次余量的逻辑推演)
        if margin > 10000:
            major_tier = "🥇 顶级王牌 (可稳选计算机/临床/实验班)"
        elif margin > 4000:
            major_tier = "🥈 核心热门 (可录法学/电子/经管等)"
        elif margin > 0:
            major_tier = "🥉 稳进专业 (建议避开组内最高分专业)"
        else:
            major_tier = "📈 压线入场 (建议服从调剂以保校名)"

        return analysis, major_tier

    # 批量应用预测逻辑
    analysis_results = matched['min_rank'].apply(lambda x: predict_details(x, user_rank))
    matched['填报建议'] = [x[0] for x in analysis_results]
    matched['可录最好专业预测'] = [x[1] for x in analysis_results]

    # 按位次升序排列（排在最前面的就是你能上的“最好学校”）
    return matched.sort_values('min_rank')


# --- 3. Web UI 界面构建 ---
st.title("🎓 2026 广东高考志愿智能预测系统")
st.markdown("---")

# 侧边栏：用户信息输入
st.sidebar.header("📋 个人信息录入")
u_rank = st.sidebar.number_input("您的全省排名 (位次)", min_value=1, value=15000, step=100)
all_subs = ["物理", "化学", "生物", "历史", "地理", "政治"]
u_subs = st.sidebar.multiselect("您的选科组合 (须选满3门)", all_subs, default=["物理", "化学", "生物"])

# 加载数据库
df = load_data()

if df is not None:
    if st.sidebar.button("🚀 生成最优方案"):
        # 强制校验：选科必须满3门
        if len(u_subs) < 3:
            st.error("❌ 政策错误：新高考模式下必须选择至少 3 门科目才能进行匹配。")
        else:
            results = match_logic(df, u_rank, u_subs)

            if results.empty:
                st.warning("⚠️ 未找到完全匹配的学校。建议尝试调整选科或放宽位次要求。")
            else:
                # 展示顶层概览看板
                st.success(f"✅ 分析完成！为您匹配到 {len(results)} 个符合条件的院校专业组。")

                m1, m2, m3 = st.columns(3)
                m1.metric("冲刺型 (挑战名校)", len(results[results['填报建议'] == "🔥 冲一冲"]))
                m2.metric("稳健型 (黄金推荐)", len(results[results['填报建议'] == "💎 稳一稳"]))
                m3.metric("保底型 (安全无忧)", len(results[results['填报建议'] == "✅ 保一保"]))

                st.markdown("### 📌 志愿推荐清单 (按学校档次由高到低)")
                st.caption("列表顶部为您的分数能触达的【最高层次大学】。")

                # 处理显示表格
                display_df = results.copy()


                # 构造搜索引擎直达链接
                def make_search_link(row):
                    q = f"2024 广东 {row['school']} {row['major']} 具体专业名单"
                    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(q)}"
                    return f'<a href="{url}" target="_blank">🔍 查看专业明细</a>'


                display_df['操作'] = display_df.apply(make_search_link, axis=1)

                # 定义展示的列名顺序
                output_columns = [
                    'school', 'min_rank', '可录最好专业预测', 'major', '填报建议', '操作'
                ]

                # 渲染 HTML 表格以支持点击链接
                st.write(
                    display_df[output_columns].to_html(escape=False, index=False),
                    unsafe_allow_html=True
                )

                # 提供数据下载
                st.markdown("---")
                csv_data = results.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📂 下载完整预测报告 (CSV)", data=csv_data, file_name=f"广东高考预测_{u_rank}.csv")
else:
    st.error("⚠️ 数据库缺失：请确保当前目录下存在 gaokao_db.csv 文件。")