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
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    logging.getLogger().handlers = []  # Clear default handlers


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('balance_log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    encoding='utf-8'  # Python 3.7+ required
)
logger = logging.getLogger()


class BalanceMonitorSingleRun:
    def __init__(self):
        self.agent_emails = [ "avinash.sk@hopzy.in",]  # UPDATE YOUR AGENTS
        self.cc_emails = ["raj.shivraj@hopzy.in","tejus.a@hopzy.in", ]  # ADD CC EMAILS HERE
        self.smtp_server = "smtp.zoho.in"
        self.smtp_port = 587
        self.sender_email = "madhu.l@hopzy.in"  # UPDATE YOUR EMAIL
        self.sender_password = "JqkGLkfkTf0n"  # UPDATE APP PASSWORD
        self.thresholds = {"Bitla": 10000, "Vaagai": 5000}

    async def fetch_bitla_balance(self, session):
        url = "https://gds.ticketsimply.com/gds/api/get_balance.json?api_key=TSVMQUAPI06318478"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                logger.info(f"Bitla API Status: {resp.status}")
                data = await resp.json()
                balance = float(data.get('result', {}).get('balance_amount', 0))
                logger.info(f"OK Bitla balance: ₹{balance:,.2f}")  # FIXED: No emoji
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
                logger.info(f"OK Vaagai balance: ₹{balance:,.2f}")  # FIXED: No emoji
                return balance
        except Exception as e:
            logger.error(f"ERROR Vaagai fetch failed: {e}")
            return 0.0

    def get_html_balance(self, provider: str, balance: float) -> str:
        threshold = self.thresholds[provider]
        if balance <= threshold and balance > 0:
            return f'<span style="color: #d32f2f; font-weight: bold; font-size: 24px;">₹{balance:,.2f}</span>'
        elif balance > 0:
            return f'<span style="color: #388e3c; font-weight: bold; font-size: 24px;">₹{balance:,.2f}</span>'
        return '<span style="color: #666; font-size: 20px;">₹0 (Error)</span>'

    async def send_email(self, bitla_balance: float, vaagai_balance: float):
        bitla_html = self.get_html_balance("Bitla", bitla_balance)
        vaagai_html = self.get_html_balance("Vaagai", vaagai_balance)
        
        is_low = (bitla_balance <= self.thresholds["Bitla"] or vaagai_balance <= self.thresholds["Vaagai"])
        subject = "🚨 GDS Balance Alert" if is_low else "GDS  Wallet Status"
        
        html_body = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; background: white;">
          <div style="background: linear-gradient(135deg, #0047ff, #1F7BFF, #00C3FF); padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 8px 25px rgba(0,71,255,0.2);">

                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">{('🚨 GDS Balance Alert' if is_low else 'GDS Wallet status')}</h1>
                
            </div>
            
            <div style="background: white; margin: 30px 0; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse;">
                    
                    <thead>
                        <tr style="color: white; background-color: #0047ff;">
                            <th style="padding: 20px 20px; text-align: left; font-size: 18px; font-weight: 600;">Provider</th>
                            <th style="padding: 20px 20px; text-align: center; font-size: 18px; font-weight: 600;">Balance</th>
                            <th style="padding: 20px 20px; text-align: center; font-size: 18px; font-weight: 600;">Threshold</th>
                        </tr>
                    </thead>
                    <tbody style="color: #333;">
                        <tr style="background: white;">
                            <td style="padding: 30px 20px; font-weight: 700; font-size: 18px;">Vaagai</td>
                            <td style="padding: 30px 20px; text-align: center;">{vaagai_html}</td>
                            <td style="padding: 30px 20px; text-align: center; font-weight: 700; font-size: 18px; color: #0047ff;">₹{self.thresholds['Vaagai']:,.0f}</td>
                        </tr>
                        <tr style="background: white;">
                            <td style="padding: 30px 20px; font-weight: 700; font-size: 18px;">Bitla</td>
                            <td style="padding: 30px 20px; text-align: center;">{bitla_html}</td>
                            <td style="padding: 30px 20px; text-align: center; font-weight: 700; font-size: 18px; color: #0047ff;">₹{self.thresholds['Bitla']:,.0f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05); color: #0047ff;">
                <p style="margin: 0 0 5px 0; font-size: 16px; font-weight: 600;">⏰ Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
                <p style="margin: 0; font-size: 14px;">Next update in 3 hours</p>
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
            logger.info(f"OK EMAIL SENT SUCCESSFULLY - {subject}")  # FIXED: No emoji
            return True
        except Exception as e:
            logger.error(f"ERROR EMAIL FAILED - Check Zoho credentials: {e}")
            return False

    async def run_single_check(self):
        """SINGLE RUN - Fetch + Console + Email"""
        print("Fetching LIVE balances...")
        logger.info("=== GDS Balance Check Started ===")
        
        async with aiohttp.ClientSession() as session:
            bitla_task = asyncio.create_task(self.fetch_bitla_balance(session))
            vaagai_task = asyncio.create_task(self.fetch_vaagai_balance(session))
            bitla_balance, vaagai_balance = await asyncio.gather(bitla_task, vaagai_task)
        
        # Console output (your exact format)
        RED, GREEN, RESET = "\033[91m", "\033[92m", "\033[0m"
        bitla_color = f"{RED}₹{bitla_balance:,.0f}{RESET}" if bitla_balance <= self.thresholds["Bitla"] else f"{GREEN}₹{bitla_balance:,.0f}{RESET}"
        vaagai_color = f"{RED}₹{vaagai_balance:,.0f}{RESET}" if vaagai_balance <= self.thresholds["Vaagai"] else f"{GREEN}₹{vaagai_balance:,.0f}{RESET}"
        
        print(f"gds:vaagai,bitla total balance:{vaagai_color},{bitla_color}  threshold balance :{self.thresholds['Vaagai']:,},{self.thresholds['Bitla']:,}")
        logger.info(f"Console: gds:vaagai,bitla total balance:{vaagai_balance:,.0f},{bitla_balance:,.0f}")
        
        # SEND EMAIL
        await self.send_email(bitla_balance, vaagai_balance)
        logger.info("=== GDS Balance Check Completed ===")
        print("Done! Check balance_log.txt for details.")


async def main():
    monitor = BalanceMonitorSingleRun()
    await monitor.run_single_check()


if __name__ == "__main__":
    asyncio.run(main())

