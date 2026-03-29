import pdfplumber
import pandas as pd
import os


# --- 新增：专业组标签映射函数 ---
def get_major_description(school_name, group_code):
    group_str = str(group_code).strip()

    # 针对广东2024投档表的通用逻辑
    if group_str == '201':
        return "201组：理工类核心专业 (通常含计算机、电子、自动化、经管等)"
    elif group_str == '202':
        return "202组：文理兼收/社科类 (通常含法学、外国语、教育等)"
    elif group_str in ['203', '204']:
        return f"{group_str}组：特色/医学/实验班/地方专项"
    elif '中外合作' in school_name or '学费' in school_name:
        return f"{group_str}组：高收费/中外合作办学专业"
    else:
        # 如果是其他编码，保留原始编码并提示查阅目录
        return f"专业组:{group_str} (请在招生目录中核对具体方向)"


def parse_guangdong_pdf(pdf_path):
    all_data = []

    print(f"🔍 正在解析广东投档表: {os.path.basename(pdf_path)}...")

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            if table:
                start_index = 1 if i == 0 else 0
                for row in table[start_index:]:
                    if len(row) >= 7:
                        school_name = str(row[1]).strip()
                        group_code = str(row[2]).strip()

                        # --- 第一步：在这里调用翻译函数 ---
                        major_desc = get_major_description(school_name, group_code)

                        all_data.append({
                            "school": school_name,
                            "major": major_desc,  # 存入直观的描述
                            "year": "2024",
                            "min_rank": str(row[6]).strip(),
                            "subject_req": "物理+化学" if group_code == '201' else "见招生目录"
                        })
            if (i + 1) % 5 == 0:
                print(f"✅ 已处理 {i + 1} / {len(pdf.pages)} 页...")

    if all_data:
        df = pd.DataFrame(all_data)
        # 数据清洗逻辑保持不变
        df = df.replace(r'\n', '', regex=True)
        df['min_rank'] = pd.to_numeric(df['min_rank'].astype(str).str.replace(',', ''), errors='coerce')
        df = df.dropna(subset=['school', 'min_rank'])
        df['min_rank'] = df['min_rank'].astype(int)

        output_file = "gaokao_db.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"🎉 解析成功！共提取 {len(df)} 条有效投档数据，已保存至 {output_file}")
    else:
        print("❌ 未能从 PDF 中提取到有效表格数据。")


if __name__ == "__main__":
    files = [f for f in os.listdir('.') if f.endswith('.pdf') and f.startswith('W02')]
    if files:
        parse_guangdong_pdf(files[0])
    else:
        print("请确保 W020240722... 开头的 PDF 文件在当前文件夹内。")