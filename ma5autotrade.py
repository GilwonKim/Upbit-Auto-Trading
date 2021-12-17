import time
import pyupbit
import datetime
import requests

access = "your access code"
secret = "your secret code"
myToken = "what is your token"

TargetVolatility = 0.05 #target volatility 5%
NumOfCoins = 2 #number of coins

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_volatility(ticker):
    """1일 변동 % 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    volatility = (df.iloc[0]['high'] - df.iloc[0]['low']) / df.iloc[0]['open']
    return volatility



def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()

    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("ma5 autotrade start")

#시작 메세지 슬랙 전송
post_message(myToken, "#breakthru", "ma5 autotrade start")


# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time_1 = get_start_time("KRW-OMG")
        start_time = start_time_1 - datetime.timedelta(hours=8)  #새벽 1시에 매수 시작
        end_time = start_time_1 + datetime.timedelta(day=1) # 오전 9시에 매도
        

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-OMG", 0.5)
            print("Start Time",start_time)
            print("End Time", end_time)
            print("Target Price",target_price)
            ma5 = get_ma5("KRW-OMG")
            print("ma5",ma5)
            current_price = get_current_price("KRW-OMG")
            print("Current Price",current_price)

            if target_price < current_price and ma5 < current_price:
                krw = get_balance("KRW")
                coins = krw / NumOfCoins
                print("krw")
                #volatility = get_volatility("KRW-OMG")
                #print("volatility")
                if krw > 5000:
                    buy_result = upbit.buy_market_order("KRW-OMG", coins * 0.9995)
                    post_message(myToken, "#breakthru", "OMG buy : " +str(buy_result))
        else:
            omg = get_balance("OMG")
            if omg > 5000/get_current_price("KRW-OMG"):
                sell_result = upbit.sell_market_order("KRW-OMG", omg)
                post_message(myToken, "#breakthru", "OMG sell : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#breakthru",e)
        time.sleep(1)

