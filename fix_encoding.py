# -*- coding: utf-8 -*-
"""
修复训练脚本中的特殊字符 - 解决 Windows GBK 编码问题
运行此脚本后重新训练模型即可
"""

import re

def fix_special_characters():
    """替换训练脚本中的特殊字符为 ASCII 安全字符"""
    
    input_file = r'd:\桌面\trae\001\ipso_bp_slope_stability.py'
    output_file = r'd:\桌面\trae\slope stability1\ipso_bp_slope_stability_fixed.py'
    
    # 特殊字符映射表
    replacements = {
        '✓': '[OK]',
        '✗': '[X]',
        '★': '[*]',
        '✔': '[OK]',
        '✖': '[X]',
        '⚠': '[!]',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '►': '>',
        '◄': '<',
        '●': '(o)',
        '○': '( )',
        '■': '[#]',
        '□': '[ ]',
        '◆': '[D]',
        '◇': '[d]',
        '△': '^',
        '▽': 'v',
        '☆': '*',
        '♦': '[+]',
        '↑': '(up)',
        '↓': '(down)',
    }
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for special_char, safe_char in replacements.items():
        content = content.replace(special_char, safe_char)
    
    if content != original_content:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] 已生成修复版本: {output_file}")
        print(f"[INFO] 替换了 {len(replacements)} 种特殊字符")
        print("")
        print("下一步操作:")
        print("  1. 使用修复后的脚本重新训练模型:")
        print(f"     python {output_file}")
        print("  2. 将生成的模型文件复制到 ipso_bp_model_output/ 目录")
        print("  3. 重启 Streamlit 应用")
        
        return True
    else:
        print("[INFO] 未发现需要替换的特殊字符")
        return False

if __name__ == '__main__':
    fix_special_characters()
