import time
import pyupbit
import datetime
import requests
import schedule
from fbprophet import Prophet

access = "your access code"
secret = "your secret code"
myToken = "what is your token"

TargetVolatility = 0.05 #target volatility 5%
NumOfCoins = 2 #number of coins

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
    """1일 변동 % 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    volatility = (df.iloc[0]['high'] - df.iloc[0]['low']) / df.iloc[0]['open']
    return volatility



def get_balance(ticker):
    """volatility of the day"""
    balances = upbit.get_balances()

    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """check balance"""
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
predict_price("KRW-ETH")
schedule.every().hour.do(lambda: predict_price("KRW-ETH"))


# log in
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# send starting message
post_message(myToken, "#breakthru", "autotrade start")


# start trading
while True:
    try:
        now = datetime.datetime.now()
        start_time = now.replace(hour=1, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-ETH", 0.5)
            print("Start Time",start_time)
            print("End Time", end_time)
            print("Target Price",target_price)
            current_price = get_current_price("KRW-ETH")
            print("Current Price",current_price)
            print("Predicted Price",predicted_close_price)

            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                coins = krw / NumOfCoins
                print("KRW", krw)
                check = get_balance("ETH")
                print("Num of coins", check)
                #volatility = get_volatility("KRW-ETH")
                #print("volatility")
                if check == 0:
                    buy_result = upbit.buy_market_order("KRW-ETH", coins * 0.9995) #TargetVolatility/volatility/NumOfCoins*krw*0.9995
                    check = get_balance("ETH")
                    print("Bought", check)
                    post_message(myToken, "#breakthru", "ETH buy : " +str(buy_result))
        else:
            sell = get_balance("ETH")
            if sell > 5000/get_current_price("KRW-ETH"):
                sell_result = upbit.sell_market_order("KRW-ETH", sell)
                current_price = get_current_price("KRW-ETH")
                print("ETH sold at",current_price)
                post_message(myToken, "#breakthru", "ETH sell : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#breakthru",e)
        time.sleep(1)

