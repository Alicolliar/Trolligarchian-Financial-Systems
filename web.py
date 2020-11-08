from flask import Flask, render_template, request, redirect, url_for, session
import requests
import pymysql as sql
import threading
from random import uniform
from datetime import datetime
db = sql.connect(
    host="###databaseadress###",
    user="###databaseuser",
    password="###databasepassword",
    db="###database")
app = Flask(__name__)
app.secret_key = "###secret_key###"
authParams = {"Authorization":"###unbelieva_key###"}

def priceMoves():
    threading.Timer(600.0, priceMoves).start()
    findQuery = "SELECT ticker, curPrice FROM stocks;"
    with db.cursor() as cursor:
        cursor.execute(findQuery)
        tickers = cursor.fetchall()
        for dat in tickers:
            tick = dat[0]
            curPrice = dat[1]
            downPrice = (curPrice * 0.95)
            upPrice = (curPrice * 1.05)
            newPrice = uniform(downPrice, upPrice)
            print(newPrice)
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            print(dt_string)
            updateQuery = "UPDATE stocks SET curPrice = '"+str(newPrice)+"' WHERE ticker = '"+str(tick)+"';"
            recordQuery = "INSERT INTO pricemoves (ticker ,timeStamped, newPrice) VALUES ('"+str(tick)+"','"+str(dt_string)+"', '"+str(newPrice)+"');"
            cursor.execute(updateQuery)
            cursor.execute(recordQuery)
            cursor.close()
        db.commit()

@app.route('/')
def home():
    message = "There is some cool stuff here. Try the site on your phone now!"
    return render_template("home.html", message=message)

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
                vat = -1*round((preVAT*0.05), 0)
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
            rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"
            runningURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
            rishi = request.patch(rishiURL, headers=authParams, json=dataRish)
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

@app.route('/personalHoldings')
def holdings():
    if 'uName' not in session and 'adminP' not in session:
        return redirect(url_for("holdingsLogin"))
    uID = session['uID']
    user = session["uName"]
    query = "SELECT ticker, quant FROM holdings WHERE uID = '"+str(uID)+"';"
    totVal = 0
    with db.cursor() as cursor:
        cursor.execute(query)
        holds = cursor.fetchall()
        holds = list(holds)
        print(holds)
        for i in holds:
            i = list(i)
            tickBoi = i[0]
            repetQuery = "SELECT curPrice FROM stocks WHERE ticker = '"+str(tickBoi)+"';"
            cursor.execute(repetQuery)
            price = cursor.fetchone()
            price = list(price)
            fullPrice = float(price[0]) * int(i[1])
            print(fullPrice)
            i.append(fullPrice)
            totVal += fullPrice
        totVal = round(totVal, 2)
        cursor.close()
    return render_template("stocks/holdingsView.html", holds=holds, users=user, valTot=totVal)

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
            new = data['newTick']
            name = data['newName']
            vol = data['newVol']
            price = data['openPrice']
            findQuery = "SELECT companyName FROM stocks WHERE ticker = '"+str(new)+"';"
            addQuery = "INSERT INTO stocks (ticker, companyName, curPrice, tradeableVolume, totalVolume) VALUES ('"+str(new)+"', '"+str(name)+"', '"+str(price)+"', '"+str(vol)+"', '"+str(vol)+"');"
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

if __name__ == '__main__':
    app.run(debug=True)
