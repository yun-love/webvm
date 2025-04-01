import requests
import json
import argparse
from flask import Flask, request, jsonify
import logging
import threading
import os
import time

# 配置默认参数
DEFAULT_CONFIG = {
    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key",
    "api_port": 5000,
    "api_secret": "your-secret-key",
    "rate_limit": 20  # 每分钟限制
}

class WeComBot:
    def __init__(self, config_path="config.json"):
        self.config = self.load_config(config_path)
        self.rate_limit_counter = 0
        self.last_reset = time.time()
        
    def load_config(self, path):
        """加载配置文件"""
        if os.path.exists(path):
            with open(path) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        return DEFAULT_CONFIG

    def check_rate_limit(self):
        """速率限制检查"""
        now = time.time()
        if now - self.last_reset > 60:
            self.rate_limit_counter = 0
            self.last_reset = now
        if self.rate_limit_counter >= self.config["rate_limit"]:
            raise Exception("Rate limit exceeded")
        self.rate_limit_counter += 1

    def send_message(self, data):
        """发送消息到企业微信"""
        try:
            self.check_rate_limit()
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.config["webhook_url"],
                headers=headers,
                data=json.dumps(data)
            )
            result = response.json()
            if result.get("errcode") != 0:
                logging.error(f"发送失败: {result.get('errmsg')}")
                return False
            logging.info("消息发送成功")
            return True
        except Exception as e:
            logging.error(f"发送异常: {str(e)}")
            return False

    def create_message(self, msg_type, content):
        """创建消息结构"""
        handlers = {
            "text": lambda: {"msgtype": "text", "text": {"content": content}},
            "markdown": lambda: {"msgtype": "markdown", "markdown": {"content": content}},
            "link": lambda: {
                "msgtype": "link",
                "link": {
                    "title": content.get("title"),
                    "url": content.get("url"),
                    "text": content.get("desc", ""),
                    "picurl": content.get("picurl", "")
                }
            },
            "image": lambda: {
                "msgtype": "image",
                "image": {"base64": content["base64"], "md5": content["md5"]}
            }
        }
        return handlers.get(msg_type.lower())()

app = Flask(__name__)
bot = None

@app.route('/send', methods=['POST'])
def api_send():
    """API发送接口"""
    # 验证密钥
    if request.headers.get("X-API-Secret") != bot.config["api_secret"]:
        return jsonify({"status": "error", "message": "Invalid secret"}), 401
    
    data = request.json
    try:
        msg_type = data["type"]
        content = data["content"]
        message = bot.create_message(msg_type, content)
        if bot.send_message(message):
            return jsonify({"status": "success"})
        return jsonify({"status": "error"}), 500
    except Exception as e:
        logging.error(f"API错误: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

def start_cli():
    """命令行交互模式"""
    print("企业微信消息推送器（CLI模式）")
    while True:
        try:
            raw = input("> ").strip()
            if not raw:
                continue
            if raw.lower() in ["exit", "quit"]:
                break
            
            # 解析命令行输入
            if raw.startswith("file:"):
                # 文件上传处理
                pass
            else:
                message = bot.create_message("text", raw)
                bot.send_message(message)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="企业微信消息推送器")
    parser.add_argument("--api", action="store_true", help="启动API服务模式")
    parser.add_argument("--cli", action="store_true", help="启动命令行交互模式")
    args = parser.parse_args()

    bot = WeComBot()

    if args.api:
        logging.info(f"启动API服务，端口：{bot.config['api_port']}")
        app.run(host='0.0.0.0', port=bot.config["api_port"])
    elif args.cli:
        start_cli()
    else:
        print("请指定运行模式：--api 或 --cli")
