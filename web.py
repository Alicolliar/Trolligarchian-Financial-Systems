from flask import Flask, render_template, request, redirect, url_for, session
import requests
import pymysql as sql
import threading
from random import uniform
from datetime import datetime, date
db = sql.connect(
    host="DB_HOST",
    user="DB_USER",
    password="DB_PASSWORD",
    db="DBNAME")
app = Flask(__name__)
app.secret_key = "###SECRETKEY###"
authParams = {"Authorization":"###AUTH_TOKEN###"}
rates = {
    "capGainTax":5,
    "interest":3.5,
    "transact":25
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
            fullPrice = price * int(i[1])
            i.append(fullPrice)
            totVal += fullPrice
        totVal = round(totVal, 2)
        cursor.close()
    return holds, totVal

@app.route('/')
def home():
    totalVal = 0
    query = "SELECT curPrice, tradeableVolume, totalVolume FROM stocks;"
    query2 = "SELECT SUM(buyValue) FROM bonds;"
    with db.cursor() as cursor:
        cursor.execute(query)
        dataS = cursor.fetchall()
        cursor.execute(query2)
        dataB = cursor.fetchone()
        bondTot = dataB[0]
        cursor.close()
    for dat in dataS:
        boughtVol = dat[2] - dat[1]
        totVal = boughtVol * dat[0]
        totalVal += totVal
    totalVal = round(totalVal, 0)
    message = "Honourable mention to Memer who helped us find a major bug that would have caused some big issues if it had been further exploited. They get a cookie."
    return render_template("home.html", message=message, valS=totalVal, valB=bondTot)

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
            return redirect(url_for("trading"))
    return render_template("login.html")

@app.route('/stockTrade', methods=['GET', 'POST']) ##DONE FOR NOW
def trading():
    if session['uName']:
        if request.method == 'POST':
            order = request.form
            stock = order["ticker"]
            quant = order["numStock"]
            discID = session['discID']
            type = order["tType"]
            uName = session['uID']
            rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
            runningURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
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
                postVAT = round((preVAT * 1.05), 2)
                vat = round((preVAT*0.05), 0)
                yourBal = requests.get(runningURL, headers=authParams)
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
                notification = str(uName)+" has purchased "+str(quant)+" of "+stock+" at £"+str(price[0])+" giving a total of £"+str(postVAT)+", including all tax."
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
                print(priceAdj)
                print(newPrice)
                updatQuant = int(help[1])-int(quant)
                query4 = "UPDATE holdings SET quant = "+str(updatQuant)+" WHERE hID = "+str(help[0])+";"
                query2 = "INSERT INTO orders (uID, ticker, price, numStock, priceperVAT, totalPrice, orderType) VALUES ('"+str(uName)+"', '"+stock+"', '"+str(price[0])+"', '"+quant+"', '"+str(preVAT)+"', '"+str(postVAT)+"', 'Sell');"
                query3 = "UPDATE stocks SET tradeableVolume = "+str(newVol)+", curPrice = "+str(newPrice)+" WHERE ticker = '"+stock+"';"
                notification = str(uName)+" has sold "+str(quant)+" of "+stock+" at £"+str(price[0])+" giving a total of £"+str(postVAT)+", including all tax."
            cursor.execute(query2)
            cursor.execute(query3)
            cursor.execute(query4)
            rishi = requests.patch(rishiURL, headers=authParams, json=dataRish)
            running = requests.patch(runningURL, headers=authParams, json=data1)
            db.commit()
            cursor.close()
            return render_template("stocks/tradePage.html", notif=notification)

        return render_template("stocks/tradePage.html")
    else:
        redirect(url_for("stocklogin"))

@app.route('/holdLogin', methods=['GET', 'POST']) ##DONE FOR NOW
def holdingsLogin():
    if 'uName' in session or 'adminP' in session:
        return redirect(url_for("holdings"))
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
    if request.method == "POST":
        data = request.form
        if 'addU' in data:
            uName = data["newUName"]
            pWord = data["newPWord"]
            uLevel = data["uLevel"]
            discID = data["discID"]
            if uLevel == "Admin":
                uInt = "1"
            else:
                uInt = "0"
            with db.cursor() as cursor:
                query = "INSERT INTO users (uName, pWord, discID, perms) VALUES ('"+str(uName)+"', '"+str(pWord)+"', '"+str(discID)+"', '"+uInt+"');"
                query2 = "SELECT uID FROM users WHERE uNAME = %s;"
                cursor.execute(query)
                db.commit()
                cursor.execute(query2, uName)
                pew = cursor.fetchone()
                cursor.close()
                print(pew)
            message = "User "+str(uName)+" added with ID "+str(pew[0])+"."
            return render_template("admin.html", mess=message)
        elif 'remUser' in data:
            uID = data["uID"]
            valQuery = "SELECT uName FROM users WHERE uID = '"+str(uID)+"';"
            actQuery = "DELETE FROM users WHERE uID = '"+str(uID)+"';"
            with db.cursor() as cursor:
                cursor.execute(valQuery)
                validate = cursor.fetchall()
                if not validate:
                    return render_template("admin.html", errMess="User Not Found. Please Check the User ID and Try Again.")
                cursor.execute(actQuery)
                db.commit()
                cursor.close()
                message = "User "+str(uID)+" removed."
                return render_template("admin.html", mess=message)
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
                return render_template("admin.html", mess=message)
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
                    return render_template("admin.html", errMess="Stock Already Exists")
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
                    return render_template("admin.html", errMess="Stock not listed")
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
                return render_template("admin.html", mess=mess)


    return render_template("admin.html")

if __name__ == '__main__':
    app.run(debug=True)
