import colorama
import datetime
import ccxt
import json
import pandas as pd
import time
import ta
import os
import ctypes

# Init Modules
colorama.init()
os.system("cls")
ctypes.windll.kernel32.SetConsoleTitleW("ZenTrade by Borane#9999")

# Load Config File
global config
with open("config.json", "r") as cf:
    config = json.load(cf)
    print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Config has been loaded")

exchange = ccxt.ftx({
    'apiKey' : config["apiKey"] ,'secret' : config["secret"] ,'enableRateLimit': True
})

# Load SubAccount
if config["sub_account"] == None:
  print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Get Main Account")
else:
  exchange.headers = {
   'FTX-SUBACCOUNT': config["sub_account"],
  }

# Global Variable Setting
symbol = config["symbol"]
time_limit = config["time_limit"]
order_type = "limit"

# Print All Settings
print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Symbol was set to {symbol}")
print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Looping Time was set to {time_limit}")
print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> EMA1 WINDOW was set to "+str(config["ema"]['EMA1_window']))
print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> EMA2 WINDOW was set to "+str(config["ema"]['EMA2_window']))
if(config["DEBUG"]): print(f"[{colorama.Fore.LIGHTRED_EX}WARN{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Launch to Debug Mod")



def priceHistdata(time):
    data = exchange.fetch_ohlcv(symbol, time)
    data = [[exchange.iso8601(candle[0])] + candle[1:] for candle in data]
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(data, columns=header)
    return df

def getPrice():
  try:
    r1 = json.dumps(exchange.fetch_ticker(symbol))
    dataPrice = json.loads(r1)
  except ccxt.NetworkError as e:
    r1 = json.dumps(exchange.fetch_ticker(symbol))
    dataPrice = json.loads(r1)
  except ccxt.ExchangeError as e:
    r1 = json.dumps(exchange.fetch_ticker(symbol))
    dataPrice = json.loads(r1)
  except Exception as e:
    r1 = json.dumps(exchange.fetch_ticker(symbol))
    dataPrice = json.loads(r1)
  return (dataPrice['last'])

def getCoinBalance():
  for x in exchange.fetchBalance(params = {})["info"]["result"]:
    if(x["coin"] == symbol.split("/")[0]):
      return float(x["total"])
  return 0

def getAmount(price, amount_config):
  if(amount_config != "max"):
    amount = amount_config
    return amount
  else:
    for x in exchange.fetchBalance(params = {})["info"]["result"]:
      if(x["coin"] == symbol.split("/")[1]):
        return float(x["total"])/price
    return 0


# Ema Vars
ema_OpenTransaction = False
ema_BuyPrice = 0
ema_BuyAmount = 0
ema_benef = 0

# Auto Vars
auto_OpenTransaction = False
auto_BuyPrice = 0
auto_BuyAmount = 0

