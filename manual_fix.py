import json
import os
import sys
from pathlib import Path

# 配置：必须与主程序保持一致
OUTPUT_FOLDER = "./markdown_output"

def input_safe(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

def main():
    print("🛠️  PPT2MD 视觉失败手动补救工具")
    print("=" * 40)
    
    # 1. 扫描已有的输出目录
    root = Path(OUTPUT_FOLDER)
    if not root.exists():
        print(f"❌ 目录 {OUTPUT_FOLDER} 不存在，请先运行主程序。")
        return

    ppt_dirs = [d for d in root.iterdir() if d.is_dir()]
    if not ppt_dirs:
        print("❌ 没有找到任何 PPT 输出文件夹。")
        return

    print(f"📂 在 {OUTPUT_FOLDER} 发现了以下项目：")
    ppt_map = {}
    for i, p in enumerate(ppt_dirs):
        print(f"  [{i+1}] {p.name}")
        ppt_map[str(i+1)] = p

    # 2. 选择项目
    choice = input_safe("\n👉 请选择要补救的 PPT 编号: ")
    if choice not in ppt_map:
        print("❌ 无效编号")
        return
    
    target_ppt = ppt_map[choice]
    temp_dir = target_ppt / "temp_raw_vision"
    
    # 确保临时目录存在（主程序运行过肯定有，除非被删了）
    if not temp_dir.exists():
        os.makedirs(temp_dir)

    while True:
        # 3. 输入失败的页码
        print("-" * 40)
        page_str = input_safe(f"📄 请输入失败的页码 (例如 166，输入 q 退出): ")
        if page_str.lower() == 'q':
            break
        
        if not page_str.isdigit():
            print("❌ 页码必须是数字")
            continue
            
        page_num = int(page_str)
        json_filename = f"Raw_{page_num:02d}.json"
        json_path = temp_dir / json_filename

        # 4. 检查是否已存在
        if json_path.exists():
            print(f"⚠️  文件 {json_filename} 已存在。覆盖它？(y/n)")
            if input_safe("> ").lower() != 'y':
                continue

        # 5. 输入人工替代文本
        print("\n📝 请输入这一页的替代文本 (可以直接回车，使用默认占位符):")
        print("   (提示：你可以打开那张图片，手动把里面的字打进去，或者只写个标题)")
        manual_text = input_safe("> ")
        
        if not manual_text:
            manual_text = f"[人工补救] 该页面 (P{page_num}) 原图触发了 API 风控拦截，已手动跳过视觉识别。"

        # 6. 构造数据结构（模拟 Step 1 的成功返回）
        fake_data = {
            "success": True,
            "slide_no": page_num,
            "raw_text": manual_text,
            "manual_fix": True  # 标记一下这是人工修的
        }

        # 7. 写入文件
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(fake_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已生成补救文件: {json_path}")
            print(f"🚀 现在你可以重新运行主程序 ppt2md.py，它会自动跳过 P{page_num} 的 API 调用！")
        except Exception as e:
            print(f"❌ 写入失败: {e}")

if __name__ == "__main__":
    main()