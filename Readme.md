# 初始化
```python
from wechat.app import WeChatApp
app = WeChatApp('xxxxxxxx', 'xxxxxxxx', 'xxxxxxxxxxxx')

app.send_text_message() #发送文本信息
app.send_card_message() # 发送卡片信息
app.send_file_message() # 推送文件信息
app.upload_media_file() # 上传临时文件

app.get_department_user() # 获取部门人员
app.get_department() # 获取部门
app.get_app_info() # 获取app信息

# 创建讨论组app必须挂在根部门下
app.chat.send_card_message() # 给讨论组发送卡片信息
app.chat.send_text_message() # 给讨论组发送文本信息
app.chat.send_markdown() # 给讨论组发送Markdown文本
app.chat.modify_chat() # 修改讨论组
app.chat.create_chat() # 创建讨论组

```