while True:
    print(f"\n[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Looping")
    priceData = priceHistdata(time_limit)
    price = getPrice()

    # Load Indicators
    priceData['EMA1']=ta.trend.ema_indicator(close=priceData['Close'], window=config["ema"]["EMA1_window"])
    priceData['EMA2']=ta.trend.ema_indicator(close=priceData['Close'], window=config["ema"]["EMA2_window"])
    priceData['STOCH_RSI'] = ta.momentum.stochrsi(close=priceData['Close'], window=14, smooth1=3, smooth2=3)


    if(config["auto"] != None):
      if not auto_OpenTransaction and price <= config["auto"]["buy_price"]:
        auto_OpenTransaction = True
        auto_BuyAmount = getAmount(price, config["auto"]["amount"])
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Open Auto Trade with Price = {price} AND Amount = {auto_BuyAmount}")
        if(not config["DEBUG"]): exchange.create_order(symbol, order_type , "buy", auto_BuyAmount, price)

      if auto_OpenTransaction and price >= config["auto"]["sell_price"]:
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Close Auto Trade with Price = {price} WITH Amount = {auto_BuyAmount}")
        auto_OpenTransaction = False
        if(not config["DEBUG"]): exchange.create_order(symbol, order_type , "sell", auto_BuyAmount, price)
      elif auto_OpenTransaction and ((price - auto_BuyPrice) / auto_BuyPrice) * 100 >= config["auto"]["increase_pc"]:
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Close Auto Trade by increase percent with Price = {price} WITH Amount = {ema_BuyAmount}")
        auto_OpenTransaction = False
        if(not config["DEBUG"]):
          if getCoinBalance() > auto_BuyAmount:
            exchange.create_order(symbol, order_type , "sell", auto_BuyAmount, price)
          else:
            exchange.create_order(symbol, order_type , "sell", getCoinBalance(), price)


    if config["ema"] != None:
      if not ema_OpenTransaction and priceData.iloc[-2]['EMA1'] > priceData.iloc[-2]['EMA2'] and priceData.iloc[-2]['STOCH_RSI'] > config["ema"]["STOCH_RSI"]:
        ema_OpenTransaction = True
        ema_BuyPrice = price
        ema_BuyAmount = getAmount(price, config["ema"]["amount"])
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Open Ema Trade with Price = {price} AND Amount = {ema_BuyAmount}")
        if(not config["DEBUG"]): exchange.create_order(symbol, order_type , "buy", ema_BuyAmount, price)

      if ema_OpenTransaction and priceData.iloc[-2]['EMA1'] < priceData.iloc[-2]['EMA2']:
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Close Ema Trade with Price = {price} WITH Amount = {ema_BuyAmount}")
        ema_OpenTransaction = False
        if(not config["DEBUG"]): exchange.create_order(symbol, order_type , "sell", getCoinBalance(), price)
      elif ema_OpenTransaction and config["ema"]["INCREASE_PC"] != None and ((price - ema_BuyPrice) / ema_BuyPrice) * 100 >= config["ema"]["INCREASE_PC"]:
        print(f"[{colorama.Fore.MAGENTA}TRADE{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Close Ema Trade by increase percent with Price = {price} WITH Amount = {ema_BuyAmount}")
        ema_OpenTransaction = False
        if(not config["DEBUG"]):
          if getCoinBalance() > ema_BuyAmount:
            exchange.create_order(symbol, order_type , "sell", ema_BuyAmount, price)
          else:
            exchange.create_order(symbol, order_type , "sell", getCoinBalance(), price)

    if ema_OpenTransaction:
      ema_benef = float(ema_BuyAmount) * float(price) - float(ema_BuyAmount) * float(ema_BuyPrice)

    print(f"[{colorama.Fore.YELLOW}INFO{colorama.Fore.RESET}] [{colorama.Fore.BLUE}{datetime.datetime.now()}{colorama.Fore.RESET}] >> Total benef: {round(ema_benef, 2)}")
    time.sleep(60*5)

'''

Ema1 => Plus Petit
Ema2 => Plus Grand

Ema1 sur Ema2 => Acheter
Ema2 sur Ema1 => Vendre

Strategies:
EMA1 > EMA2 & STOCH_RSI > __VALUE__ => Open
EMA2 > EMA1 => Open

Pivot:
    priceDataPp = priceHistdata("1d")
    priceDataPp['PP'] = (priceDataPp['High']+priceDataPp['Low']+priceDataPp['Close']) / 3
    priceDataPp['R1'] = priceDataPp['PP']+(priceDataPp['PP']-priceDataPp['Low'])
    priceDataPp['S1'] = priceDataPp['PP']-(priceDataPp['High'] - priceDataPp['PP'])
    priceDataPp['R2'] = priceDataPp['PP'] + (priceDataPp['High'] - priceDataPp['Low'])
    priceDataPp['S2'] = priceDataPp['PP'] - (priceDataPp['High'] - priceDataPp['Low'])
    priceDataPp['R3'] = priceDataPp['High'] + 2 * (priceDataPp['PP'] - priceDataPp['Low']) 
    priceDataPp['S3'] = priceDataPp['Low'] - 2 * (priceDataPp['High'] - priceDataPp['PP'])
    

    print(priceDataPp.iloc[-2]['R1'])
    print(priceDataPp.iloc[-2]['S1'])

R => Monte
S => Descend


Si le prix s'approche d'un R genre à 2€ ou 0.8€ près a voir dans la config et puis ressort on le vend si il est un % au dessus du prix d'achat
On peu aussi le desactiver

Si le prix s'approche d'un S genre à 2€ ou 0.8€ près a voir dans la config et puis vérifier qu'il ne remonte pas de 0.001% et si il remonte genre de 1 à 2€ (config) en acheter
On peu aussi le desactiver



A faire:
  Auto Max

'''