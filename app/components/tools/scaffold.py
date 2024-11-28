import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QStackedWidget,
    QHBoxLayout, QMessageBox, QRadioButton, QButtonGroup, QLabel
)
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, LineEdit, TextEdit, PushButton,
    MessageBox
)
from app.components.utils.scaffold import (
    confirm_details, create_cmakelists, create_header, create_source,
    create_package_json, create_readme, create_gitignore,
    create_component_main, create_component_hpp, create_component_cpp
)
from app.model.custom_messagebox import CustomMessageBox


@dataclass
class ModuleDetails:
    module_name: str = ""
    component_name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "GPL-3.0-or-later"
    repo_url: str = ""
    cpp_standard: str = "20"
    additional_sources: List[str] = field(default_factory=list)
    additional_headers: List[str] = field(default_factory=list)


class ScaffoldApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("模块脚手架生成器")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()

        self.module_details = ModuleDetails()
        self.setup_mode: str = "step"  # 'step' or 'complete'

        self.create_intro_page()
        self.create_form_pages()

        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)

    def create_intro_page(self):
        intro_page = QWidget()
        intro_layout = QVBoxLayout()

        intro_label = TitleLabel(
            "欢迎使用模块脚手架生成器。\n请选择设置方式并点击‘下一步’开始。")
        intro_layout.addWidget(intro_label)

        # 设置方式选择
        mode_layout = QHBoxLayout()
        self.step_radio = QRadioButton("逐步设置")
        self.step_radio.setChecked(True)
        self.complete_radio = QRadioButton("一次性完整设置")
        mode_layout.addWidget(self.step_radio)
        mode_layout.addWidget(self.complete_radio)
        intro_layout.addLayout(mode_layout)

        self.next_button = PushButton("下一步")
        self.next_button.clicked.connect(self.set_mode_and_next)
        intro_layout.addWidget(self.next_button)

        intro_page.setLayout(intro_layout)
        self.stacked_widget.addWidget(intro_page)

    def set_mode_and_next(self):
        if self.step_radio.isChecked():
            self.setup_mode = "step"
        else:
            self.setup_mode = "complete"
        self.show_next_page()

    def create_form_pages(self):
        self.pages = []
        fields = [
            ("模块名称 (例如 atom.utils):", "module_name"),
            ("组件名称 (例如 SystemComponent):", "component_name"),
            ("版本 (例如 1.0.0):", "version"),
            ("描述:", "description"),
            ("作者:", "author"),
            ("许可证 (例如 GPL-3.0-or-later):", "license"),
            ("仓库 URL (例如 https://github.com/ElementAstro/Lithium):", "repo_url"),
            ("C++ 标准 (例如 20):", "cpp_standard"),
            ("额外的源文件 (用逗号分隔, 例如 utils.cpp,math.cpp):", "additional_sources"),
            ("额外的头文件 (用逗号分隔, 例如 utils.hpp,math.hpp):", "additional_headers")
        ]

        if self.setup_mode == "complete":
            page = QWidget()
            layout = QVBoxLayout()
            form_layout = QFormLayout()
            for label_text, key in fields:
                label = SubtitleLabel(label_text)
                input_widget = LineEdit() if key != "description" else TextEdit()
                setattr(self, f"{key}_input", input_widget)
                form_layout.addRow(label, input_widget)
            layout.addLayout(form_layout)

            button_layout = QHBoxLayout()
            confirm_button = PushButton("确认")
            confirm_button.clicked.connect(self.confirm_details)
            layout.addLayout(button_layout)
            layout.addWidget(confirm_button)
            page.setLayout(layout)
            self.stacked_widget.addWidget(page)
            self.pages.append((page, None, None))
        else:
            for label_text, key in fields:
                page = QWidget()
                layout = QVBoxLayout()
                form_layout = QFormLayout()
                label = SubtitleLabel(label_text)
                input_widget = LineEdit() if key != "description" else TextEdit()
                setattr(self, f"{key}_input", input_widget)
                form_layout.addRow(label, input_widget)
                layout.addLayout(form_layout)

                button_layout = QHBoxLayout()
                if key != "module_name":
                    back_button = PushButton("上一步")
                    back_button.clicked.connect(self.show_previous_page)
                    button_layout.addWidget(back_button)

                next_button = PushButton("下一步")
                next_button.clicked.connect(self.show_next_page)
                button_layout.addWidget(next_button)
                layout.addLayout(button_layout)
                page.setLayout(layout)
                self.stacked_widget.addWidget(page)
                self.pages.append((page, input_widget, key))

        # 摘要页面
        self.summary_page = QWidget()
        summary_layout = QVBoxLayout()
        self.summary_label = TextEdit()
        self.summary_label.setReadOnly(True)
        summary_layout.addWidget(SubtitleLabel("模块详情预览"))
        summary_layout.addWidget(self.summary_label)

        button_layout = QHBoxLayout()
        self.copy_button = PushButton("复制到剪贴板")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.confirm_button = PushButton("确认并生成")
        self.confirm_button.clicked.connect(self.confirm_details)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.confirm_button)
        summary_layout.addLayout(button_layout)
        self.summary_page.setLayout(summary_layout)
        self.stacked_widget.addWidget(self.summary_page)

    def show_next_page(self):
        current_index = self.stacked_widget.currentIndex()
        if self.setup_mode == "step":
            if current_index < len(self.pages):
                page, input_widget, key = self.pages[current_index]
                if key:
                    value = input_widget.toPlainText() if key == "description" else input_widget.text()
                    setattr(self.module_details, key, value.strip())
                if key == "cpp_standard" and not getattr(self.module_details, key):
                    setattr(self.module_details, key, "20")
                self.stacked_widget.setCurrentIndex(current_index + 1)
        else:
            # 完整设置模式，直接跳转到摘要页面
            self.collect_all_inputs()
            self.show_summary()

    def collect_all_inputs(self):
        methods = [
            "module_name",
            "component_name",
            "version",
            "description",
            "author",
            "license",
            "repo_url",
            "cpp_standard",
            "additional_sources",
            "additional_headers"
        ]
        for key in methods:
            input_widget = getattr(self, f"{key}_input")
            value = input_widget.toPlainText() if key == "description" else input_widget.text()
            setattr(self.module_details, key, value.strip())
        if not self.module_details.cpp_standard:
            self.module_details.cpp_standard = "20"

    def show_summary(self):
        details = self.module_details.__dict__.copy()
        details['additional_sources'] = ', '.join(details['additional_sources'])
        details['additional_headers'] = ', '.join(details['additional_headers'])
        formatted_details = json.dumps(details, indent=4, ensure_ascii=False)
        self.summary_label.setText(formatted_details)
        self.stacked_widget.setCurrentIndex(self.stacked_widget.count() - 1)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.summary_label.toPlainText())
        MessageBox.information(self, "已复制", "模块详情已复制到剪贴板。").exec()

    def show_previous_page(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    def confirm_details(self):
        if self.setup_mode == "step":
            # 在逐步设置模式下，可能需要在最后一步收集所有输入
            if self.stacked_widget.currentIndex() != len(self.pages):
                return
        else:
            self.collect_all_inputs()
        confirmed, _ = confirm_details(self.module_details.__dict__)
        if not confirmed:
            CustomMessageBox.warning(
                self, "警告", "请检查您的输入并重试。")
            self.stacked_widget.setCurrentIndex(0)
            return

        try:
            module_dir = Path.cwd() / self.module_details.module_name
            src_dir = module_dir / "src"
            include_dir = module_dir / "include"
            src_dir.mkdir(parents=True, exist_ok=True)
            include_dir.mkdir(parents=True, exist_ok=True)

            base_name = self.module_details.module_name.split('.')[-1]

            (module_dir / f"{base_name}.cpp").write_text(
                create_component_cpp(
                    self.module_details.author,
                    self.module_details.description,
                    self.module_details.module_name,
                    self.module_details.component_name
                ),
                encoding='utf-8'
            )

            (module_dir / f"{base_name}.hpp").write_text(
                create_component_hpp(
                    self.module_details.author,
                    self.module_details.description,
                    self.module_details.module_name,
                    self.module_details.component_name
                ),
                encoding='utf-8'
            )

            (module_dir / 'CMakeLists.txt').write_text(
                create_cmakelists(
                    self.module_details.module_name,
                    self.module_details.cpp_standard,
                    self.module_details.additional_sources,
                    self.module_details.additional_headers
                ),
                encoding='utf-8'
            )

            (include_dir / f'{base_name}.hpp').write_text(
                create_header(self.module_details.module_name),
                encoding='utf-8'
            )

            (src_dir / f'{base_name}.cpp').write_text(
                create_source(self.module_details.module_name),
                encoding='utf-8'
            )

            for src in filter(None, self.module_details.additional_sources.split(',')):
                (src_dir / src.strip()).write_text("// {}\n".format(src.strip()), encoding='utf-8')

            for hdr in filter(None, self.module_details.additional_headers.split(',')):
                (include_dir / hdr.strip()).write_text("// {}\n".format(hdr.strip()), encoding='utf-8')

            (module_dir / 'package.json').write_text(
                create_package_json(
                    self.module_details.module_name,
                    self.module_details.version,
                    self.module_details.description,
                    self.module_details.author,
                    self.module_details.license,
                    self.module_details.repo_url
                ),
                encoding='utf-8'
            )

            (module_dir / 'README.md').write_text(
                create_readme(
                    self.module_details.module_name,
                    self.module_details.description,
                    self.module_details.author,
                    self.module_details.version
                ),
                encoding='utf-8'
            )

            (module_dir / '.gitignore').write_text(
                create_gitignore(),
                encoding='utf-8'
            )

            CustomMessageBox.information(
                self,
                "成功",
                f"模块 {self.module_details.module_name} 已成功创建在 {module_dir}"
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建模块时发生错误: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScaffoldApp()
    window.show()
    sys.exit(app.exec())