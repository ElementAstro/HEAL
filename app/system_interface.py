import psutil
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,QWidget
from PySide6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, TableWidget, MessageDialog, MessageBox

class ProcessManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("进程管理器")
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout(self.centralWidget)

        self.process_table = TableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["进程ID", "名称", "状态", "CPU占用率", "内存占用"])
        self.layout.addWidget(self.process_table)

        self.refresh_button = PrimaryPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_processes)
        self.layout.addWidget(self.refresh_button)

        self.kill_button = PrimaryPushButton("结束进程")
        self.kill_button.clicked.connect(self.kill_process)
        self.layout.addWidget(self.kill_button)

        self.refresh_processes()

    def refresh_processes(self):
        self.process_table.setRowCount(0)
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info']):
            rowPosition = self.process_table.rowCount()
            self.process_table.insertRow(rowPosition)
            self.process_table.setItem(rowPosition, 0, QTableWidgetItem(str(proc.info['pid'])))
            self.process_table.setItem(rowPosition, 1, QTableWidgetItem(proc.info['name']))
            self.process_table.setItem(rowPosition, 2, QTableWidgetItem(proc.info['status']))
            self.process_table.setItem(rowPosition, 3, QTableWidgetItem(str(proc.info['cpu_percent'])))
            self.process_table.setItem(rowPosition, 4, QTableWidgetItem(str(proc.info['memory_info'].rss / (1024 * 1024))))

    def kill_process(self):
        selected_row = self.process_table.currentRow()
        if selected_row >= 0:
            pid_item = self.process_table.item(selected_row, 0)
            pid = int(pid_item.text())
            try:
                p = psutil.Process(pid)
                p.terminate()
                MessageBox("成功", f"进程 {pid} 已成功结束", self).show()
                self.refresh_processes()
            except psutil.NoSuchProcess:
                MessageBox("错误", f"进程 {pid} 不存在", self)
        else:
            MessageBox("错误", "请先选择要结束的进程", self)

if __name__ == "__main__":
    app = QApplication([])
    window = ProcessManager()
    window.showNormal()
    app.exec()
