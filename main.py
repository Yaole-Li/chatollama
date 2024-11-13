import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from chat_ui import ChatWindow
import os

class MenuBarApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
        # 创建系统托盘图标
        self.tray = QSystemTrayIcon()
        icon = QIcon(os.path.join(os.path.dirname(__file__), 'icon_inverted.png'))  # 需要添加一个图标文件
        self.tray.setIcon(icon)
        
        # 创建托盘菜单
        self.menu = QMenu()
        self.window = ChatWindow()
        
        # 添加菜单项
        show_action = QAction("显示/隐藏", self.menu)
        show_action.triggered.connect(self.toggle_window)
        
        quit_action = QAction("退出", self.menu)
        quit_action.triggered.connect(self.quit_app)
        
        self.menu.addAction(show_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)
        
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_activated)
        
        # 设置窗口标志
        self.window.setWindowFlags(
            self.window.windowFlags() |
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.WindowStaysOnTopHint   # 保持在顶层
        )
        
    def run(self):
        self.tray.show()
        return self.app.exec()
    
    def toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.show_window()
    
    def show_window(self):
        # 获取主屏幕
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # 获取菜单栏高度（macOS 通常是 22 像素）
        menu_bar_height = 22
        
        # 计算窗口位置 - 考虑到更宽的窗口
        window_x = screen_geometry.width() - self.window.width() - 50  # 距离右边 50 像素
        window_y = menu_bar_height + 5  # 距离顶部多留一点空间
        
        # 设置窗口位置
        self.window.move(window_x, window_y)
        self.window.show()
    
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击
            self.toggle_window()
    
    def quit_app(self):
        self.window.close()
        self.app.quit()

if __name__ == "__main__":
    app = MenuBarApp()
    sys.exit(app.run())
