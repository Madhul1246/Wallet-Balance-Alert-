#!/usr/bin/env python3
"""
GDS Wallet + SMS Balance Monitor - Hopzy (SIMPLEST EMAIL)
"""

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
        self.agent_emails = ["avinash.sk@hopzy.in"]
        self.cc_emails = ["tejus.a@hopzy.in",]
        self.smtp_server = "smtp.zoho.in"
        self.smtp_port = 587
        self.sender_email = "madhu.l@hopzy.in"
        self.sender_password = "JqkGLkfkTf0n"
        self.thresholds = {"EzeeInfo": 5000, "Bitla": 10000, "Vaagai": 5000, "BhashSMS": 5000}
        self.bhashsms_url = "https://bhashsms.com/api/checkbalance.php?user=HOPZYTRANS&pass=123456"

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

    async def fetch_bhashsms_balance(self, session):
        """Handle plain numeric response "103298" correctly"""
        try:
            async with session.get(self.bhashsms_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                logger.info(f"BhashSMS API Status: {resp.status}")
                text = await resp.text()
                logger.info(f"BhashSMS raw response: {text}")
                
                balance_str = text.strip()
                try:
                    balance = float(balance_str)
                    logger.info(f"OK BhashSMS balance: ₹{balance:,.2f}")
                    return balance
                except (ValueError, TypeError):
                    logger.warning(f"BhashSMS invalid balance format: '{balance_str}'")
                    return 0.0
                    
        except Exception as e:
            logger.error(f"ERROR BhashSMS fetch failed: {e}")
            return 0.0

    def get_status_color(self, provider: str, balance: float) -> str:
        threshold = self.thresholds[provider]
        if balance <= threshold and balance > 0:
            return '#dc2626'  # Red
        elif balance > 0:
            return '#059669'  # Green
        return '#6b7280'  # Gray

    async def send_email(self, ezeeinfo_balance: float, bitla_balance: float, vaagai_balance: float, bhashsms_balance: float):
        is_low = any(balance <= self.thresholds[provider] for provider, balance in 
                     [("EzeeInfo", ezeeinfo_balance), ("Bitla", bitla_balance), ("Vaagai", vaagai_balance), ("BhashSMS", bhashsms_balance)] 
                     if balance > 0)
        subject = "🚨 Balance Alert" if is_low else "✅ Wallet Status OK"
        
        # ULTRA SIMPLE HTML EMAIL
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5;">
        
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
             <h2 style="color: {'#dc2626' if is_low else '#059669'}; text-align: center; margin-bottom: 20px;">
                    {('🚨 LOW BALANCE ALERT' if is_low else 'WALLET SUMMARY')}
            </h2>
            <h3 style="color: #059669; margin: 25px 0 15px 0;">SMS Wallet Balance</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Provider</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Current Balance</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Threshold</th>
                    </tr>
                    <tr>
                        <td style="padding: 15px; font-weight: bold;">BhashSMS Credits</td>
                        <td style="padding: 15px; text-align: center; font-size: 20px; font-weight: bold; color: {self.get_status_color('BhashSMS', bhashsms_balance)};">₹{bhashsms_balance:,.0f}</td>
                        <td style="padding: 15px; text-align: center; color: #007bff;">₹{self.thresholds['BhashSMS']:,.0f}</td>
                    </tr>
                </table>
            
                
                <h3 style="color: #059669; margin: 25px 0 15px 0;">GDS Wallets</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Provider</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Current Balance</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Threshold</th>
                    </tr>
                    <tr>
                        <td style="padding: 15px; font-weight: bold;">Bitla</td>
                        <td style="padding: 15px; text-align: center; font-size: 20px; font-weight: bold; color: {self.get_status_color('Bitla', bitla_balance)};">₹{bitla_balance:,.0f}</td>
                        <td style="padding: 15px; text-align: center; color: #007bff;">₹{self.thresholds['Bitla']:,.0f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; font-weight: bold;">Vaagai</td>
                        <td style="padding: 15px; text-align: center; font-size: 20px; font-weight: bold; color: {self.get_status_color('Vaagai', vaagai_balance)};">₹{vaagai_balance:,.0f}</td>
                        <td style="padding: 15px; text-align: center; color: #007bff;">₹{self.thresholds['Vaagai']:,.0f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; font-weight: bold;">EzeeInfo</td>
                        <td style="padding: 15px; text-align: center; font-size: 20px; font-weight: bold; color: {self.get_status_color('EzeeInfo', ezeeinfo_balance)};">₹{ezeeinfo_balance:,.0f}</td>
                        <td style="padding: 15px; text-align: center; color: #007bff;">₹{self.thresholds['EzeeInfo']:,.0f}</td>
                    </tr>
                </table>
                
                
                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center; font-size: 14px; color: #666;">
                    <strong>Last Check:</strong> {datetime.now().strftime('%d %b %Y, %I:%M %p IST')} | Next check in 3 hours
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
        logger.info("=== GDS + SMS Balance Check Started ===")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                asyncio.create_task(self.fetch_ezeeinfo_balance(session)),
                asyncio.create_task(self.fetch_bitla_balance(session)),
                asyncio.create_task(self.fetch_vaagai_balance(session)),
                asyncio.create_task(self.fetch_bhashsms_balance(session))
            ]
            ezeeinfo_balance, bitla_balance, vaagai_balance, bhashsms_balance = await asyncio.gather(*tasks)
        
        RED, GREEN, RESET = "\033[91m", "\033[92m", "\033[0m"
        colors = {}
        for provider, balance in [("EzeeInfo", ezeeinfo_balance), ("Vaagai", vaagai_balance), ("Bitla", bitla_balance), ("BhashSMS", bhashsms_balance)]:
            color = RED if balance <= self.thresholds[provider] else GREEN
            colors[provider] = f"{color}₹{balance:,.0f}{RESET}"
        
        print(f"gds+sms:ezeeinfo,vaagai,bitla,bhashsms total balance:{colors['EzeeInfo']},{colors['Vaagai']},{colors['Bitla']},{colors['BhashSMS']}  threshold:{self.thresholds['EzeeInfo']:,},{self.thresholds['Vaagai']:,},{self.thresholds['Bitla']:,},{self.thresholds['BhashSMS']:,}")
        logger.info(f"Console: ezeeinfo:{ezeeinfo_balance:,.0f}, vaagai:{vaagai_balance:,.0f}, bitla:{bitla_balance:,.0f}, bhashsms:{bhashsms_balance:,.0f}")
        
        await self.send_email(ezeeinfo_balance, bitla_balance, vaagai_balance, bhashsms_balance)
        logger.info("=== GDS + SMS Balance Check Completed ===")
        print("Done! Check balance_log.txt for details.")

async def main():
    monitor = BalanceMonitorSingleRun()
    await monitor.run_single_check()

if __name__ == "__main__":
    asyncio.run(main())
