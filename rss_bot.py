import feedparser
import logging
import asyncio
import json
import os
from telegram import Bot
from telegram.error import TelegramError

# Telegram Bot Token 和目标聊天 ID
TELEGRAM_TOKEN = 'Bot Token'
CHAT_ID = '群ID'

# 存储已发送的帖子 ID 的文件
POSTS_FILE = 'sent_posts.json'

# 读取已发送的帖子 ID
def load_sent_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return []

# 保存已发送的帖子 ID
def save_sent_posts(post_ids):
    with open(POSTS_FILE, 'w') as f:
        json.dump(post_ids, f)

# 从 RSS 源获取更新
def fetch_updates():
    feed_url = "订阅地址"
    try:
        return feedparser.parse(feed_url)
    except Exception as e:
        logging.error(f"获取 RSS 更新时出错: {e}")
        return None

# 转义 Markdown 特殊字符
def escape_markdown(text):
    special_chars = r"_*~`>#+-.!"
    for char in special_chars:
        text = text.replace(char, f"\{char}")
    return text

# 发送消息到 Telegram
async def send_message(bot, title, link):
    # 转义 Markdown 特殊字符
    escaped_title = escape_markdown(title)  # 转义 Markdown 特殊字符
    escaped_link = escape_markdown(link)    # 转义 Markdown 特殊字符

    # 使用 Markdown 格式，将标题包裹在反引号中以避免超链接，链接直接显示
    message = f"`{escaped_title}`\n{escaped_link}"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='MarkdownV2')
        logging.info(f"消息发送成功: {escaped_title}")
    except TelegramError as e:
        logging.error(f"发送消息时出错: {e}")

# 主函数
async def check_for_updates(sent_post_ids):
    updates = fetch_updates()

    if updates is None:
        return  # 如果获取更新出错，则返回

    new_post_ids = []  # 用于存储新帖子 ID

    for entry in updates.entries:
        # 从 guid 中提取帖子 ID
        post_id = entry.guid.split('-')[-1].split('.')[0]  # 提取 ID

        # 检查是否为新帖子
        if post_id not in sent_post_ids:
            new_post_ids.append((post_id, entry.title, entry.link))  # 存储 ID, 标题和链接

    # 如果有新帖子，按 ID 升序排序并发送最新帖子
    if new_post_ids:
        new_post_ids.sort(key=lambda x: int(x[0]))  # 升序排序
        latest_post_id, title, link = new_post_ids[0]  # 获取最新的帖子
        async with Bot(token=TELEGRAM_TOKEN) as bot:
            await send_message(bot, title, link)

        # 更新已发送的帖子 ID
        sent_post_ids.append(latest_post_id)
        save_sent_posts(sent_post_ids)  # 保存到文件

# 主循环
async def main():
    logging.basicConfig(level=logging.INFO)

    # 加载已发送的帖子 ID
    sent_post_ids = load_sent_posts()

    while True:
        try:
            await check_for_updates(sent_post_ids)
        except Exception as e:
            logging.error(f"检查更新时出错: {e}")
        await asyncio.sleep(60)  # 每 60 秒检查一次

if __name__ == "__main__":
    asyncio.run(main())
