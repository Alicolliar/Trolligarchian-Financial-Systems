from flask import Flask, render_template, request, redirect, url_for, session
import requests
import pymysql as sql
import threading
from random import uniform
from datetime import datetime, date
from randomFunctions import *
db = sql.connect(
    host="###database_host###",
    user="###database_user###",
    password="###database_password###",
    db="###database_name###")
app = Flask(__name__)
app.secret_key = "###SECRET_KEY###"
authParams = {"Authorization":"###YOUR_UNBELIEV_KEY###"}
rates = {
    "capGainTax":20,
    "interest":3.5,
    "transact":32
}

def holdRetrieve(uID):
    query = "SELECT ticker, quant FROM holdings WHERE uID = '"+str(uID)+"';"
    totVal = 0
    with db.cursor() as cursor:
        cursor.execute(query)
        holds = cursor.fetchall()
        holds = list(holds)
        holds = [list(ele) for ele in holds]
        print(holds)
        for i in holds:
            tickBoi = i[0]
            repetQuery = "SELECT curPrice FROM stocks WHERE ticker = '"+str(tickBoi)+"';"
            cursor.execute(repetQuery)
            price = cursor.fetchone()
            price = price[0]
            i.append(price)
            fullPrice = (price * int(i[1]))
            i.append(fullPrice)
            totVal += fullPrice
        totVal = round(totVal, 2)
        cursor.close()
    return holds, totVal

@app.route('/')
def home():
    totalVal = 0
    query = "SELECT curPrice, tradeableVolume, totalVolume FROM stocks;"
    accQuery = "SELECT SUM(balance) FROM accounts WHERE offshore = 0;"
    #query2 = "SELECT SUM(buyValue) FROM bonds;"
    with db.cursor() as cursor:
        cursor.execute(query)
        dataS = cursor.fetchall()
        cursor.execute(accQuery)
        dataA = cursor.fetchone()
        #cursor.execute(query2)
        #dataB = cursor.fetchone()
        #bondTot = dataB[0]
        accTot = dataA[0]
    for dat in dataS:
        boughtVol = dat[2] - dat[1]
        totVal = boughtVol * dat[0]
        totalVal += totVal
    totalVal = round(totalVal, 0)
    message = "The British Virgin Islands can now be found over in the Accounts section. Enjoy"
    return render_template("home.html", message=message, valS=totalVal, valB=accTot)

@app.route('/stocklookup', methods=['GET', 'POST'])
def lookup():
    if request.method == "POST":
        stuff = request.form
        metric = stuff["metric"]
        data = stuff["value"]
        print(metric)
        if metric == "ticker":
            query = "SELECT * FROM stocks WHERE ticker = %s"
        elif metric == "priceg":
            query = "SELECT * FROM stocks WHERE curPrice >= %s;"
        elif metric == "pricel":
            query = "SELECT * FROM stocks WHERE curPrice <= %s;"
        elif metric == "voll":
            query = "SELECT * FROM stocks WHERE tradeableVolume <= %s;"
        else:
            query = "SELECT * FROM stocks WHERE tradeableVolume >= %s;"
        with db.cursor() as cursor:
            cursor.execute(query, data)
            db.commit()
            foundStuff = cursor.fetchall()
            cursor.close()
        print(foundStuff)
        return render_template("stocks/tickerLookup.html", datas=foundStuff)
    return render_template("stocks/tickerLookup.html")

