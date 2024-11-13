from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QComboBox, QLabel, QScrollArea, QListWidget, 
                            QListWidgetItem, QSplitter, QMenu, QTextBrowser, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize, QRegularExpression, QWaitCondition, QMutex
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QTextCharFormat, QSyntaxHighlighter, QTextOption
import sys
import ollama
import json
import os
from datetime import datetime
from markdown import markdown
import subprocess
from typing import List

class ModelManager:
    """模型管理类"""
    @staticmethod
    def get_local_models() -> List[str]:
        """获取本地已安装的模型列表"""
        try:
            # 执行 ollama list 命令
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                # 解析输出
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                models = []
                for line in lines:
                    if line.strip():
                        # 分割行并获取模型名称（第一列）
                        model_name = line.split()[0]
                        models.append(model_name)
                return models if models else ["llama3.2-vision:11b"]  # 如果没有找到模型，返回默认模型
            return ["llama3.2-vision:11b"]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return ["llama3.2-vision:11b"]

class Conversation:
    def __init__(self, id=None, title=None):
        self.id = id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.title = title or "新对话"
        self.messages = []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'messages': self.messages
        }

    @staticmethod
    def from_dict(data):
        conv = Conversation(data['id'], data['title'])
        conv.messages = data['messages']
        return conv

class ConversationList(QWidget):
    conversation_selected = pyqtSignal(Conversation)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # 新建对话按钮
        self.new_chat_btn = QPushButton("+ 新建对话")
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        layout.addWidget(self.new_chat_btn)
        
        # 对话列表
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                color: white;
                border-radius: 5px;
                padding: 8px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        layout.addWidget(self.list_widget)
        
        self.conversations = {}
        self.load_conversations()
        
    def add_conversation(self, conversation):
        """添加新对话到列表顶部"""
        self.conversations[conversation.id] = conversation
        # 在列表顶部插入新对话
        item = QListWidgetItem(conversation.title)
        item.setData(Qt.ItemDataRole.UserRole, conversation.id)
        self.list_widget.insertItem(0, item)
        # 选中新对话
        self.list_widget.setCurrentRow(0)
        self.save_conversations()
        
    def load_conversations(self):
        """加载对话历史，按时间倒序排序"""
        try:
            if os.path.exists('conversations.json'):
                with open('conversations.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 按照 id (时间戳) 排序，最新的在前
                    sorted_data = sorted(data, key=lambda x: x['id'], reverse=True)
                    for conv_data in sorted_data:
                        conv = Conversation.from_dict(conv_data)
                        self.conversations[conv.id] = conv
                        item = QListWidgetItem(conv.title)
                        item.setData(Qt.ItemDataRole.UserRole, conv.id)
                        self.list_widget.addItem(item)
        except Exception as e:
            print(f"加载对话历史失败: {e}")
            
    def save_conversations(self):
        """保存对话历史，保持时间顺序"""
        try:
            # 将对话列表转换为列表并按时间戳排序
            conversations_list = list(self.conversations.values())
            sorted_conversations = sorted(conversations_list, key=lambda x: x.id, reverse=True)
            data = [conv.to_dict() for conv in sorted_conversations]
            with open('conversations.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存对话历史失败: {e}")

    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("删除对话")
        action = menu.exec(self.list_widget.mapToGlobal(position))
        
        if action == delete_action:
            current_item = self.list_widget.currentItem()
            if current_item:
                conv_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.delete_conversation(conv_id)

    def delete_conversation(self, conv_id):
        """删除对话"""
        # 从字典中删除
        if conv_id in self.conversations:
            del self.conversations[conv_id]
        
        # 从列表控件中删除当前选中的项
        current_item = self.list_widget.currentItem()
        if current_item:
            self.list_widget.takeItem(self.list_widget.row(current_item))
        
        # 如果删除后没有对话了，创建一个新对话
        if self.list_widget.count() == 0:
            self.new_chat_btn.click()
        else:
            # 选择第一个对话并触发选择事件
            self.list_widget.setCurrentRow(0)
            # 发出信号通知需要加载新的对话
            selected_item = self.list_widget.item(0)
            if selected_item:
                self.list_widget.itemClicked.emit(selected_item)
        
        # 保存更新后的对话列表
        self.save_conversations()

class MessageWidget(QWidget):
    regenerate_requested = pyqtSignal()  # 添加信号
    
    def __init__(self, message, is_user=False):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 5, 10, 5)
        
        # 消息气泡布局
        self.bubble_layout = QHBoxLayout()
        self.bubble_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建消息气泡
        self.message_bubble = QTextBrowser()
        self.message_bubble.setOpenExternalLinks(True)
        self.message_bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.message_bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 设置文本换行
        self.message_bubble.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        
        # 设置内容
        self.update_content(message, is_user)
        
        # 设置大小策略
        self.message_bubble.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # 设置气泡样式
        if is_user:
            bubble_style = """
                QTextBrowser {
                    background-color: #0078d4;
                    color: white;
                    border-radius: 15px;
                    padding: 10px;
                    border: none;
                }
                QScrollBar {
                    background: transparent;
                    width: 8px;
                    height: 8px;
                }
                QScrollBar::handle {
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                }
            """
            self.bubble_layout.insertStretch(0)
        else:
            bubble_style = """
                QTextBrowser {
                    background-color: #2d2d2d;
                    color: white;
                    border-radius: 15px;
                    padding: 10px;
                    border: none;
                }
                QScrollBar {
                    background: transparent;
                    width: 8px;
                    height: 8px;
                }
                QScrollBar::handle {
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                }
            """
        
        self.message_bubble.setStyleSheet(bubble_style)
        self.bubble_layout.addWidget(self.message_bubble)
        
        if not is_user:
            self.bubble_layout.addStretch()
            
            # 为AI回复添加按钮组
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 5, 0, 0)
            button_layout.addSpacing(10)
            
            # 复制按钮
            copy_button = QPushButton("复制")
            copy_button.setFixedSize(60, 25)
            copy_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 120, 212, 0.1);
                }
                QPushButton:pressed {
                    background-color: rgba(0, 120, 212, 0.2);
                }
            """)
            copy_button.clicked.connect(self.copy_text)
            
            # 新生成按钮
            regenerate_button = QPushButton("重新生成")
            regenerate_button.setFixedSize(80, 25)
            regenerate_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 120, 212, 0.1);
                }
                QPushButton:pressed {
                    background-color: rgba(0, 120, 212, 0.2);
                }
            """)
            regenerate_button.clicked.connect(self.regenerate_requested.emit)  # 发送信号
            
            button_layout.addWidget(copy_button)
            button_layout.addWidget(regenerate_button)
            button_layout.addStretch()
            
            self.main_layout.addLayout(button_layout)
        
        self.main_layout.addLayout(self.bubble_layout)
        self.setLayout(self.main_layout)
        
    def update_content(self, message, is_user=False):
        """更新消息内容"""
        if not is_user:
            html_content = markdown(
                message,
                extensions=['fenced_code', 'tables', 'codehilite']
            )
            styled_html = f"""
                <style>
                    pre {{
                        background-color: #1e1e1e;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        font-family: 'Courier New', monospace;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                    code {{
                        background-color: #1e1e1e;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                    }}
                    p {{
                        margin: 0;
                        padding: 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                </style>
                {html_content}
            """
            self.message_bubble.setHtml(styled_html)
        else:
            self.message_bubble.setText(message)
        
        # 动态调整大小
        doc = self.message_bubble.document()
        doc.setTextWidth(self.message_bubble.viewport().width())
        doc_height = doc.size().height()
        
        # 设置合适的大小
        content_width = min(600, doc.idealWidth() + 40)
        content_height = min(400, doc_height + 20)
        
        self.message_bubble.setFixedWidth(int(content_width))
        self.message_bubble.setFixedHeight(int(content_height))
    
    def copy_text(self):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.message_bubble.toPlainText())

