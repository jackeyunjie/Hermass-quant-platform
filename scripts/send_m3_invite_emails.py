#!/usr/bin/env python3
"""
M3 Pilot 邀请邮件发送脚本
使用 QQ 邮箱 SMTP 发送邀请邮件

用法:
    python scripts/send_m3_invite_emails.py

需要修改下面的配置:
    - SMTP_USER: 发件人 QQ 邮箱
    - SMTP_PASS: SMTP 授权码
    - HOST: 服务器地址
    - recipients: 收件人列表（邮箱、称呼、pilot 信息）
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============ 配置区域（请修改） ============

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "1300893414@qq.com"
SMTP_PASS = "dyhqeduaqsrnihag"  # SMTP 授权码

# 服务器地址（替换 <host>）
HOST = "quant.supertrader.world"

# 收件人列表
# 格式: (邮箱, 称呼, pilot_id, user_type, token)
RECIPIENTS = [
    # pilot-02: 策略研究员
    ("554732319@qq.com", "朋友", "pilot-02", "策略研究员", "cfIPwHmW0G9rjm4rDQuHBA"),
    # pilot-03: 私募量化研究员
    ("3393639019@qq.com", "朋友", "pilot-03", "私募量化研究员", "AlLg1MjVVC0a6SuY-4EGOA"),
    # 请添加更多收件人...
]

# ============ 邮件模板 ============

EMAIL_SUBJECT = "Hermass 策略研究工具 - 受控试点邀请（2 周）"

EMAIL_TEMPLATE = """Hi {name}，

你被选为 Hermass 首批受控试点用户之一。

Hermass 是一个 AI 原生的量化策略研究平台，当前处于早期研究工具阶段：
- 它帮助研究者把中文策略想法转化为结构化 DSL；
- 它提供条件预览、红线检查和基于历史 A 股日线数据的 Light Backtest；
- 它输出交易证据和审计链路，用于假设验证和复盘。

重要边界：
- Hermass 不是投资建议服务，不承诺收益，不提供买卖指令。
- 回测基于历史日线数据（A 股，2018-2026，前复权），不包含实时行情。
- 系统不提供真实交易执行、资金托管或自动下单功能。
- 所有输出仅用于研究，不构成对未来表现的预测。

试点安排：
- 人数：5 人
- 周期：2 周
- 形式：通过邀请链接进入，完成免责声明和分层诊断后即可使用
- 反馈：第 7 天和第 14 天各一次简短问卷

邀请链接：http://{host}/onboarding/?invite={token}

请在使用前阅读并确认免责声明。如果你有任何问题，随时联系我。

Hermass 团队
{date}
"""

# ============ 发送逻辑 ============

def send_email(to_addr: str, name: str, pilot_id: str, user_type: str, token: str) -> bool:
    """发送单封邀请邮件"""
    if not to_addr:
        print(f"  跳过 {pilot_id}: 邮箱地址为空")
        return False
    
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    msg["Subject"] = EMAIL_SUBJECT
    
    body = EMAIL_TEMPLATE.format(
        name=name,
        host=HOST,
        token=token,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_addr, msg.as_string())
        print(f"  已发送: {pilot_id} ({user_type}) -> {to_addr}")
        return True
    except Exception as e:
        print(f"  发送失败: {pilot_id} -> {to_addr}: {e}")
        return False

def main():
    print("=" * 50)
    print("M3 Pilot 邀请邮件发送")
    print("=" * 50)
    print(f"发件人: {SMTP_USER}")
    print(f"服务器: {HOST}")
    print(f"收件人数量: {len(RECIPIENTS)}")
    print("-" * 50)
    
    success = 0
    failed = 0
    skipped = 0
    
    for email, name, pilot_id, user_type, token in RECIPIENTS:
        if not email:
            skipped += 1
            continue
        
        if send_email(email, name, pilot_id, user_type, token):
            success += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"发送完成: 成功 {success}, 失败 {failed}, 跳过 {skipped}")
    print("=" * 50)
    
    # 输出发送记录（用于更新 0017 决策记录）
    print("\n发送记录（请复制到 0017 决策记录）:")
    print("| 编号 | 邮箱 | 称呼 | 发送时间 | 状态 |")
    print("|---|---|---|---|---|")
    for email, name, pilot_id, user_type, token in RECIPIENTS:
        status = "已发送" if email else "待发送"
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M") if email else "-"
        print(f"| {pilot_id} | {email or '-'} | {name or '-'} | {time_str} | {status} |")

if __name__ == "__main__":
    main()
