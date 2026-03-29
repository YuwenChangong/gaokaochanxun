import os


def batch_rename():
    # 获取当前文件夹下所有 pdf 文件
    folder_path = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    if not files:
        print("文件夹里没有 PDF 文件！")
        return

    print(f"找到 {len(files)} 个 PDF 文件，准备重命名...")

    for i, filename in enumerate(files):
        # 构造新名字，例如 data_1.pdf, data_2.pdf
        new_name = f"data_{i + 1}.pdf"

        # 执行重命名
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_name)

        os.rename(old_file, new_file)
        print(f"已改名: {filename} -> {new_name}")

    print("\n✅ 全部重命名完成！")


if __name__ == "__main__":
    batch_rename()