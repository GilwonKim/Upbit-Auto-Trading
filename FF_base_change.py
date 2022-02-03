import time
import pyupbit
import datetime
import requests
import re

access = "Your Upbit Acess Key"
secret = "Your Upbit Secret Key"
myToken = "Your Slack API token"


TargetVolatility = 0.05 #chose your target volatility as 5%
CoinBuyList = ["KRW-GAS"] #chose your ticker as many as you want


def get_daily_ohlcv_from_base_new(ticker="KRW-BTC", base=0): #base time change fuction
    """
    :param ticker:
    :param base:
    :return:
    """
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute60", count=480) #count 480 brings 20 days of data
        df = df.resample('24H', base=base).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        return df
    except Exception as x:
        return None    




def post_message(token, channel, text):
    """send messages to Slack"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """breakthorugh price check"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    target_price = df.iloc[-2]['close'] + (df.iloc[-2]['high'] - df.iloc[-2]['low']) * k #get value from the second last iloc[-2]
    return target_price

def get_noise_k(ticker):
    """get k value related to noise""" # 20days average noise to get an optimal k value
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #chage your base time to 1:00am
    noise = (1 - abs((df['open']-df['close'])/(df['high']-df['low']))).rolling(20).mean().iloc[-1] #noise ratio = 1 - (abs(open-close)/(high-low))
    return noise

def get_start_time(ticker):
    """get current time"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    start_time = df.index[0]
    return start_time

def get_ma3(ticker):
    """review ma3"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    ma3 = df['close'].rolling(3).mean().iloc[-1] #iloc[-1] gets you the very last row value
    return ma3

def get_ma5(ticker):
    """review ma5"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_ma10(ticker):
    """review ma10"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    return ma10

def get_ma20(ticker):
    """review ma20"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    return ma20

def get_volatility(ticker):
    """volatility of the day"""
    df = get_daily_ohlcv_from_base_new(ticker, base=7) #change your base time to 1:00am
    volatility = (df.iloc[-1]['high'] - df.iloc[-1]['low']) / df.iloc[-1]['open']
    return volatility



def get_balance(ticker):
    """check balance"""
    balances = upbit.get_balances()

    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """current price"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]



# log in
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# send starting message
post_message(myToken, "#breakthru", "VS ma5 autotrade start") #change "breakthru" into your Slack API channel name


# start autotrade
while True:
    try:
        now = datetime.datetime.now()
        start_time = now.replace(hour=19, minute=0, second=0, microsecond=0) #start at 7:00pm (2022.01.30)
        start_time_mid = now.replace(hour=0, minute=0, second=0, microsecond=0) #start at 0:0am (2022.01.05)
        end_time = start_time_mid.replace(hour=7, minute=1, second=0, microsecond=0) #sell everything at 7:01am (2022.01.31)

        krw = get_balance("KRW")
        BuyAmount = krw/len(CoinBuyList)

        if start_time < now or start_time_mid < now < end_time - datetime.timedelta(seconds=10):
            for CoinList in CoinBuyList:
                k = get_noise_k(CoinList) #get an optimal k value from noise value
                target_price = get_target_price(CoinList, k)
                ma3 = get_ma3(CoinList)
                ma5 = get_ma5(CoinList)
                ma10 = get_ma10(CoinList)
                ma20 = get_ma20(CoinList)
                current_price = get_current_price(CoinList)

                print("k", k)
                print("target price", target_price)
                print("ma3", ma3)
                print("ma5", ma5)
                print("ma10", ma10)
                print("ma20", ma20)


                if target_price < current_price:
                    List = re.sub(r'.', '', CoinList, count = 4) #convert KRW-BTC into BTC to check the coin qty

                    check = get_balance(List)
                    ScoreMa3 = 0
                    ScoreMa5 = 0
                    ScoreMa10 = 0
                    ScoreMa20 = 0
                    volatility = get_volatility(CoinList)
                    if ma3 < current_price:
                        ScoreMa3 = 1
                    if ma5 < current_price:
                        ScoreMa5 = 1
                    if ma10 < current_price:
                        ScoreMa10 = 1
                    if ma20 < current_price:
                        ScoreMa20 = 1

                    MaScores = (ScoreMa3 + ScoreMa5 + ScoreMa10 + ScoreMa20) / 4 # divide by 4 represents the number of MAs
                    RevisedVolatility = TargetVolatility / volatility * BuyAmount
                    BuyThisAmount = MaScores * RevisedVolatility

                    print("MaScores", MaScores)
                    print("Revised Volatility", RevisedVolatility)
                    print("Buy This Amount", BuyThisAmount)
                    
                    if check == 0:
                        buy_result = upbit.buy_market_order(CoinList, BuyThisAmount * 0.9995)
                        check = get_balance(List)
                        print("Coin bought", check)
                        post_message(myToken, "#breakthru", "Coin buy : " +str(buy_result))
        else:
            for SellCoin in CoinBuyList:
                List = re.sub(r'.', '', SellCoin, count = 4) #convert KRW-BTC into BTC to check the coin qty
                Rich = get_balance(List) #become Rich!
                if Rich > 5000/get_current_price(SellCoin):
                    sell_result = upbit.sell_market_order(SellCoin, Rich)
                    current_price = get_current_price(SellCoin)
                    print("Coin sold at",current_price)
                    post_message(myToken, "#breakthru", "Coin sell : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#breakthru",e)
        time.sleep(1)