class ChatThread(QThread):
    """聊天线程类"""
    response_received = pyqtSignal(str, str)  # 发送 (conversation_id, text)
    
    def __init__(self, model, conversation_id):
        super().__init__()
        self.model = model
        self.conversation_id = conversation_id
        self.messages = []  # 存储对话历史
        self.is_running = True
        self.condition = QWaitCondition()
        self.mutex = QMutex()
        self.new_message = False  # 标记是否有新消息
        
    def add_message(self, message, role='user'):
        """添加新消息到对话历史"""
        self.messages.append({'role': role, 'content': message})
        
    def run(self):
        while self.is_running:
            self.mutex.lock()
            if not self.new_message:
                self.condition.wait(self.mutex)  # 等待新消息
            self.new_message = False
            self.mutex.unlock()
            
            if not self.is_running:
                break
                
            try:
                # 使用完整的对话历史进行请求
                stream = ollama.chat(
                    model=self.model,
                    messages=self.messages,
                    stream=True
                )
                
                response_text = ""
                for chunk in stream:
                    if not self.is_running:
                        break
                    text = chunk['message']['content']
                    response_text += text
                    self.response_received.emit(self.conversation_id, response_text)
                
                # 将AI回复添加到对话历史
                if response_text:
                    self.messages = self.messages[:-1]  # 移除临时的用户消息
                    self.add_message(response_text, 'assistant')
                    
            except Exception as e:
                self.response_received.emit(self.conversation_id, f"\n错误: {str(e)}")
    
    def send_message(self, message):
        """发送新消息"""
        self.add_message(message, 'user')
        self.mutex.lock()
        self.new_message = True
        self.condition.wakeOne()  # 唤醒线程处理新消息
        self.mutex.unlock()
            
    def stop(self):
        """停止线程"""
        self.is_running = False
        self.mutex.lock()
        self.condition.wakeOne()  # 唤醒线程以便退出
        self.mutex.unlock()

