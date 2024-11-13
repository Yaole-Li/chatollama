import sys
from PyQt6.QtWidgets import QApplication
from chat_ui import ChatWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = ChatWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
