import time
import pyupbit
import datetime
import requests
import schedule
import re
from fbprophet import Prophet

access = "UPBIT API"
secret = "UPBIT API"
myToken = "Your Slack API"

TargetVolatility = 0.05 #target volatility 5%
CoinBuyList = ["KRW-SOL", "KRW-ETH"]

def post_message(token, channel, text):
    """send messages to Slack"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """breakthorugh price check"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_k(ticker):
    """get k value related to noise""" # 20days average noise to get an optimal k value
    df = pyupbit.get_ohlcv(ticker, interval="day", count=20) #get noise value for 20 days. (notise ratio = 1 - (abs(open-close)/(high-low))
    noise = (1 - abs((df['open']-df['close'])/(df['high']-df['low']))).rolling(20).mean().iloc[-1]
    return noise

def get_start_time(ticker):
    """get current time"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma3(ticker):
    """review ma3"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
    ma3 = df['close'].rolling(3).mean().iloc[-1]
    return ma3

def get_ma5(ticker):
    """review ma5"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_ma10(ticker):
    """review ma10"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=10)
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    return ma10

def get_ma20(ticker):
    """review ma20"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=20)
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    return ma20

def get_volatility(ticker):
    """1 day volatility %"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    volatility = (df.iloc[0]['high'] - df.iloc[0]['low']) / df.iloc[0]['open']
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

predicted_close_price = 0
def predict_price(ticker):
    """forcast the end price with Prophet"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue



# log in
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# send starting message
post_message(myToken, "#breakthru", "VS AI autotrade start")


# start trading
while True:
    try:
        now = datetime.datetime.now()
        start_time = now.replace(hour=19, minute=0, second=0, microsecond=0) #start at 7pm (2022.01.04)
        start_time_mid = now.replace(hour=0, minute=0, second=0, microsecond=0) #start at 0:0am (2022.01.05)
        end_time = start_time_mid.replace(hour=9, minute=0, second=0, microsecond=0) #end at 9:00am (2022.01.05)
        
        krw = get_balance("KRW")
        BuyAmount = krw/len(CoinBuyList)
        schedule.run_pending()

        if start_time < now or start_time_mid < now < end_time - datetime.timedelta(seconds=10):
            for CoinList in CoinBuyList:
                k = get_k(CoinList) #get an optimal k value with 20 days of average noise value
                predict_price(CoinList)
                schedule.every().hour.do(lambda: predict_price(CoinList))
                
                target_price = get_target_price(CoinList, 0.5)
                ma3 = get_ma3(CoinList)
                ma5 = get_ma5(CoinList)
                ma10 = get_ma10(CoinList)
                ma20 = get_ma20(CoinList)
                print("Start Time",start_time)
                print("End Time", end_time)
                print("Target Price",target_price)
                current_price = get_current_price(CoinList)
                print("Current Price",current_price)
                print("Predicted Price",predicted_close_price)

                if target_price < current_price and current_price < predicted_close_price:
                    List = re.sub(r'.', '', CoinList, count = 4) #convert KRW-BTC into BTC to check the coin qty
                    print(List)
                    
                    check = get_balance(List)
                    ScoreMa3 = 0
                    ScoreMa5 = 0
                    ScoreMa10 = 0
                    ScoreMa20 = 0
                    print("Num of coins", check)
                    volatility = get_volatility(CoinList)
                    
                    if ma3 < current_price:
                        ScoreMa3 = 1
                    if ma5 < current_price:
                        ScoreMa5 = 1
                    if ma10 < current_price:
                        ScoreMa10 = 1
                    if ma20 < current_price:
                        ScoreMa20 = 1
                    MaScores = (ScoreMa3 + ScoreMa5 + ScoreMa10 + ScoreMa20) / 4 # divide by 4 represents the number of MA
                    RevisedVolatility = TargetVolatility / volatility * BuyAmount
                    BuyThisAmount = MaScores * RevisedVolatility                        
                        
                    if check == 0:
                        buy_result = upbit.buy_market_order(CoinList, BuyThisAmount * 0.9995)
                        check = get_balance(List)
                        print("Coin bought", check)
                        post_message(myToken, "#breakthru", "Coin buy : " +str(buy_result))
        else:
            for SellCoin in CoinBuyList:
                List = re.sub(r'.', '', SellCoin, count = 4) #convert KRW-BTC into BTC to check the coin qty
                Rich = get_balance(List) #Let us become Rich!
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
