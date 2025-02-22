# 📌 Stock Market Discord Bot - ESPI Tracker

<img src="images/espi_bot_logo.png" width="150"/>

## 🔹 What is this bot?
It is a discord bot with a purpose of informing about meaningfull events of tracked Polish stock market comapnies.

## 🔹 Features
✅ Real-Time ESPI Alerts – Tracks new ESPI reports and posts updates.  
✅ Automated Filtering – Only new ESPIs are notified (no duplicates).  
✅ Emoji Representation – Each tracked stock is auto-assigned an emoji (chat gpt generated) for quick recognition.  
✅ Pinned Stock Tracking – Users can add stocks to track with !add <URL>.  
✅ Easy Management – Admins can remove stocks with !remove <URL>.  
✅ Runs 24/7 – Hosted on an AWS EC2 instance for continuous tracking.  

## 🔹 How It Works  
1. Add a Stock to Tracked ESPIs  
  `!add https://biznes.pap.pl/espi/espi/2025?company=1619&selectCompany=1619`  
  🔹 The bot fetches company name and assigns an emoji.  
  🔹 The stock is pinned in the channel for tracking.  
2. Receive ESPI Updates Automatically  
  📢 New ESPI Announcement for Creotech Instruments SA 🛰️  
  🕒 2025-02-21 12:44  
  📌 CREOTECH INSTRUMENTS SA (15/2025) Zamknięcie oferty akcji serii K.  
  🔗 View on ESPI  
  🔹 Only new ESPIs are reported, avoiding spam.  
3. Remove a Stock from Tracking  
  `!remove https://biznes.pap.pl/espi/espi/2025?company=1619&selectCompany=1619`  
  🔹 The stock is removed and unpinned.  

## 🔹 Future Plans  
  - 📊 Stock Price Monitoring (Track real-time price changes).
  - 🔔 Custom Alerts (Set alerts for specific ESPI keywords).
  - 🌎 Expand to US Stocks (Support SEC filings for US markets).
