from flask import Flask
import re
from requests_html import HTMLSession
import time
import os
from bs4 import BeautifulSoup


# Fill in your details here to be posted to the login form.
payload = {
    'lEmail': 'itswhocaresman@gmail.com',
    'lPass': 'who@123',
    'fbSig': 'web'
}


GOODFUELPRICE = 0.6
GOODCO2PRICE = 0.15

EMERFUEL = 2000000
EMERCO2 = 3500000


# comma seperated numbers
moneyRegex = re.compile(r'\'headerAccount\'>(.*)</span>')
fuelRegex = re.compile(r'\'headerFuel\'>([0-9,]*)</span>')
fuelPriceRegex = re.compile(
    r'Current price</span><br><span class=\'text-danger\'><b>\$ ([0-9,]*)</b></span>')
co2PriceRegex = re.compile(
    r'Quota cost</span><br><span class=\'text-danger\'><b>\$ ([0-9,]*)</b></span>')
co2Regex = re.compile(
    r'<span id=\'holding\' class=\'font-weight-bold text-(success|danger)\'>(-)?([0-9,]*)</span>')
# Use 'with' to ensure the session context is closed after use.

fuelCapacity = 13240000
co2Capacity = 10385000

# maxFuelBuyFor500 = 5608400


def doMaintainance(session):
    # https://www.airlinemanager.com/maint_plan_do.php?type=bulkRepair&id=53079314&mode=do&pct=40&fbSig=false
    res = session.get(
        "https://www.airlinemanager.com/maint_plan_repair_bulk.php?pct=40&fbSig=false")
    a = res.text.find("type=bulkRepair&id=")
    if a != -1:
        matches = re.search(r'type=bulkRepair&id=([0-9]*)', res.text)
        ID = matches.group(1)
        url = f"https://www.airlinemanager.com/maint_plan_do.php?type=bulkRepair&id={ID}&mode=do&pct=40&fbSig=false"
        res2 = session.get(url)
        print("Maintainance done")
        return True
    return False


def checkPending(session):
    res = session.get(
        "https://www.airlinemanager.com/maint_plan_check_bulk.php?undefined&fbSig=false")
    soup = BeautifulSoup(res.text, 'html.parser')
    a = soup.find_all('b', class_='text-danger')
    pending = []
    for i in a:
        temp = i.parent.attrs['data-id']
        temp2 = re.search(r'(\w\w\s\w\w\s\w\w\w\w)', i.parent.text).group(1)
        temp3 = re.search(r'([0-9]*)', i.parent.find('b').text).group(1)
        pending.append({
            "id": temp,
            "name": temp2,
            "hours": temp3
        })
    # print(pending)
    # con = input("Continue? (y/n): ")
    # if con != 'y':
    #     return False
    for fleet in pending:
        res2 = session.get(
            "https://www.airlinemanager.com/maint_plan_check_bulk.php?undefined&fbSig=false")
        ID = re.search(
            r'maint_plan_do.php\?mode=do&id=([0-9]*)', res2.text).group(1)
        print("Fleet sent for A check: ", ID, fleet)
        url = f"https://www.airlinemanager.com/maint_plan_do.php?mode=do&id={ID}&type=check&checkBulk=1&ids={fleet['id']}&fbSig=false"
        res3 = session.get(url)
        if res3.text.find("Error") != -1:
            print("Error")
            return False
        time.sleep(2)
    return True


def buyCO2(session):
    r = session.get('https://www.airlinemanager.com/?gameType=web')
    # extract balance
    balance = int(moneyRegex.search(r.text).group(1).replace(',', ''))
    # get co2 price
    res = session.get("https://www.airlinemanager.com/co2.php?fbSig=false")
    # print(co2Regex.search(res.text).group())
    x = co2Regex.search(res.text)
    if x.group(2) == '-':
        co2 = -1 * int(x.group(3).replace(',', ''))
    else:
        co2 = int(co2Regex.search(res.text).group(3).replace(',', ''))
    co2Price = int(co2PriceRegex.search(res.text).group(1)) / 1000

    # co2Price = 0.125
    if (co2Price <= GOODCO2PRICE and co2 < co2Capacity) or co2 < 1000000:
        amount = EMERCO2
        if co2Price <= GOODCO2PRICE:
            amount = co2Capacity - co2
        if balance - amount * co2Price < 1000000:
            amount = (balance - 1000000) // co2Price
        if amount > 0:
            session.get(
                f"https://www.airlinemanager.com/co2.php?mode=do&amount={amount}&fbSig=false&_={int(time.time())}")
            print(f"Buying {amount} CO2 for {amount * co2Price}")


def buyFuel(s):
    r = s.get('https://www.airlinemanager.com/?gameType=web')
    # extract balance
    balance = int(moneyRegex.search(r.text).group(1).replace(',', ''))

    # extract fuel
    fuel = int(fuelRegex.search(r.text).group(1).replace(',', ''))

    # extract fuel price
    a = s.get("https://www.airlinemanager.com/fuel.php?undefined&fbSig=false")
    fuelPrice = int(fuelPriceRegex.search(
        a.text).group(1).replace(',', '')) / 1000

    if (fuelPrice <= GOODFUELPRICE and fuel < fuelCapacity) or (fuelPrice <= 1.1 and fuel <= 1000000):
        if fuelPrice > GOODFUELPRICE:
            amount = EMERFUEL
            if 0.6 <= fuelPrice <= 0.9:
                amount = int((fuelCapacity - fuel) * 0.60)
        else:
            amount = fuelCapacity - fuel
        if balance - amount * fuelPrice < 1000000:
            amount = (balance - 1000000) // fuelPrice

        if amount > 0:
            print("Buying " + str(amount) +
                  " fuel for " + str(amount * fuelPrice))
            a = s.get(
                f"https://www.airlinemanager.com/fuel.php?mode=do&amount={amount}&fbSig=false&_={int(time.time()*100)}")


