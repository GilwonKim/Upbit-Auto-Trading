import time
import pyupbit
import datetime
import requests

access = "Your upbit access key"
secret = "Your Upbit secret key"
myToken = "Your Slack API"

TargetVolatility = 0.05 #target volatility 5%
NumOfCoins = 1 #number of coins

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

def get_start_time(ticker):
    """get current time"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma5(ticker):
    """review ma5"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_volatility(ticker):
    """volatility of the day"""
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



# log in
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# send starting message
post_message(myToken, "#tradingbot", "AWS ma5 autotrade start")


# start autotrade
while True:
    try:
        now = datetime.datetime.now()
        start_time = now.replace(hour=0, minute=30, second=0, microsecond=0)
        end_time = now.replace(hour=10, minute=0, second=0, microsecond=0)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-DOT", 0.5)
            print("Start Time",start_time)
            print("End Time", end_time)
            print("Target Price",target_price)
            ma5 = get_ma5("KRW-DOT")
            print("ma5",ma5)
            current_price = get_current_price("KRW-DOT")
            print("Current Price",current_price)

            if target_price < current_price and ma5 < current_price:
                krw = get_balance("KRW")
                coins = krw / NumOfCoins
                print("KRW", krw)
                check = get_balance("DOT")
                print("Num of coins", check)
                #volatility = get_volatility("KRW-DOT")
                #print("volatility")
                if check == 0:
                    buy_result = upbit.buy_market_order("KRW-DOT", coins * 0.9995) #TargetVolatility/volatility/NumOfCoins*krw*0.9995
                    check = get_balance("DOT")
                    print("Bought", check)
                    post_message(myToken, "#tradingbot", "DOT buy : " +str(buy_result))
        else:
            sell = get_balance("DOT")
            if sell > 5000/get_current_price("KRW-DOT"):
                sell_result = upbit.sell_market_order("KRW-DOT", sell)
                current_price = get_current_price("KRW-DOT")
                print("DOT sold at",current_price)
                post_message(myToken, "#tradingbot", "DOT sell : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#tradingbot",e)
        time.sleep(1)

