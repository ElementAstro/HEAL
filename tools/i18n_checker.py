#!/usr/bin/env python3
"""
国际化检查工具
扫描项目中的翻译使用情况，检查缺失的翻译
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class I18nChecker:
    """国际化检查器"""
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.translations_dir = project_root / "src" / "data" / "translations"
        self.app_dir = project_root / "app"
        
        # 翻译键的正则表达式
        self.tr_patterns = [
            r'tr\(["\']([a-zA-Z][a-zA-Z0-9_\.]*)["\']',  # tr("key") - 必须以字母开头
            r't\(["\']([a-zA-Z][a-zA-Z0-9_\.]*)["\']',   # t("key") - 必须以字母开头
            r'self\.tr\(["\']([a-zA-Z][a-zA-Z0-9_\.]*)["\']',  # self.tr("key") - 必须以字母开头
        ]

        # 要忽略的键（通常是不需要翻译的内容）
        self.ignore_patterns = [
            r'^[0-9]+$',  # 纯数字
            r'^[^a-zA-Z]*$',  # 不包含字母的字符串
            r'^[a-zA-Z]$',  # 单个字母
            r'^\s*$',  # 空白字符
        ]
        
        self.found_keys: Set[str] = set()
        self.translation_files: Dict[str, Dict[str, str]] = {}
        
    def load_translation_files(self) -> None:
        """加载所有翻译文件"""
        print("加载翻译文件...")
        
        for file_path in self.translations_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.translation_files[file_path.stem] = self._flatten_dict(data)
                    print(f"  加载: {file_path.name} ({len(self.translation_files[file_path.stem])} 项)")
            except Exception as e:
                print(f"  错误: 无法加载 {file_path.name}: {e}")
                
    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
        
    def scan_python_files(self) -> None:
        """扫描Python文件中的翻译键"""
        print("扫描Python文件...")
        
        python_files = list(self.app_dir.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in self.tr_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # 检查是否应该忽略这个键
                        should_ignore = False
                        for ignore_pattern in self.ignore_patterns:
                            if re.match(ignore_pattern, match):
                                should_ignore = True
                                break

                        if not should_ignore and len(match) > 1:  # 忽略单字符键
                            self.found_keys.add(match)
                        
            except Exception as e:
                print(f"  错误: 无法读取 {file_path}: {e}")
                
        print(f"  找到 {len(self.found_keys)} 个翻译键")
        
    def check_missing_translations(self) -> Dict[str, List[str]]:
        """检查缺失的翻译"""
        print("检查缺失的翻译...")
        
        missing = defaultdict(list)
        
        for lang_code, translations in self.translation_files.items():
            for key in self.found_keys:
                if key not in translations:
                    missing[lang_code].append(key)
                    
        return dict(missing)
        
    def check_unused_translations(self) -> Dict[str, List[str]]:
        """检查未使用的翻译"""
        print("检查未使用的翻译...")
        
        unused = defaultdict(list)
        
        for lang_code, translations in self.translation_files.items():
            for key in translations.keys():
                if key not in self.found_keys:
                    unused[lang_code].append(key)
                    
        return dict(unused)
        
    def generate_missing_translations(self, missing: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
        """生成缺失翻译的模板"""
        templates = {}
        
        for lang_code, keys in missing.items():
            templates[lang_code] = {}
            for key in keys:
                # 使用键名作为默认翻译
                templates[lang_code][key] = f"[TODO: {key}]"
                
        return templates
        
    def save_missing_translations_template(self, templates: Dict[str, Dict[str, str]]) -> None:
        """保存缺失翻译的模板文件"""
        output_dir = self.project_root / "tools" / "i18n_missing"
        output_dir.mkdir(exist_ok=True)
        
        for lang_code, translations in templates.items():
            if translations:
                output_file = output_dir / f"missing_{lang_code}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                print(f"  保存缺失翻译模板: {output_file}")
                
    def generate_report(self) -> str:
        """生成检查报告"""
        missing = self.check_missing_translations()
        unused = self.check_unused_translations()
        
        report = []
        report.append("=" * 60)
        report.append("国际化检查报告")
        report.append("=" * 60)
        report.append("")
        
        # 统计信息
        report.append("统计信息:")
        report.append(f"  找到的翻译键: {len(self.found_keys)}")
        for lang_code, translations in self.translation_files.items():
            report.append(f"  {lang_code} 翻译项: {len(translations)}")
        report.append("")
        
        # 缺失的翻译
        report.append("缺失的翻译:")
        if any(missing.values()):
            for lang_code, keys in missing.items():
                if keys:
                    report.append(f"  {lang_code}: {len(keys)} 项")
                    for key in sorted(keys)[:10]:  # 只显示前10个
                        report.append(f"    - {key}")
                    if len(keys) > 10:
                        report.append(f"    ... 还有 {len(keys) - 10} 项")
        else:
            report.append("  无缺失翻译")
        report.append("")
        
        # 未使用的翻译
        report.append("未使用的翻译:")
        if any(unused.values()):
            for lang_code, keys in unused.items():
                if keys:
                    report.append(f"  {lang_code}: {len(keys)} 项")
                    for key in sorted(keys)[:10]:  # 只显示前10个
                        report.append(f"    - {key}")
                    if len(keys) > 10:
                        report.append(f"    ... 还有 {len(keys) - 10} 项")
        else:
            report.append("  无未使用翻译")
        report.append("")
        
        # 建议
        report.append("建议:")
        if any(missing.values()):
            report.append("  1. 添加缺失的翻译项")
            report.append("  2. 检查 tools/i18n_missing/ 目录下的模板文件")
        if any(unused.values()):
            report.append("  3. 考虑删除未使用的翻译项")
        if not any(missing.values()) and not any(unused.values()):
            report.append("  国际化状态良好！")
        
        return "\n".join(report)
        
    def run_check(self) -> None:
        """运行完整检查"""
        print("开始国际化检查...")
        print()
        
        self.load_translation_files()
        print()
        
        self.scan_python_files()
        print()
        
        missing = self.check_missing_translations()
        unused = self.check_unused_translations()
        print()
        
        # 生成并保存缺失翻译模板
        if any(missing.values()):
            templates = self.generate_missing_translations(missing)
            self.save_missing_translations_template(templates)
            print()
        
        # 生成报告
        report = self.generate_report()
        print(report)
        
        # 保存报告
        report_file = self.project_root / "tools" / "i18n_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")


def main() -> None:
    """主函数"""
    checker = I18nChecker(project_root)
    checker.run_check()


if __name__ == "__main__":
    main()
