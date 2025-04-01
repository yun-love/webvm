import requests
import json

# 企业微信机器人Webhook地址
webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=16d86fc7-b892-448f-a79f-d3bf5f25523a"

headers = {"Content-Type": "application/json"}

def send_message(content):
    """发送消息到企业微信机器人"""
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
        result = response.json()
        if result.get("errcode") != 0:
            print(f"发送失败，错误信息：{result.get('errmsg')}")
        else:
            print("消息发送成功！")
    except Exception as e:
        print(f"请求异常：{str(e)}")

if __name__ == "__main__":
    print("企业微信消息推送工具（输入exit退出）")
    while True:
        message = input("请输入要推送的消息内容：").strip()
        
        if not message:
            continue
            
        if message.lower() == "exit":
            print("程序已退出")
            break
            
        send_message(message)