class ChatDisplay(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: rgba(30, 30, 30, 180);
            }
        """)
        
        # 创建容器widget
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.addStretch()
        self.setWidget(self.container)
        
        # 保存最后一个消息组件的引用
        self.last_message = None
        
    def clear_messages(self):
        """清空所有消息"""
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.last_message = None
                
    def add_message(self, message, is_user=False, new_message=True):
        """添加或更新消息"""
        if new_message:
            # 创建新消息
            message_widget = MessageWidget(message, is_user)
            if not is_user:
                # 连接重新生成信号
                message_widget.regenerate_requested.connect(
                    lambda: self.parent().parent().regenerate_response(message_widget)
                )
            self.layout.insertWidget(self.layout.count() - 1, message_widget)
            self.last_message = message_widget
        elif self.last_message is not None:
            # 更新最后一条消息
            self.last_message.update_content(message, is_user)
            
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 聊天助手")
        self.setMinimumSize(800, 600)  # 设置最小窗口大小
        
        # 设置窗口半透明
        self.setWindowOpacity(0.95)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建左侧对话列表
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.conversation_list = ConversationList()
        left_layout.addWidget(self.conversation_list)
        
        # 添加垂直分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("""
            QFrame {
                color: #3d3d3d;
                border: 1px solid #3d3d3d;
            }
        """)
        
        # 将左侧容器和分隔线添加到分割器
        splitter.addWidget(left_container)
        
        # 创建右侧聊天区域容器
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(10)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加模型选择区域
        model_layout = QHBoxLayout()
        model_label = QLabel("选择模型:")
        model_label.setStyleSheet("color: white; font-size: 14px;")
        self.model_combo = QComboBox()
        
        # 获取本地模型列表
        local_models = ModelManager.get_local_models()
        self.model_combo.addItems(local_models)
        
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(45, 45, 45, 180);
                color: white;
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #3d3d3d;
                selection-color: white;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
        """)
        
        # 添加刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedSize(60, 30)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(0, 120, 212, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 120, 212, 0.2);
            }
        """)
        refresh_button.clicked.connect(self.refresh_models)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(refresh_button)
        model_layout.addStretch()
        chat_layout.addLayout(model_layout)
        
        # 创建聊天显示区域
        self.chat_display = ChatDisplay()
        chat_layout.addWidget(self.chat_display)
        
        # 创建输入区域
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入您的问题...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(45, 45, 45, 180);
                color: white;
                border: 2px solid #3d3d3d;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(80, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d9;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)
        
        splitter.addWidget(chat_container)
        
        # 设置主布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 初始化变量
        self.current_conversation = None
        self.is_new_response = True
        self.chat_threads = {}  # 保存每个对话的线程
        
        # 连接信号
        self.conversation_list.new_chat_btn.clicked.connect(self.new_conversation)
        self.conversation_list.list_widget.itemClicked.connect(self.load_conversation)
        
        # 设置分割器的初始比例
        splitter.setStretchFactor(0, 1)  # 左侧权重为1
        splitter.setStretchFactor(1, 3)  # 右侧权重为3
        
        # 创建新对话
        self.new_conversation()
        
    def new_conversation(self):
        """创建新对话"""
        self.current_conversation = Conversation()
        self.conversation_list.add_conversation(self.current_conversation)
        self.chat_display.clear_messages()
        
        # 为新对话创建线程
        thread = ChatThread(self.model_combo.currentText(), self.current_conversation.id)
        thread.response_received.connect(self.update_chat_display)
        self.chat_threads[self.current_conversation.id] = thread
        thread.start()
    
    def load_conversation(self, item):
        """加载选中的对话"""
        # 停止当前正在运行的线程
        self.stop_current_thread()
        
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation = self.conversation_list.conversations[conv_id]
        self.chat_display.clear_messages()
        
        # 显示历史消息
        for msg in self.current_conversation.messages:
            is_user = msg['role'] == 'user'
            self.chat_display.add_message(
                msg['content'],
                is_user=is_user,
                new_message=True
            )
            if not is_user:
                # 更新最后一条 AI 消息的引用
                self.chat_display.last_message = self.chat_display.layout.itemAt(
                    self.chat_display.layout.count() - 2
                ).widget()
        
        # 创建新的聊天线程
        thread = ChatThread(self.model_combo.currentText(), self.current_conversation.id)
        thread.response_received.connect(self.update_chat_display)
        # 加载历史消息到线程
        for msg in self.current_conversation.messages:
            thread.add_message(msg['content'], msg['role'])
        self.chat_threads[self.current_conversation.id] = thread
        thread.start()
    
    def stop_current_thread(self):
        """停止当前对话的线程"""
        if self.current_conversation and self.current_conversation.id in self.chat_threads:
            thread = self.chat_threads[self.current_conversation.id]
            thread.stop()
            thread.wait()
            # 确保最后一条消息被正确保存
            if thread.conversation_id == self.current_conversation.id:
                self.is_new_response = True
            self.chat_threads.pop(self.current_conversation.id)
            
    def send_message(self):
        if not self.current_conversation:
            self.new_conversation()
            
        message = self.input_field.text().strip()
        if not message:
            return
            
        # 保存用户消息
        self.current_conversation.messages.append({
            'role': 'user',
            'content': message
        })
        
        # 显示用户消息
        self.chat_display.add_message(message, is_user=True)
        self.input_field.clear()
        
        # 更新对话标题
        if len(self.current_conversation.messages) == 1:
            self.current_conversation.title = message[:20] + ('...' if len(message) > 20 else '')
            self.conversation_list.save_conversations()
            # 更新列表显示
            for i in range(self.conversation_list.list_widget.count()):
                item = self.conversation_list.list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_conversation.id:
                    item.setText(self.current_conversation.title)
                    break
        
        # 使用当前对话的线程发送消息
        thread = self.chat_threads[self.current_conversation.id]
        thread.send_message(message)
        self.is_new_response = True
    
    def update_chat_display(self, conversation_id, text):
        """更新聊天显示"""
        # 只有当消息属于当前对话时才更新显示
        if self.current_conversation and conversation_id == self.current_conversation.id:
            self.chat_display.add_message(text, is_user=False, new_message=self.is_new_response)
            self.is_new_response = False
            
            # 更新当前对话的消息
            if self.is_new_response:
                self.current_conversation.messages.append({
                    'role': 'assistant',
                    'content': text
                })
            else:
                # 确保有消息可以更新
                if self.current_conversation.messages and self.current_conversation.messages[-1]['role'] == 'assistant':
                    self.current_conversation.messages[-1]['content'] = text
                else:
                    self.current_conversation.messages.append({
                        'role': 'assistant',
                        'content': text
                    })
                
            # 保存对话
            self.conversation_list.save_conversations()
            
    def closeEvent(self, event):
        """窗口关闭时清理所有线程"""
        for thread in self.chat_threads.values():
            thread.stop()
            thread.wait()
        event.accept()
        
    def resizeEvent(self, event):
        """窗口大小改变时调整消息气泡的最大宽度"""
        super().resizeEvent(event)
        # 遍历所有消息组件
        if hasattr(self, 'chat_display'):
            for i in range(self.chat_display.layout.count() - 1):  # -1 是因为最后一个是 stretch
                item = self.chat_display.layout.itemAt(i)
                if item and item.widget():
                    message_widget = item.widget()
                    text_browser = message_widget.findChild(QTextBrowser)
                    if text_browser:
                        text_browser.setMaximumWidth(int(self.width() * 0.7))
                        text_browser.document().adjustSize()
        
    def regenerate_response(self, message_widget):
        """重新生成回答"""
        if self.current_conversation and self.current_conversation.messages:
            # 获取最后一个用户消息
            user_messages = [msg for msg in self.current_conversation.messages if msg['role'] == 'user']
            if user_messages:
                last_user_message = user_messages[-1]['content']
                
                # 清空当前消息组件的内容
                message_widget.update_content("")
                
                # 创建新的聊天线程
                thread = ChatThread(
                    self.model_combo.currentText(),
                    self.current_conversation.id
                )
                thread.response_received.connect(lambda conv_id, text: self.update_regenerated_response(message_widget, conv_id, text))
                self.chat_threads[self.current_conversation.id] = thread
                thread.start()
    
    def update_regenerated_response(self, message_widget, conversation_id, text):
        """更新重新生成的回答"""
        if self.current_conversation and conversation_id == self.current_conversation.id:
            message_widget.update_content(text)
            
            # 更新对话历史
            if self.current_conversation.messages and self.current_conversation.messages[-1]['role'] == 'assistant':
                self.current_conversation.messages[-1]['content'] = text
            
            # 保存对话
            self.conversation_list.save_conversations()
    
    def refresh_models(self):
        """刷新模型列表"""
        current_model = self.model_combo.currentText()
        self.model_combo.clear()
        local_models = ModelManager.get_local_models()
        self.model_combo.addItems(local_models)
        
        # 尝试恢复之前选择的模型
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        