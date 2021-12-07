import time
import pyupbit
import datetime
import requests

access = "sAs0ruRpqYGZPmdSryQs5Aj9xTJG6twiuCdWxcoy"
secret = "IzlKVHxnjNBIbgPrCcfQVLlUW48W7CxejxOtww9E"
myToken = "xoxb-2798363804053-2798367938133-S6rxq5cjJcJh264oXG7ZwrEf"

TargetVolatility = 0.05 #타겟 변동성 5%
NumOfCoins = 1 #코인 개수

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
print("autotrade start")

#시작 메세지 슬랙 전송
post_message(myToken, "#breakthrough", "autotrade start")


# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-SOL") #9:00
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=13): #원래 (seconds=10) 였음. 나는 정오 팔기 원해서 hours=12로 구현
            target_price = get_target_price("KRW-SOL", 0.5)
            #print("Target Price",target_price)
            ma5 = get_ma5("KRW-SOL")
            #print("ma5",ma5)
            current_price = get_current_price("KRW-SOL")
            #print("Current Price",current_price)
            if target_price < current_price and ma5 < current_price:
                krw = get_balance("KRW")
                #print(krw)
                volatility = get_volatility("KRW-SOL")
                #print("volatility")
                if krw > 5000:
                    buy_result = upbit.buy_market_order("KRW-SOL", TargetVolatility/volatility/NumOfCoins*krw*0.9995)
                    post_message(myToken, "#breakthrough", "SOL buy : " +str(buy_result))
        else:
            sol = get_balance("SOL")
            if sol > 0.01:
                sell_result = upbit.sell_market_order("KRW-SOL", sol*0.9995)
                post_message(myToken, "#breakthrough", "SOL buy : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#breakthrough",e)
        time.sleep(1)