def departPlains(s):
    # getCampain(s)
    print("!!! Departing all plains !!!")
    s.get(
        f"https://www.airlinemanager.com/route_depart.php?mode=all&ids=x&fbSig=false&_={int(time.time())}")


# caterSize = {
#     "Dubai, United Arab Emirates": "6962617",
#     "Caracas, Venezuela": "6992139",
#     "Dallas-Fort Worth, United States": "7012340",
#     "London Heathrow Intl, United Kingdom": "7013457",
#     "Addis Ababa, Ethiopia": "7043052",
#     "Phoenix Int, United States": "7045391",
#     "NGTA": "7080905",
#     "SBGR": "7079820",
#     "LOWW": "7156637",
#     "SBBR": "7278739",
#     "EPWA": "7423856",
#     "BKPR": "7492714"
# }
caterSize = {
    "Dubai, United Arab Emirates": ["6962617", 3000],
    "Caracas, Venezuela": ["6992139", 3000],
    "Dallas-Fort Worth, United States": ["7012340", 5000],
    "London Heathrow Intl, United Kingdom": ["7013457", 5000],
    "Addis Ababa, Ethiopia": ["7043052", 2000],
    "Phoenix Int, United States": ["7045391", 5000],
    "NGTA": ["7080905", 10000],
    "SBGR": ["7079820", 10000],
    "LOWW": ["7156637", 10000],
    "SBBR": ["7278739", 5000],
    "EPWA": ["7423856", 10000],
    "BKPR": ["7492714", 5000],
    "FDSK": ["7600524", 5000],
    "LYPG": ["7666150", 5000],
    "FEFF": ["7729322", 5000],
    "KATL": ["7729377", 5000],
    "LQSA": ["7791210", 5000],
    "FYWH": ["7828095", 5000],
    "FBSK": ["7839999", 5000]
}


def orderCatering(s):
    for value in caterSize.values():
        # print(value)
        res = s.get(
            f"https://www.airlinemanager.com/catering.php?mode=do&hub={value[0]}&type=3&amount={value[1]}&duration=24&fbSig=false")
    print("!!! Ordered Catering !!!")


def logData(s):
    r = s.get('https://www.airlinemanager.com/?gameType=web')

    # extract balance
    balance = int(moneyRegex.search(r.text).group(1).replace(',', ''))

    # extract fuel
    fuel = int(fuelRegex.search(r.text).group(1).replace(',', ''))

    a = s.get(
        "https://www.airlinemanager.com/fuel.php?undefined&fbSig=false&_=1686928666887")
    fuelPrice = int(fuelPriceRegex.search(
        a.text).group(1).replace(',', '')) / 1000
    z = s.get("https://www.airlinemanager.com/marketing.php?undefined")
    rep = re.search(r'<div class=\'stars\'>([0-9]*)</div>', z.text).group(1)
    print("Balance: " + str(balance))
    print("Fuel: " + str(fuel))
    print("Fuel Price: " + str(fuelPrice))
    print("Fuel Capacity: " + str(fuelCapacity))
    print("Reputation: " + str(rep))

    res = s.get("https://www.airlinemanager.com/co2.php?fbSig=false")
    # print(co2Regex.search(res.text).group())
    x = co2Regex.search(res.text)
    if x.group(2) == '-':
        co2 = -1 * int(x.group(3).replace(',', ''))
    else:
        co2 = int(co2Regex.search(res.text).group(3).replace(',', ''))
    co2Price = int(co2PriceRegex.search(res.text).group(1)) / 1000

    print(f"CO2: {co2}")
    print(f"CO2 Price: {co2Price}")
    print(f"CO2 Capacity: {co2Capacity}")

# while True:


def getCampain(s):
    return None
    c = "https://www.airlinemanager.com/marketing_new.php?type=1&c=4&mode=do&d=6"
    a = s.get("https://www.airlinemanager.com/marketing_new.php?type=5&mode=do&c=1")
    b = a.text.find("You already have an active campaign")
    if b != -1:
        print("!!! Campain already active !!!")
        return
    else:
        print("!!! Activated Campain !!!")
        # a = s.get(
        #     "https://www.airlinemanager.com/marketing_new.php?type=5&mode=do&fbSig=false&_=" + str(int(time.time())))


def hello_pubsub(event, context):
    with HTMLSession() as s:
        # clear screen
        # os.system('cls')
        try:
            # Login.
            p = s.post(
                'https://www.airlinemanager.com/weblogin/login.php', data=payload)

            # if time is 04:00:00 am
            #if 2 < time.localtime().tm_hour < 6:
            checkPending(s)
            
            doMaintainance(s)

            orderCatering(s)
            buyFuel(s)
            buyCO2(s)
            # depart all plains
            departPlains(s)
            time.sleep(2)
            buyFuel(s)
            buyCO2(s)
            time.sleep(2)
            departPlains(s)

            logData(s)
            return "Done"

        except Exception as e:
            print(e)


# if __name__ == '__main__':
#     hello_pubsub(None, None)
#     # time.sleep(60)


# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)

# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.


@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    return hello_pubsub(None, None)


# main driver function
if __name__ == '__main__':

    # run() method of Flask class runs the application
    # on the local development server.
    app.run()