@app.route('/stocklogin', methods=['GET', 'POST']) ##DONE FOR NOW
def stocklogin():
    if 'uName' in session:
        return redirect(url_for("trading"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, discID, perms FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
            print(gubbins)
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username, please try again")
        if pword == gubbins[1]:
            session['uName'] = uname
            session['uID'] = gubbins[0]
            session['discID'] = gubbins[2]
            session['accType'] = gubbins[3]
            return redirect(url_for("trading"))
    return render_template("login.html")

@app.route('/stockTrade', methods=['GET', 'POST'])
def trading():
    if 'uName' not in session:
        redirect(url_for("stocklogin"))
    if request. method == 'POST':
        order = request.form
        stock = order["ticker"]
        quant = order["numStock"]
        discID = session['discID']
        type = order["tType"]
        uName = session['uID']
        accType = session['accType']
        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
        runningURL = ("https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID))
        cursor = db.cursor()
        query1 = "SELECT curPrice, tradeableVolume, totalVolume FROM stocks WHERE ticker = %s"
        query15 = "SELECT hID, quant FROM holdings WHERE ticker = '"+str(stock)+"' AND uID = "+str(uName)+";"
        cursor.execute(query1, stock)
        price = cursor.fetchone()
        cursor.execute(query15)
        help = cursor.fetchone()
        if not price:
            note = "No stock with that ticker."
            return render_template("stocks/tradePage.html", notif=note)
        if type == "Buy":
            if float(price[1]) < float(quant):
                note = "Volume is too low."
                return render_template("stocks/tradePage.html", notif=note)
            preVAT = float(price[0]) * float(quant)
            postVAT = round(preVAT * (1+(rates["capGainTax"]/10)), 2)
            vat = round((preVAT*(rates["transact"]/10)), 0)
            if accType != 2:
                yourBal = requests.get(runningURL, headers=authParams)
                yourBal = yourBal.json()
                bal = yourBal['total']
                if postVAT > bal:
                    return render_template("tradePage.html", notif="You do not have the requisite balance. Please select a different volume.")
            priceforFire = (0-postVAT)
            dataRish = {'cash': vat, 'bank': 0}
            data1 = {'cash': 0, 'bank': priceforFire}
            newVol = int(price[1]) - int(quant)
            priceAdj = int(price[0])*(int(quant)/int(price[2]))
            newPrice = price[0] + priceAdj
            if help:
                updatQuant = int(quant)+int(help[1])
                query4 = "UPDATE holdings SET quant = "+str(updatQuant)+" WHERE hID = "+str(help[0])+";"
            else:
                query4 = "INSERT INTO holdings (uID, ticker, quant) VALUES('"+str(uName)+"', '"+str(stock)+"', "+str(quant)+");"
            query2 = "INSERT INTO orders (uID, ticker, price, numStock, priceperVAT, totalPrice, orderType) VALUES ('"+str(uName)+"', '"+stock+"', '"+str(price[0])+"', '"+quant+"', '"+str(preVAT)+"', '"+str(postVAT)+"', 'Buy');"
            query3 = "UPDATE stocks SET tradeableVolume = "+str(newVol)+", curPrice = "+str(newPrice)+" WHERE ticker = '"+stock+"';"
            notification = (str(uName)+" has purchased "+str(quant)+" of "+stock+" at £"+str(price[0])+" giving a total of £"+str(postVAT)+", including all tax.")
            rishi = requests.patch(rishiURL, headers=authParams, json=dataRish)
        else:
            if float(quant) > float(price[1]):
                note = "Volume is too high."
                return render_template("stocks/tradePage.html", notif=note)
            if int(help[1]) < int(quant):
                notif = "You don't own this many stock."
                return render_template("stocks/tradePage.html", notif=notif)
            preVAT = float(price[0]) * float(quant)
            postVAT = round((preVAT * 1.05), 2)
            vat = 1*round((preVAT*0.05), 0)
            priceforFire = (postVAT)
            dataRish = {'cash': vat, 'bank': 0}
            data1 = {'cash': 0, 'bank': priceforFire}
            newVol = int(price[1]) + int(quant)
            priceAdj = int(price[0])*(int(quant)/int(price[2]))
            newPrice = price[0] - priceAdj
            updatQuant = int(help[1])-int(quant)
            if updatQuant > 0:
                query4 = "UPDATE holdings SET quant = "+str(updatQuant)+" WHERE hID = "+str(help[0])+";"
            else:
                query4 = "DELETE FROM holdings WHERE hID = "+str(help[0])+";"
            query2 = "INSERT INTO orders (uID, ticker, price, numStock, priceperVAT, totalPrice, orderType) VALUES ('"+str(uName)+"', '"+stock+"', '"+str(price[0])+"', '"+quant+"', '"+str(preVAT)+"', '"+str(postVAT)+"', 'Sell');"
            query3 = "UPDATE stocks SET tradeableVolume = "+str(newVol)+", curPrice = "+str(newPrice)+" WHERE ticker = '"+stock+"';"
            notification = str(uName)+" has sold "+str(quant)+" of "+stock+" at £"+str(price[0])+" giving a total of £"+str(postVAT)+", including all tax."
            rishi = requests.patch(rishiURL, headers=authParams, json=dataRish)
        cursor.execute(query2)
        cursor.execute(query3)
        cursor.execute(query4)
        print(uName)
        if accType != 2:
            running = requests.patch(runningURL, headers=authParams, json=data1)
        else:
            accFindQ = "SELECT accID, balance, frozen FROM accounts WHERE uID = '"+str(uName)+"';"
            cursor.execute(accFindQ)
            account = cursor.fetchone()
            print(account)
            if account[2] == 1:
                return render_template("stocks/tradePage.html", notif="Account frozen")
            if type == "Buy":
                newBal = account[1] - float(postVAT)
            else:
                newBal = account[1] + float(postVAT)
            if newBal < 0:
                return render_template("stocks/tradePage.html", notif="You do not have the requisite balance.")
            balUpdateQuery = "UPDATE accounts SET balance = '"+str(newBal)+"' WHERE accID = '"+str(account[0])+"';"
            cursor.execute(balUpdateQuery)
        db.commit()
        cursor.close()
        return render_template("stocks/tradePage.html", notif=notification)
    return render_template("stocks/tradePage.html")

@app.route('/holdLogin', methods=['GET', 'POST']) ##DONE FOR NOW
def holdingsLogin():
    if 'uName' in session or 'adminP' in session:
        return redirect(url_for("holdings"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, discID, perms FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
            print(gubbins)
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username, please try again")
        if pword == gubbins[1]:
            session['uName'] = uname
            session['uID'] = gubbins[0]
            session['discID'] = gubbins[2]
            session['accType'] = gubbins[3]
            return redirect(url_for("holdings"))
    return render_template("login.html")

@app.route('/personalHoldings', methods=['GET', 'POST'])
def holdings():
    if 'uName' not in session and 'adminP' not in session:
        return redirect(url_for("holdingsLogin"))
    if request.method == 'POST':
        user = request.form
        uName = user['uName']
        cursor = db.cursor()
        query = "SELECT uID FROM users WHERE uName = '"+str(uName)+"';"
        cursor.execute(query)
        uID = cursor.fetchone()
        uID = uID[0]
        holds, totVal = holdRetrieve(uID)
    else:
        uID = session['uID']
        user = session["uName"]
        holds, totVal = holdRetrieve(uID)
    return render_template("stocks/holdingsView.html", holds=holds, users=user, valTot=totVal)

@app.route('/bondCalculator', methods=['GET', 'POST'])
def bondCalc():
    if request.method == 'POST':
        dats = request.form
        endVal = int(dats['endVal'])
        period = int(dats['period'])
        rate = float(dats['rate'])
        uhuh = endVal/((1+(rate/100))**period)
        return render_template("bonds/bondCalculator.html", result=round(uhuh,2))
    return render_template("bonds/bondCalculator.html")

@app.route('/bondLogin', methods=['GET', 'POST'])
def locked5():
    return render_template("shuttered.html")
def bondingLogin():
    if 'uName' in session or 'adminP' in session:
        return redirect(url_for("bondTrades"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, discID FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
            print(gubbins)
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username, please try again")
        if pword == gubbins[1]:
            session['uName'] = uname
            session['uID'] = gubbins[0]
            session['discID'] = gubbins[2]
            return redirect(url_for("bondTrades"))
    return render_template("login.html")

@app.route('/bondTrading', methods=['GET', 'POST'])
def locked4():
    return render_template("shuttered.html")
def bondTrades():
    if 'uName' not in session and 'adminP' not in session:
        return redirect(url_for("bondingLogin"))
    if request.method == 'POST':
        data = request.form
        uID = session['uID']
        val = float(data['endVal'])
        matureDate = data['matureDate']
        discID = session['discID']
        now = datetime.now()
        startDate = now.date()
        matureCalc = datetime.strptime(matureDate, "%Y-%m-%d").date()
        startString = now.strftime("%Y-%m-%d")
        periods = (((matureCalc-startDate).days)/7)
        rate = float(rates["interest"])
        uhuh = val/((1+(rate/100))**periods)
        uPrice = 0-uhuh
        query = "INSERT INTO bonds (uID, buyDate, maturityDate, buyValue, fullValue) VALUES ('"+str(uID)+"', '"+str(startString)+"', '"+str(matureDate)+"', '"+str(round(uhuh,2))+"', '"+str(round(val,2))+"');"
        jsonU = {'cash': 0, 'bank':uPrice}
        jsonRishi = {'cash': uhuh, 'bank': 0}
        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
        runningURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
        rishi = requests.patch(rishiURL, headers=authParams, json=jsonRishi)
        running = requests.patch(runningURL, headers=authParams, json=jsonU)
        with db.cursor() as cursor:
            cursor.execute(query)
            db.commit()
            cursor.close()
        return render_template("bonds/bondTrade.html", notif="Bond Purchased")
    return render_template("bonds/bondTrade.html")

@app.route('/bondHoldLogin', methods=['GET', 'POST'])
def locked3():
    return render_template("shuttered.html")
def bondingHoldLogin():
    if 'uName' in session or 'adminP' in session:
        return redirect(url_for("bondTrades"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, discID FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
            print(gubbins)
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username, please try again")
        if pword == gubbins[1]:
            session['uName'] = uname
            session['uID'] = gubbins[0]
            session['discID'] = gubbins[2]
            return redirect(url_for("bondHolds"))
    return render_template("login.html")

@app.route('/bondHoldings', methods=['GET', 'POST'])
def locked2():
    return render_template("shuttered.html")
def bondLads():
    if 'uName' not in session and 'adminP' not in session:
        return redirect(url_for("holdingsLogin"))
    uID = session['uID']
    user = session["uName"]
    discID = session["discID"]
    query = "SELECT bondID, maturityDate, fullValue, buyValue FROM bonds WHERE uID = '"+str(uID)+"';"
    cursor = db.cursor()
    cursor.execute(query)
    bonds = cursor.fetchall()
    if request.method == 'POST':
        bondID = request.form['sell']
        print(bondID)
        for i in bonds:
            if i[0] == bondID:
                 bond = i
        query = "DELETE FROM bonds WHERE bondID = '"+str(bondID)+"';"
        rish = 0-i[3]
        dataU = {'cash':0, 'bank': i[3]}
        dataR = {'cash': rish, 'bank': 0}
        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
        runningURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
        rishi = requests.patch(rishiURL, headers=authParams, json=dataR)
        running = requests.patch(runningURL, headers=authParams, json=dataU)
        with db.cursor() as cursor:
            cursor.execute(query)
            db.commit()
    cursor.close()
    return render_template("bonds/bondHoldings.html", holds=bonds, users=user)

@app.route('/accountsLogin', methods=['GET', 'POST'])
def accountHolding():
    if 'uName' in session or 'adminP' in session:
        return redirect(url_for("accounting"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, discID, perms FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
            print(gubbins)
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username, please try again")
        if pword == gubbins[1]:
            session['uName'] = uname
            session['uID'] = gubbins[0]
            session['discID'] = gubbins[2]
            session['accType'] = gubbins[3]
            return redirect(url_for("accounting"))
    return render_template("login.html")

@app.route('/offAccounts', methods=['GET', 'POST'])
def accounting():
    if 'uName' not in session and 'adminP' not in session:
        return redirect(url_for("accountHolding"))
    uID = session['uID']
    discID = session['discID']
    query = "SELECT accID, accName, balance, offshore, frozen FROM accounts WHERE uID = '"+str(uID)+"';"
    cursor = db.cursor()
    cursor.execute(query)
    accounts = cursor.fetchall()
    if len(accounts) == 0:
        return render_template("accounts.html")
    accDats = []
    for account in accounts:
        accDat = []
        accDat.append(account[1])
        accDat.append(account[2])
        if account[3] == 1:
            accDat.append("Offshore")
        else:
            accDat.append("Local")
        accDats.append(accDat)
    if request.method == 'POST':
        formGuff = request.form
        if "newAcc" in formGuff:
            newName = formGuff["accName"]
            type = formGuff["type"]
            query = "SELECT accName FROM accounts;"
            cursor.execute(query)
            aAccounts = cursor.fetchall()
            if newName in aAccounts:
                return render_template("accounts.html", dets=accDats, failNotif="Account name already reserved.")
            if type == "Offshore":
                typeInt = 1
            else:
                typeInt = 0
            query2 = "INSERT INTO accounts (uID, accName, balance, offshore, frozen) VALUES ('"+str(uID)+"', '"+str(newName)+"', '0', '"+str(typeInt)+"', '0');"
            cursor.execute(query2)
            db.commit()
            return render_template("accounts.html", sucNotif=(str(newName)+" created."))
        elif "transfer" in formGuff:
            transFrom = formGuff["acctFrom"]
            transTo = formGuff["acctTo"]
            transBal = formGuff["transBal"]
            discID = session["discID"]
            fromCheck = checkInput(transFrom)
            toCheck = checkInput(transTo)
            with db.cursor() as cursor:
                if fromCheck == False:
                    queryFrom = "SELECT accID, balance, offshore, frozen FROM accounts WHERE accName = '"+str(transFrom)+"' AND uID = '"+str(uID)+"';"
                    cursor.execute(queryFrom)
                    fromAccount = cursor.fetchone()
                    print(fromAccount)
                    if not fromAccount:
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif="No accounts to transfer from")
                    fromID = fromAccount[0]
                    fromBal = fromAccount[1]
                    if fromAccount[3] == 1:
                        frozen = str(transFrom)+" has been frozen. Please contact the government if you believe this is a mistake."
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif=frozen)
                    if int(transBal) > int(fromBal):
                        inSuf = str(transFrom)+" has insufficient funds."
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif=inSuf)
                else:
                    runURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
                    uBal = requests.get(runURL, headers=authParams)
                    uBal = uBal.json()
                    bal = uBal['total']
                    if int(transBal) > int(bal):
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif="Not enough cash in bank to transfer")
                if toCheck == False:
                    queryTo = "SELECT accID, balance, offshore, frozen FROM accounts WHERE accName = '"+str(transTo)+"';"
                    cursor.execute(queryTo)
                    toAccount = cursor.fetchone()
                    toBal = toAccount[1]
                    if not toAccount:
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif="No account to transfer to")
                    if toAccount[3] == 1:
                        frozen = str(transTo)+" has been frozen. Please contact the government if you believe this is a mistake."
                        cursor.close()
                        return render_template("accounts.html", dets=accDats, failNotif=frozen)
                if fromCheck == False and toCheck == False:
                    if fromAccount[2] == 1 or toAccount[2] == 1:
                        transBal = float(transBal) * (1-(rates["transact"]/100))
                        rishiBal = float(transBal) * (rates["transact"]/100)
                        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
                        rishiJ = {"cash" : rishiBal, "bank": 0}
                        requests.patch(rishiURL, headers=authParams, json=rishiJ)
                    print(transBal)
                    print(toAccount)
                    fromNew = (float(fromBal)-float(transBal))
                    toNew = (float(toBal)+float(transBal))
                    print(str(toNew), str(fromNew))
                    fromQuery = "UPDATE accounts SET balance = '"+str(fromNew)+"' WHERE accID = '"+str(fromAccount[0])+"';"
                    toQuery = "UPDATE accounts SET balance ='"+str(toNew)+"' WHERE accID = '"+str(toAccount[0])+"';"
                    print(fromQuery)
                    print(toQuery)
                    cursor.execute(fromQuery)
                    cursor.execute(toQuery)
                    db.commit()
                    cursor.close()
                    return render_template("accounts.html", dets=accDats, sucNotif="Transfer Complete")
                elif fromCheck == True and toCheck == False:
                    if toAccount[2] == 1:
                        transBal = transBal * (1-(rates["transact"]/100))
                        rishiBal = transBal * (rates["transact"]/100)
                        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
                        rishiJ = {"cash" : rishiBal, "bank": 0}
                        requests.patch(rishiURL, headers=authParams, json=rishiJ)
                    usrBal = (0-float(transBal))
                    fromURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
                    transBal = (0-int(transBal))
                    fromJSON = {"cash": 0, "bank": str(usrBal)}
                    toBal = (float(toBal)-float(transBal))
                    toQuery = "UPDATE accounts SET balance = '"+str(toBal)+"' WHERE accID = '"+str(toAccount[0])+"';"
                    requests.patch(fromURL, headers=authParams, json=fromJSON)
                    cursor.execute(toQuery)
                    db.commit()
                    cursor.close()
                    return render_template("accounts.html", dets=accDats, sucNotif="Transfer Complete")
                elif fromCheck == False and toCheck == True:
                    if fromAccount[2] == 1:
                        transBal = transBal * (1-(rates["transact"]/100))
                        rishiBal = transBal * (rates["transact"]/100)
                        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
                        rishiJ = {"cash" : rishiBal, "bank": 0}
                        requests.patch(rishiURL, headers=autParams, json=rishiJ)
                    else:
                        accBalChan = transBal
                        toBal = transBal
                    toURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
                    toJSON = {"cash": 0, "bank": transBal}
                    fromBal = (float(fromBal)-float(accBalChan))
                    fromQuery = "UPDATE accounts SET balance = '"+str(fromBal)+"' WHERE accID = '"+str(accID)+"';"
                    requests.patch(toURL, headers=authParams, json=toJSON)
                    requests.patch(rishiURL, headers=authParams, json=rishiJ)
                    cursor.execute(toQuery)
                    db.commit()
                    cursor.close()
                    return render_template("accounts.html", dets=accDats, sucNotif="Transfer Complete")
                else:
                    return render_template("accounts.html", dets=accDats, failNotif="Can not transfer between your own personal account")
        elif "delete" in formGuff:
            accDel = formGuff["accDel"]
            findQuery = "SELECT uID, balance FROM accounts WHERE accName = '"+str(accDel)+"';"
            delQuery = "DELETE FROM accounts WHERE accName = '"+str(accDel)+"';"
            with db.cursor() as cursor:
                cursor.execute(findQuery)
                finds = cursor.fetchone()
                print(finds)
                if finds[1] > 0:
                    return render_template("accounts.html", dets=accDats, failNotif="Can not delete account with more than £0")
                cursor.execute(delQuery)
                db.commit()
                return render_template("accounts.html", dets=accDats, notif=str(accDel)+" deleted.")
    return render_template("accounts.html", dets=accDats)

@app.route('/accountSearch', methods=['GET', 'POST'])
def accSearch():
    if request.method == "POST":
        data = request.form
        uName = data["searchTerm"]
        if 'adminP' in session:
            query = query = "SELECT accounts.accName, accounts.balance, accounts.offshore, accounts.offshore FROM users, accounts WHERE accounts.uID = users.uID AND users.uName = '"+str(uName)+"';"
        else:
            query = "SELECT accounts.accName, accounts.balance, accounts.offshore, accounts.offshore FROM users, accounts WHERE accounts.uID = users.uID AND users.uName = '"+str(uName)+"' AND accounts.offshore = '0';"
        with db.cursor() as cursor:
            cursor.execute(query)
            accts = cursor.fetchall()
            if len(accts) == 0:
                return render_template("accountSearch.html")
            nuAccts = []
            for acct in accts:
                nuacct = []
                nuacct.append(acct[0])
                nuacct.append(acct[1])
                if acct[2] == 0:
                    nuacct.append("Local")
                else:
                    nuacct.append("Offshore")
                if acct[3] == 1:
                    nuacct.append("Yes!")
                else:
                    nuacct.append("No")
                nuAccts.append(nuacct)
        return render_template("accountSearch.html", accts=nuAccts)
    return render_template("accountSearch.html")

@app.route('/adLogin', methods=['GET', 'POST']) ##DONE FOR NOW
def adminlogin():
    if 'adminP' in session:
        return redirect(url_for("adminPans"))
    if request.method == "POST":
        data = request.form
        uname = data["uname"]
        pword = data["pwd"]
        query = "SELECT uID, pWord, perms, discID FROM users WHERE uName = %s"
        with db.cursor() as cursor:
            cursor.execute(query, uname)
            db.commit()
            gubbins = cursor.fetchone()
            cursor.close()
        if not gubbins:
            return render_template("login.html", errMess="Incorrect Username")
        if pword == gubbins[1]:
            if gubbins[2] == 1:
                session['uName'] = uname
                session['uID'] = gubbins[0]
                session['adminP'] = 1
                session['discID'] = gubbins[3]
                return redirect(url_for("adminPans"))
            else:
                return render_template("login.html", errMess="Incorrect Permissions")
        else:
            return render_template("login.html", errMess="Incorrect Password")
    return render_template("login.html")

@app.route('/adminPanel', methods=['GET', 'POST'])
def adminPans():
    if 'adminP' not in session:
        return redirect(url_for("adminlogin"))
    with db.cursor() as cursor:
        query = "SELECT SUM(balance) FROM accounts WHERE offshore = 1;"
        cursor.execute(query)
        funcGubbins = cursor.fetchone()
        funcGubbins = round(funcGubbins[0], 2)
        cursor.close()
    if request.method == "POST":
        data = request.form
        if 'addU' in data:
            uName = data["newUName"]
            pWord = data["newPWord"]
            uLevel = data["uLevel"]
            discID = data["discID"]
            if uLevel == "Admin":
                uInt = "1"
            elif uLevel == "Corporate":
                uInt = "2"
            else:
                uInt = "0"
            with db.cursor() as cursor:
                query = "INSERT INTO users (uName, pWord, discID, perms) VALUES ('"+str(uName)+"', '"+str(pWord)+"', '"+str(discID)+"', '"+uInt+"');"
                query2 = "SELECT uID FROM users WHERE uNAME = %s;"
                cursor.execute(query)
                cursor.execute(query2, uName)
                pew = cursor.fetchone()
                if uLevel == "Corporate":
                    queryCorp = "INSERT INTO accounts (uID, accName, balance, offshore, frozen) VALUES ('"+str(pew[0])+"', '"+str(uName)+"', '0', '0', '0');"
                    cursor.execute(queryCorp)
                db.commit()
                cursor.close()
                print(pew)
            message = "User "+str(uName)+" added with ID "+str(pew[0])+"."
            return render_template("admin.html", mess=message, funcGubbins=funcGubbins)
        elif 'remUser' in data:
            uID = data["uID"]
            valQuery = "SELECT uName FROM users WHERE uID = '"+str(uID)+"';"
            actQuery = "DELETE FROM users WHERE uID = '"+str(uID)+"';"

            with db.cursor() as cursor:
                cursor.execute(valQuery)
                validate = cursor.fetchall()
                if not validate:
                    return render_template("admin.html", errMess="User Not Found. Please Check the User ID and Try Again.", funcGubbins=funcGubbins)
                cursor.execute(actQuery)
                db.commit()
                cursor.close()
                message = "User "+str(uID)+" removed."
                return render_template("admin.html", mess=message, funcGubbins=funcGubbins)
        elif 'changePass' in data:
            uID = data['uID']
            newPWord = data['newPWord']
            valQuery = "SELECT uName FROM users WHERE uID = '"+str(uID)+"';"
            actQuery = "UPDATE users SET pWord = '"+str(newPWord)+"' WHERE uID = "+str(uID)+";"
            with db.cursor() as cursor:
                cursor.execute(valQuery)
                validate = cursor.fetchall()
                if not validate:
                    return render_template("admin.html", errMess="User Not Found. Please Check the User ID and Try Again.")
                cursor.execute(actQuery)
                db.commit()
                cursor.close()
                message = str(uID)+" password succesfully changed."
                return render_template("admin.html", mess=message, funcGubbins=funcGubbins)
        elif 'tickerAdd' in data:
            print(data)
            new = data['newTick']
            name = data['newName']
            vol = data['newVol']
            price = data['openPrice']
            findQuery = "SELECT companyName FROM stocks WHERE ticker = '"+str(new)+"';"
            addQuery = "INSERT INTO stocks (ticker, companyName, curPrice, tradeableVolume, totalVolume) VALUES ('"+str(new)+"', '"+str(name)+"', '"+str(price)+"', '"+str(vol)+"', '"+str(vol)+"');"
            print(addQuery)
            with db.cursor() as cursor:
                cursor.execute(findQuery)
                validateMe = cursor.fetchall()
                if validateMe:
                    return render_template("admin.html", errMess="Stock Already Exists", funcGubbins=funcGubbins)
                cursor.execute(addQuery)
                db.commit()
                cursor.close()
                return render_template("admin.html", mess=str(new)+" added to the stock market.")
        elif 'tickerDelete' in data:
            ticker = data["tickerDrop"]
            findQuery = "SELECT companyName FROM stocks WHERE ticker = '"+str(ticker)+"';"
            delStockQuery = "DELETE FROM stocks WHERE ticker = '"+str(ticker)+"'"
            with db.cursor() as cursor:
                cursor.execute(findQuery)
                validateMe = cursor.fetchall()
                if not validateMe:
                    return render_template("admin.html", errMess="Stock not listed", funcGubbins=funcGubbins)
                db.execute(delStockQuery)
                db.commit()
                cursor.close()
                return render_template("admin.html", mess="Stock with ticker "+str(ticker)+" deleted and all holdings removed.")
        elif 'stockChange' in data:
            ticker = data['tickToChange']
            option = data['fallDrop']
            percentChange = data['percent']
            if option == "Increase":
                cang = 1 + (int(percentChange)/100)
            else:
                cang = 1- (int(percentChange)/100)
            with db.cursor() as cursor:
                print(cang)
                queryTick = "SELECT curPrice FROM stocks WHERE ticker = '"+str(ticker)+"';"
                cursor.execute(queryTick)
                price = cursor.fetchone()
                newPrice = cang * float(price[0])
                newPrice = round(newPrice, 2)
                newQuery = "UPDATE stocks SET curPrice = '"+str(newPrice)+"' WHERE ticker = '"+str(ticker)+"';"
                cursor.execute(newQuery)
                db.commit()
                cursor.close()
                mess = str(ticker)+" changed in price by "+str(percentChange)+"% to price £"+str(newPrice)+"."
                return render_template("admin.html", mess=mess, funcGubbins=funcGubbins)
        elif 'freezerAcc' in data:
            accName = data["accName"]
            with db.cursor() as cursor:
                checkQuery = "SELECT accID, frozen FROM accounts WHERE accName = '"+str(accName)+"';"
                transitionQuery = "UPDATE accounts SET frozen = 1 WHERE accName = '"+str(accName)+"';"
                cursor.execute(checkQuery)
                check = cursor.fetchone()
                if not check:
                    return render_template("admin.html", errMess="Account does not exist")
                if check[1] == 1:
                    return render_template("admin.html", errMess="Account already frozen")
                cursor.execute(transitionQuery)
                db.commit()
                cursor.close()
                return render_template("admin.html", mess="Account succesfully frozen", funcGubbins=funcGubbins)
        elif 'defrostAcc' in data:
            accName = data["accName"]
            with db.cursor() as cursor:
                checkQuery = "SELECT accID, frozen FROM accounts WHERE accName = '"+str(accName)+"';"
                transitionQuery = "UPDATE accounts SET frozen = 0 WHERE accName = '"+str(accName)+"';"
                cursor.execute(checkQuery)
                check = cursor.fetchone()
                if not check:
                    return render_template("admin.html", errMess="Account does not exist")
                if check[1] == 0:
                    return render_template("admin.html", errMess="Account not frozen")
                cursor.execute(transitionQuery)
                db.commit()
                cursor.close()
                return render_template("admin.html", mess="Account succesfully defrosted")
        elif "threshChange" in data:
            tick = data["ticker"]
            upRate = data["uprate"]
            downRate = data["downrate"]
            query1 = "SELECT ticker FROM stocks WHERE ticker = '"+str(tick)+"';"
            with db.cursor() as cursor:
                cursor.execute(query1)
                check = cursor.fetchall()
                if not check:
                    return render_template("admin.html", errMess="Stock doesn't exist", funcGubbins=funcGubbins)
                queryUp = "UPDATE stocks SET upRate = '"+str(upRate)+"' WHERE ticker = '"+str(tick)+"';"
                queryDown = "UPDATE stocks SET downRate = '"+str(downRate)+"' WHERE ticker = '"+str(tick)+"';"
                cursor.execute(queryUp)
                cursor.execute(queryDown)
                db.commit()
                return render_template("admin.html", mess="Change Succesfull", funcGubbins=funcGubbins)
    return render_template("admin.html", funcGubbins=funcGubbins)

@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)
