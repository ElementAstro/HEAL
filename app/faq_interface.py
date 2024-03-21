import sys
import json
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QStackedWidget,
    QLabel
)
from app.component.setting_group import SettingCardGroup
from app.component.style_sheet import StyleSheet
from qfluentwidgets import PrimaryPushButton, LineEdit, TextEdit, SubtitleLabel, ScrollArea, PlainTextEdit, MessageBox, TitleLabel, Pivot, qrouter
from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase

class AddFAQDialog(QDialog):
    accepted = Signal()
    rejected = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add New FAQ")
        layout = QVBoxLayout(self)

        self.category_line = LineEdit()
        self.category_line.setPlaceholderText("Category")
        layout.addWidget(self.category_line)

        self.description_line = LineEdit()
        self.description_line.setPlaceholderText("Description")
        layout.addWidget(self.description_line)

        self.difficulty_line = LineEdit()
        self.difficulty_line.setPlaceholderText("Difficulty")
        layout.addWidget(self.difficulty_line)

        self.question_line = LineEdit()
        self.question_line.setPlaceholderText("Question")
        layout.addWidget(self.question_line)

        solutions_label = SubtitleLabel("Solutions:")
        layout.addWidget(solutions_label)

        self.solutions_text = TextEdit()
        layout.addWidget(self.solutions_text)

        links_label = SubtitleLabel("Links:")
        layout.addWidget(links_label)

        self.links_text = TextEdit()
        layout.addWidget(self.links_text)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class FAQ(ScrollArea):
    Nav = Pivot
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text.replace(' ', '-'))
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        self.FAQInterface = SettingCardGroup(self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)    # 必须设置！！！

        # 使用qss设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        #self.__connectSignalToSlot()

    def __initLayout(self):
        self.faq_data = [
            {
                "category": "Language",
                "description": "C++ is a general-purpose programming language.",
                "difficulty": 2,
                "links": [
                    "https://www.cplusplus.com/",
                    "https://en.cppreference.com/"
                ],
                "question": "What is C++?",
                "solutions": [
                    "Study C++ programming books",
                    "Take online tutorials"
                ]
            },
            {
                "category": "Language",
                "description": "You can declare a variable using the syntax: type name;",
                "difficulty": 1,
                "links": [
                    "https://www.geeksforgeeks.org/variables-cpp/"
                ],
                "question": "How to declare a variable in C++?",
                "solutions": [
                    "int x;",
                    "float y = 3.14;"
                ]
            }
        ]
        self.favorite_faqs = []

        #self.setWindowTitle("FAQ Viewer")
        self.FAQInterface.layout = QVBoxLayout(self.FAQInterface)

        self.FAQInterface.search_box = LineEdit()
        self.FAQInterface.search_box.setPlaceholderText("Search FAQ")
        self.FAQInterface.search_box.textChanged.connect(self.filter_faqs)
        self.FAQInterface.layout.addWidget(self.FAQInterface.search_box)

        self.FAQInterface.scroll_area = ScrollArea()
        self.FAQInterface.scroll_area.setWidgetResizable(True)
        self.FAQInterface.scroll_area_content = QWidget()
        self.FAQInterface.scroll_area_layout = QVBoxLayout(self.FAQInterface.scroll_area_content)
        self.FAQInterface.scroll_area.setWidget(self.FAQInterface.scroll_area_content)
        self.FAQInterface.layout.addWidget(self.FAQInterface.scroll_area)

        self.current_faqs = self.faq_data
        self.show_faqs()

        self.FAQInterface.export_button = PrimaryPushButton("Export FAQs")
        self.FAQInterface.export_button.clicked.connect(self.export_faqs)
        self.FAQInterface.layout.addWidget(self.FAQInterface.export_button)

        self.FAQInterface.import_button = PrimaryPushButton("Import FAQs")
        self.FAQInterface.import_button.clicked.connect(self.import_faqs)
        self.FAQInterface.layout.addWidget(self.FAQInterface.import_button)

        self.FAQInterface.add_button = PrimaryPushButton("Add FAQ")
        self.FAQInterface.add_button.clicked.connect(self.add_faq)
        self.FAQInterface.layout.addWidget(self.FAQInterface.add_button)

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.FAQInterface)
        self.pivot.setCurrentItem(self.FAQInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.FAQInterface.objectName())

        #self.vBoxLayout.addWidget(self.openEditorButton)
        #self.openEditorButton.clicked.connect(self.open_json_editor)

    #def __connectSignalToSlot(self):
        #self.faq.clicked.connect(lambda: self.open_file('config/config.json'))
        #self.personalConfigCard.clicked.connect(lambda: self.open_file('config/auto.json'))
        #self.bannersConfigCard.clicked.connect(lambda: self.open_file('server/lunarcore/data/banners.json'))

    def addSubInterface(self, widget: QLabel, objectName, text, icon=None):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def show_faqs(self):
        for faq in self.current_faqs:
            faq_widget = QWidget()
            faq_layout = QVBoxLayout(faq_widget)

            question_label = TitleLabel(f"Question: {faq['question']}")
            faq_layout.addWidget(question_label)

            description_label = SubtitleLabel(f"Description: {faq['description']}")
            faq_layout.addWidget(description_label)

            solutions_label = SubtitleLabel("Solutions:")
            faq_layout.addWidget(solutions_label)

            solutions_text = PlainTextEdit()
            solutions_text.setPlainText("\n".join(faq["solutions"]))
            solutions_text.setDisabled(True)
            faq_layout.addWidget(solutions_text)

            links_label = SubtitleLabel("Links:")
            faq_layout.addWidget(links_label)

            links_text = PlainTextEdit()
            links_text.setPlainText("\n".join(faq["links"]))
            links_text.setDisabled(True)
            faq_layout.addWidget(links_text)

            favorite_button = PrimaryPushButton("Favorite")
            favorite_button.clicked.connect(lambda _, faq=faq: self.toggle_favorite(faq))
            faq_layout.addWidget(favorite_button)

            self.FAQInterface.scroll_area_layout.addWidget(faq_widget)

    def filter_faqs(self):
        search_text = self.search_box.text().lower()
        if not search_text:
            self.current_faqs = self.faq_data
        else:
            self.current_faqs = [faq for faq in self.faq_data if search_text in faq['question'].lower() or any(search_text in solution.lower() for solution in faq['solutions'])]

        self.clear_scroll_area()
        self.show_faqs()

    def clear_scroll_area(self):
        for i in reversed(range(self.scroll_area_layout.count())):
            widget = self.scroll_area_layout.itemAt(i).widget()
            widget.setParent(None)

    def toggle_favorite(self, faq):
        if faq in self.favorite_faqs:
            self.favorite_faqs.remove(faq)
        else:
            self.favorite_faqs.append(faq)

    def export_faqs(self):
        with open("exported_faqs.json", "w") as f:
            json.dump(self.favorite_faqs, f, indent=4)
        MessageBox("Export Successful", "FAQs exported successfully.", self).show()

    def import_faqs(self):
        try:
            with open("imported_faqs.json", "r") as f:
                imported_faqs = json.load(f)
                self.favorite_faqs.extend(imported_faqs)
                MessageBox("Import Successful", "FAQs imported successfully.", self).show()
        except Exception as e:
            MessageBox("Import Error", f"Error importing FAQs: {str(e)}" , self).show()

    def add_faq(self):
        dialog = AddFAQDialog()
        if dialog.exec() == AddFAQDialog.Accepted:
            new_faq = {
                "category": dialog.category_line.text(),
                "description": dialog.description_line.text(),
                "difficulty": int(dialog.difficulty_line.text()),
                "question": dialog.question_line.text(),
                "solutions": dialog.solutions_text.toPlainText().split("\n"),
                "links": dialog.links_text.toPlainText().split("\n")
            }
            self.faq_data.append(new_faq)
            MessageBox("FAQ Added", "New FAQ added successfully.", self).show()
            self.filter_faqs()

if __name__ == "__main__":
    app = QApplication([])

    faq_data = [
        {
            "category": "Language",
            "description": "C++ is a general-purpose programming language.",
            "difficulty": 2,
            "links": [
                "https://www.cplusplus.com/",
                "https://en.cppreference.com/"
            ],
            "question": "What is C++?",
            "solutions": [
                "Study C++ programming books",
                "Take online tutorials"
            ]
        },
        {
            "category": "Language",
            "description": "You can declare a variable using the syntax: type name;",
            "difficulty": 1,
            "links": [
                "https://www.geeksforgeeks.org/variables-cpp/"
            ],
            "question": "How to declare a variable in C++?",
            "solutions": [
                "int x;",
                "float y = 3.14;"
            ]
        }
    ]

    faq_viewer = FAQ(faq_data)
    faq_viewer.show()

    sys.exit(app.exec())
