import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import sys
import os

# FIXED: UTF-8 encoding for Windows console + file logging
if os.name == 'nt':  # Windows
    sys.stdout.reconfigure(encoding='utf-8')
    logging.getLogger().handlers = []  # Clear default handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('balance_log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    encoding='utf-8'
)
logger = logging.getLogger()

class BalanceMonitorSingleRun:
    def __init__(self):
        self.agent_emails = ["avinash.sk@hopzy.in",]
        self.cc_emails = ["tejus.a@hopzy.in",]
        self.smtp_server = "smtp.zoho.in"
        self.smtp_port = 587
        self.sender_email = "madhu.l@hopzy.in"
        self.sender_password = "JqkGLkfkTf0n"
        self.thresholds = {"EzeeInfo": 5000, "Bitla": 10000, "Vaagai": 5000}

    async def fetch_ezeeinfo_balance(self, session):
        url = "https://prodapi.hopzy.in/api/public/getprofileDetails/85838250575G9524849Q104XEL1CLB8"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                logger.info(f"EzeeInfo API Status: {resp.status}")
                data = await resp.json()
                balance = float(data.get('data', {}).get('data', {}).get('currentBalance', 0))
                logger.info(f"OK EzeeInfo balance: ₹{balance:,.2f}")
                return balance
        except Exception as e:
            logger.error(f"ERROR EzeeInfo fetch failed: {e}")
            return 0.0

    async def fetch_bitla_balance(self, session):
        url = "https://gds.ticketsimply.com/gds/api/get_balance.json?api_key=TSVMQUAPI06318478"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                logger.info(f"Bitla API Status: {resp.status}")
                data = await resp.json()
                balance = float(data.get('result', {}).get('balance_amount', 0))
                logger.info(f"OK Bitla balance: ₹{balance:,.2f}")
                return balance
        except Exception as e:
            logger.error(f"ERROR Bitla fetch failed: {e}")
            return 0.0

    async def fetch_vaagai_balance(self, session):
        url = "https://api.vaagaibus.in/api/GetOperatorList/hopzy"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'insomnia/11.0',
            'token': 'MTE1YzI2YzEwOWMxMDdjOTNjMTA2YzEwMmM4OWMxMDFjOTNjMjZjNTBjMjRjMjZjOTZjMTAzYzEwNGMxMTRjMTEzYzEwN2MxMDBjMjZjMzZjMjZjMTA0Yzg5YzEwN2MxMDdjMTExYzEwM2MxMDZjOTJjMjZjNTBjMjZjNjRjMTAzYzc1YzEwM2M0MmMxMDRjMTA4YzQ5YzI2YzExN2M3MA==',
        }
        cookies = {'PHPSESSID': '5gbecimc48p21906k1qa7edu1g'}
        try:
            async with session.post(url, headers=headers, cookies=cookies, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                logger.info(f"Vaagai API Status: {resp.status}")
                data = await resp.json()
                balance_str = data.get('status', {}).get('profiledata', {}).get('balance', '0')
                balance = float(balance_str)
                logger.info(f"OK Vaagai balance: ₹{balance:,.2f}")
                return balance
        except Exception as e:
            logger.error(f"ERROR Vaagai fetch failed: {e}")
            return 0.0

    def get_html_balance(self, provider: str, balance: float) -> str:
        threshold = self.thresholds[provider]
        if balance <= threshold and balance > 0:
            return f'<span style="color: #dc2626; font-weight: 700; font-size: 28px; letter-spacing: -0.5px;">₹{balance:,.0f}</span>'
        elif balance > 0:
            return f'<span style="color: #059669; font-weight: 700; font-size: 28px; letter-spacing: -0.5px;">₹{balance:,.0f}</span>'
        return '<span style="color: #6b7280; font-weight: 500; font-size: 24px;">₹0.00 (Error)</span>'

    async def send_email(self, ezeeinfo_balance: float, bitla_balance: float, vaagai_balance: float):
        ezeeinfo_html = self.get_html_balance("EzeeInfo", ezeeinfo_balance)
        bitla_html = self.get_html_balance("Bitla", bitla_balance)
        vaagai_html = self.get_html_balance("Vaagai", vaagai_balance)
        
        is_low = (ezeeinfo_balance <= self.thresholds["EzeeInfo"] or 
                 bitla_balance <= self.thresholds["Bitla"] or 
                 vaagai_balance <= self.thresholds["Vaagai"])
        subject = "🚨 GDS Balance Alert - Action Required" if is_low else "✅ GDS Wallet Status Report"
        
        # ENHANCED 1000px WIDTH PROFESSIONAL TEMPLATE
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }}
                .email-container {{ width: 100%; max-width: 800px; margin: 20px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }}
                .header-section {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; padding: 25px 30px; }}
                .header-content {{ display: flex; justify-content: space-between; align-items: center; }}
                .status-bar {{ background: {'#fef2f2' if is_low else '#f0fdf4'}; padding: 20px 30px; border-bottom: 1px solid {'#fecaca' if is_low else '#bbf7d0'}; }}
                .status-text {{ font-size: 15px; font-weight: 600; color: {'#dc2626' if is_low else '#059669'}; }}
                .status-badge {{ display: inline-block; background: {'#fee2e2' if is_low else '#d1fae5'}; padding: 8px 16px; border-radius: 25px; font-size: 13px; font-weight: 700; color: {'#dc2626' if is_low else '#059669'}; }}
                .content-section {{ padding: 35px 30px; }}
                .section-title {{ font-size: 22px; font-weight: 700; color: #2c3e50; margin-bottom: 10px; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
                .subtitle {{ font-size: 15px; color: #6b7280; margin-bottom: 30px; }}
                .balance-grid {{ display: table; width: 100%; border-collapse: separate; border-spacing: 0 12px; table-layout: fixed; }}
                .balance-card {{ display: table-row; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; }}
                .balance-card:hover {{ box-shadow: 0 8px 25px rgba(0,0,0,0.1); transform: translateY(-2px); }}
                .provider-info {{ display: table-cell; width: 45%; padding: 12px 15px; vertical-align: middle; }}
                .provider-logo {{ width: 200px; height: 55px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 29px; font-weight: 700; color: white; }}
                .bitla-logo {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); }}
                .vaagai-logo {{ background: linear-gradient(135deg, #06b6d4, #0891b2); }}
                .ezee-logo {{ background: linear-gradient(135deg, #10b981, #059669); }}
                .balance-amount {{ display: table-cell; width: 22%; padding: 12px 15px; text-align: center; font-size: 32px; font-weight: 700; vertical-align: middle; }}
                .threshold-info {{ display: table-cell; width: 33%; padding: 12px 15px; vertical-align: middle; text-align: right; }}
                .threshold-label {{ font-size: 20px; color: #6b7280; margin-bottom: 6px; }}
                .threshold-value {{ font-size: 23px; font-weight: 700; color: #1e40af; }}
                .footer {{ background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); color: #ecf0f1; padding: 30px; text-align: center; font-size: 14px; }}
                @media (max-width: 768px) {{
                    .email-container {{ margin: 10px; border-radius: 8px; }}
                    .header-content {{ flex-direction: column; gap: 15px; text-align: center; }}
                    .content-section {{ padding: 30px 25px;; }}
                    .balance-card {{ display: block; margin-bottom: 15px; }}
                    .provider-info, .balance-amount, .threshold-info {{ display: block; width: 100%; text-align: center; padding: 15px 20px; }}
                    .balance-grid {{ border-spacing: 0; }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <!-- Header -->
                <div class="header-section">
                    <div class="header-content">
                        <div style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                            {('🚨 GDS Balance Alert' if is_low else '✅ GDS Wallet Status')}
                        </div>
                         <!--<div style="font-size: 17px; opacity: 0.95;">Hopzy Wallet Dashboard</div> -->
                    </div>
                </div>

                <!-- Status Bar -->
                <div class="status-bar">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td class="status-text">
                                {('⚠️ One or more wallets below threshold - Immediate action required' if is_low else ' All wallets above threshold limits')}
                            </td>
                            <td align="right">
                                <span class="status-badge">{('CRITICAL' if is_low else 'NORMAL')}</span>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Content -->
                <div class="content-section">
                    <!--<div class="section-title">Current Wallet Balances</div>-->
                    <!--<div class="subtitle">Real-time balances across all GDS providers (Updated live)</div> -->
                    
                    <table class="balance-grid">
                        <!-- Bitla Card -->
                        <tr class="balance-card">
                            <td class="provider-info">
                                <div class="provider-logo bitla-logo">Bitla</div>
                            </td>
                            <td class="balance-amount">{bitla_html}</td>
                            <td class="threshold-info">
                                <div class="threshold-label">Threshold</div>
                                <div class="threshold-value">₹{self.thresholds['Bitla']:,.0f}</div>
                            </td>
                        </tr>

                        <!-- Vaagai Card -->
                        <tr class="balance-card">
                            <td class="provider-info">
                                <div class="provider-logo vaagai-logo">Vaagai</div>
                            </td>
                            <td class="balance-amount">{vaagai_html}</td>
                            <td class="threshold-info">
                                <div class="threshold-label">Threshold</div>
                                <div class="threshold-value">₹{self.thresholds['Vaagai']:,.0f}</div>
                            </td>
                        </tr>

                        <!-- EzeeInfo Card -->
                        <tr class="balance-card">
                            <td class="provider-info">
                                <div class="provider-logo ezee-logo">EzeeInfo</div>
                            </td>
                            <td class="balance-amount">{ezeeinfo_html}</td>
                            <td class="threshold-info">
                                <div class="threshold-label">Threshold</div>
                                <div class="threshold-value">₹{self.thresholds['EzeeInfo']:,.0f}</div>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Footer -->
                <div class="footer">
                    <div style="max-width: 280px; margin: 0 auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; font-size: 15px;">
                            <span>Last Updated:</span>
                            <strong>{datetime.now().strftime('%d %b %Y, %I:%M %p IST')}</strong>
                        </div>
                        <div style="font-size: 13px; opacity: 0.9;">
                             GDS Wallet Status | Next check in 3 hours
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(self.agent_emails)
        if self.cc_emails:
            msg['Cc'] = ", ".join(self.cc_emails)
        
        msg.attach(MIMEText(html_body, 'html'))
        
        recipients = self.agent_emails[:]
        if self.cc_emails:
            recipients += self.cc_emails
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            logger.info(f"OK EMAIL SENT SUCCESSFULLY - {subject}")
            return True
        except Exception as e:
            logger.error(f"ERROR EMAIL FAILED - Check Zoho credentials: {e}")
            return False

    async def run_single_check(self):
        print("Fetching LIVE balances...")
        logger.info("=== GDS Balance Check Started ===")
        
        async with aiohttp.ClientSession() as session:
            ezeeinfo_task = asyncio.create_task(self.fetch_ezeeinfo_balance(session))
            bitla_task = asyncio.create_task(self.fetch_bitla_balance(session))
            vaagai_task = asyncio.create_task(self.fetch_vaagai_balance(session))
            ezeeinfo_balance, bitla_balance, vaagai_balance = await asyncio.gather(ezeeinfo_task, bitla_task, vaagai_task)
        
        RED, GREEN, RESET = "\033[91m", "\033[92m", "\033[0m"
        ezeeinfo_color = f"{RED}₹{ezeeinfo_balance:,.0f}{RESET}" if ezeeinfo_balance <= self.thresholds["EzeeInfo"] else f"{GREEN}₹{ezeeinfo_balance:,.0f}{RESET}"
        bitla_color = f"{RED}₹{bitla_balance:,.0f}{RESET}" if bitla_balance <= self.thresholds["Bitla"] else f"{GREEN}₹{bitla_balance:,.0f}{RESET}"
        vaagai_color = f"{RED}₹{vaagai_balance:,.0f}{RESET}" if vaagai_balance <= self.thresholds["Vaagai"] else f"{GREEN}₹{vaagai_balance:,.0f}{RESET}"
        
        print(f"gds:ezeeinfo,vaagai,bitla total balance:{ezeeinfo_color},{vaagai_color},{bitla_color}  threshold balance :{self.thresholds['EzeeInfo']:,},{self.thresholds['Vaagai']:,},{self.thresholds['Bitla']:,}")
        logger.info(f"Console: gds:ezeeinfo,vaagai,bitla total balance:{ezeeinfo_balance:,.0f},{vaagai_balance:,.0f},{bitla_balance:,.0f}")
        
        await self.send_email(ezeeinfo_balance, bitla_balance, vaagai_balance)
        logger.info("=== GDS Balance Check Completed ===")
        print("Done! Check balance_log.txt for details.")

async def main():
    monitor = BalanceMonitorSingleRun()
    await monitor.run_single_check()

if __name__ == "__main__":
    asyncio.run(main())


