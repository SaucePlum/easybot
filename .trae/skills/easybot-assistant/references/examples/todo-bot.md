# 待办事项机器人

一个展示数据持久化和命令系统的完整示例。

## 功能概述

- 添加/删除/查看待办事项
- 数据持久化存储
- 支持设置优先级和截止日期
- 列表管理功能

## 核心代码

```python
import json
import os
from datetime import datetime
from typing import Optional
from easybot import Bot, Model, CommandValidScenes, Scope, WaitTimeoutError

bot = Bot(
    app_id="your_app_id",
    app_secret="your_app_secret",
)

DATA_FILE = "sdk_data/todos.json"

def load_todos() -> dict:
    """加载待办数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_todos(todos: dict) -> None:
    """保存待办数据"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def get_user_key(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage) -> str:
    """获取用户唯一标识"""
    if hasattr(msg.author, 'id'):
        return msg.author.id
    return msg.author.user_openid

@bot.on_command(command=["待办", "todo"], valid_scenes=CommandValidScenes.ALL)
async def todo_menu(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """待办事项菜单"""
    await msg.reply(
        "📋 待办事项管理\n"
        "━━━━━━━━━━━━━\n"
        "添加 待办内容 - 添加新待办\n"
        "列表 - 查看所有待办\n"
        "完成 编号 - 标记完成\n"
        "删除 编号 - 删除待办\n"
        "清空 - 清空所有待办"
    )

@bot.on_command(command="添加", valid_scenes=CommandValidScenes.ALL)
async def add_todo(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """添加待办事项"""
    content = msg.treated_msg.replace("添加", "").strip()
    
    if not content:
        await msg.reply("请输入待办内容，例如：添加 完成作业")
        return
    
    user_key = get_user_key(msg)
    todos = load_todos()
    
    if user_key not in todos:
        todos[user_key] = []
    
    todo_id = len(todos[user_key]) + 1
    
    todos[user_key].append({
        "id": todo_id,
        "content": content,
        "done": False,
        "created_at": datetime.now().isoformat(),
        "priority": "normal"
    })
    
    save_todos(todos)
    await msg.reply(f"✅ 已添加待办：{content}")

@bot.on_command(command=["列表", "list"], valid_scenes=CommandValidScenes.ALL)
async def list_todos(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """查看待办列表"""
    user_key = get_user_key(msg)
    todos = load_todos()
    
    if user_key not in todos or not todos[user_key]:
        await msg.reply("📭 暂无待办事项")
        return
    
    lines = ["📋 待办事项列表", "━━━━━━━━━━━━━"]
    
    for todo in todos[user_key]:
        status = "✅" if todo["done"] else "⬜"
        content = todo["content"]
        if todo["done"]:
            content = f"~~{content}~~"
        lines.append(f"{status} [{todo['id']}] {content}")
    
    await msg.reply("\n".join(lines))

@bot.on_command(command="完成", valid_scenes=CommandValidScenes.ALL)
async def complete_todo(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """标记待办完成"""
    try:
        todo_id = int(msg.treated_msg.replace("完成", "").strip())
    except ValueError:
        await msg.reply("请输入有效的编号，例如：完成 1")
        return
    
    user_key = get_user_key(msg)
    todos = load_todos()
    
    if user_key not in todos:
        await msg.reply("📭 暂无待办事项")
        return
    
    for todo in todos[user_key]:
        if todo["id"] == todo_id:
            todo["done"] = True
            save_todos(todos)
            await msg.reply(f"✅ 已完成：{todo['content']}")
            return
    
    await msg.reply(f"❌ 未找到编号为 {todo_id} 的待办")

@bot.on_command(command="删除", valid_scenes=CommandValidScenes.ALL)
async def delete_todo(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """删除待办事项"""
    try:
        todo_id = int(msg.treated_msg.replace("删除", "").strip())
    except ValueError:
        await msg.reply("请输入有效的编号，例如：删除 1")
        return
    
    user_key = get_user_key(msg)
    todos = load_todos()
    
    if user_key not in todos:
        await msg.reply("📭 暂无待办事项")
        return
    
    for i, todo in enumerate(todos[user_key]):
        if todo["id"] == todo_id:
            deleted = todos[user_key].pop(i)
            save_todos(todos)
            await msg.reply(f"🗑️ 已删除：{deleted['content']}")
            return
    
    await msg.reply(f"❌ 未找到编号为 {todo_id} 的待办")

@bot.on_command(command="清空", valid_scenes=CommandValidScenes.ALL)
async def clear_todos(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """清空所有待办"""
    with bot.session.bind(msg) as s:
        await msg.reply("⚠️ 确定要清空所有待办吗？回复「确认」继续")
        
        try:
            result = await s.wait_for(
                scopes=Scope.USER,
                command="确认",
                timeout=30
            )
            
            user_key = get_user_key(msg)
            todos = load_todos()
            
            if user_key in todos:
                count = len(todos[user_key])
                todos[user_key] = []
                save_todos(todos)
                await msg.reply(f"🗑️ 已清空 {count} 条待办")
            else:
                await msg.reply("📭 暂无待办事项")
        
        except WaitTimeoutError:
            await msg.reply("⏰ 操作已取消")

@bot.on_command(command="统计", valid_scenes=CommandValidScenes.ALL)
async def todo_stats(msg: Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage):
    """待办统计"""
    user_key = get_user_key(msg)
    todos = load_todos()
    
    if user_key not in todos or not todos[user_key]:
        await msg.reply("📭 暂无待办事项")
        return
    
    user_todos = todos[user_key]
    total = len(user_todos)
    done = sum(1 for t in user_todos if t["done"])
    pending = total - done
    
    await msg.reply(
        f"📊 待办统计\n"
        f"━━━━━━━━━━━━━\n"
        f"总计: {total} 条\n"
        f"已完成: {done} 条\n"
        f"待处理: {pending} 条\n"
        f"完成率: {done/total*100:.1f}%"
    )

bot.start()
```

## 关键知识点

1. **数据持久化**：使用 JSON 文件存储数据
2. **用户隔离**：通过用户 ID 区分不同用户的数据
3. **命令解析**：从消息中提取命令参数
4. **确认机制**：使用 `wait_for` 实现危险操作确认

## 扩展建议

- 添加截止日期提醒功能
- 支持优先级排序
- 添加分类标签
- 支持多人共享列表
- 添加定时提醒
