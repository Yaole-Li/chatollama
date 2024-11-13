# ChatOllama

ChatOllama 是一个基于 Ollama API 的本地聊天应用程序，提供了类似 ChatGPT 的用户界面，支持多个对话管理、模型选择等功能。

## 功能特点

- 🚀 流畅的聊天体验
- 💾 本地对话历史保存
- 🔄 支持多个对话管理
- 🎨 美观的深色主题界面
- 📝 Markdown 格式支持
- 🔍 代码高亮显示
- 🔄 实时流式输出
- 🛠 支持多个本地模型切换

## 安装说明

### 前置要求

- Python 3.8 或更高版本
- Ollama 已安装并运行
- 至少一个已下载的 Ollama 模型

### 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/Yaole-Li/chatollama.git
cd chatollama
```

2. 创建虚拟环境（可选但推荐）：
```bash
python -m venv myEnv
source myEnv/bin/activate  # Linux/Mac
# 或
myEnv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用说明

1. 启动应用：
```bash
python main.py
```

2. 主要功能：
   - 左侧栏：管理对话历史
   - 右上角：选择和刷新可用模型
   - 中间区域：显示对话内容
   - 底部：输入问题并发送

3. 快捷操作：
   - 回车键：发送消息
   - 右键点击对话：删除对话
   - 复制按钮：复制 AI 回答内容
   - 重新生成：重新生成 AI 回答

## 项目结构

```
chatollama/
├── main.py           # 程序入口
├── chat_ui.py        # UI 实现
├── requirements.txt  # 项目依赖
└── conversations.json # 对话历史存储（自动生成）
```

## 依赖说明

- PyQt6：GUI 框架
- ollama：与 Ollama API 交互
- markdown：Markdown 渲染
- Pygments：代码高亮

## 注意事项

1. 确保 Ollama 服务正在运行
2. 确保至少安装了一个 Ollama 模型
3. 首次运行时会自动创建对话历史文件

## 常见问题

1. 如果遇到模型无法加载：
   - 检查 Ollama 服务是否运行
   - 使用 `ollama list` 确认模型是否已安装

2. 如果界面显示异常：
   - 确保安装了所有依赖
   - 尝试重新启动应用

## 许可证

[MIT License](LICENSE) 