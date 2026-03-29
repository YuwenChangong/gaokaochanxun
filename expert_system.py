import os
import pandas as pd


class GaokaoEngine:
    def __init__(self, csv_name="gaokao_db.csv"):
        # 【关键：自动获取当前脚本所在的真实文件夹路径】
        base_path = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_path, csv_name)

        print(f"正在尝试从以下位置加载数据: {csv_path}")  # 调试信息

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"找不到数据库！请确保 {csv_name} 就在代码旁边。\n当前检测路径: {csv_path}")

        self.df = pd.read_csv(csv_path)
        # ... 后面保持不变 ...

    def match(self, user_rank, user_subs):
        # 1. 2026 选科过滤
        def filter_subs(req, u_subs):
            if pd.isna(req) or req == "不限": return True
            return all(s in u_subs for s in req.split(","))

        df_filtered = self.df[self.df['subject_req'].apply(lambda x: filter_subs(x, user_subs))].copy()

        # 2. 冲稳保算法 (修正系数：理科物化生位次 * 1.15, 文科 * 0.9)
        if "物理" in user_subs and "化学" in user_subs:
            adj_rank = user_rank * 1.15
        else:
            adj_rank = user_rank * 0.9

        # 划分区间
        df_filtered['type'] = '保一保'
        df_filtered.loc[df_filtered['min_rank'] < adj_rank * 0.95, 'type'] = '冲一冲'
        df_filtered.loc[(df_filtered['min_rank'] >= adj_rank * 0.95) & (df_filtered['min_rank'] <= adj_rank * 1.1), 'type'] = '稳一稳'

        # 3. 关联行业点评
        def get_advice(major):
            for key, val in self.market_advice.items():
                if key in major: return val
            return {"status": "未知", "note": "需结合当年政策细看"}

        advice_data = df_filtered['major'].apply(get_advice)
        df_filtered['行业状态'] = advice_data.apply(lambda x: x['status'])
        df_filtered['职业建议'] = advice_data.apply(lambda x: x['note'])

        return df_filtered.sort_values('min_rank')

# 运行逻辑
engine = GaokaoEngine()
res = engine.match(15000, ["物理", "化学"])
res.to_excel("你的专属志愿报告.xlsx", index=False)