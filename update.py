def priceMoves():
    threading.Timer(600.0, priceMoves).start()
    findQuery = "SELECT ticker, curPrice, upRate, downRate FROM stocks;"
    with db.cursor() as cursor:
        cursor.execute(findQuery)
        tickers = cursor.fetchall()
        for dat in tickers:
            tick = dat[0]
            curPrice = dat[1]
            uprate = (1+float(dat[2]))
            downrate = (1-float(dat[3]))
            downPrice = (curPrice * downrate)
            upPrice = (curPrice * uprate)
            newPrice = uniform(downPrice, upPrice)
            print(newPrice)
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            print(dt_string)
            updateQuery = "UPDATE stocks SET curPrice = '"+str(newPrice)+"' WHERE ticker = '"+str(tick)+"';"
            recordQuery = "INSERT INTO pricemoves (ticker ,timeStamped, newPrice) VALUES ('"+str(tick)+"','"+str(dt_string)+"', '"+str(newPrice)+"');"
            cursor.execute(updateQuery)
            cursor.execute(recordQuery)
        db.commit()
