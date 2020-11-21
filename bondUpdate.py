import requests
import pymysql as sql
from datetime import datetime, date
db = sql.connect(
    host="34.66.12.173",
    user="root",
    password="Loki2018!",
    db="fiscalTrading")
authParams = {"Authorization":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI3NTc5MDA2NjQzMzE0MzY0MzAiLCJpYXQiOjE2MDM1NTg3MTh9.jrZpy7vjbp4CiH4d3zwkp-qgs3P8KBdSFvg9J91wmFc"}
def bondOwnChecks():
    now = datetime.now()
    nowStr = now.strftime("%Y-%m-%d")
    findQuery = "SELECT uID, bondID, fullValue FROM bonds WHERE maturityDate = '"+str(nowStr)+"';"
    cursor = db.cursor()
    cursor.execute(findQuery)
    bonds = cursor.fetchall()
    if not bonds:
        print("No Bonds")
        return
    for bond in bonds:
        uID = bond[0]
        query2 = "SELECT discID FROM users WHERE uID = '"+str(uID)+"';"
        deQuery = "DELETE FROM bonds WHERE bondID = '"+str(bond[1]+"';"
        cursor.execute(query2)
        discID = cursor.fetchone()
        discID = discID[0]
        runningURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/"+str(discID)
        uData = {'cash':0,'bank':bond[2]}
        rData = {'cash':(0-bond[2]), 'bank':0}
        rishiURL = "https://unbelievaboat.com/api/v1/guilds/560525317429526539/users/292953664492929025"
        rishi = requests.patch(rishiURL, headers=authParams, json=rData)
        running = requests.patch(runningURL, headers=authParams, json=uData)
    cursor.close()

def bondPriceMoves():
    curRate = 3.5
    findQuery = "SELECT uID, bondID, fullValue, buyValue, maturityDate, buyDate FROM bonds;"
    cursor = db.cursor()
    cursor.execute(findQuery)
    bonds = cursor.fetchall()
    for bond in bonds:
        matureCalc = datetime.strptime(bond[4], "%Y-%m-%d").date()
        buyCalc = datetime.strptime(bond[5], "%Y-%m-%d").date()
        print(matureCalc,buyCalc)
        uhuh = bond[2]/((1+(curRate/100))**period)
        if bond[3] != uhuh:
            query = "UPDATE bonds SET buyValue = '"+str(uhuh)+"' WHERE bondID = '"+str(bond[1])+"';"
            cursor.execute(query)
    db.commit()
    cursor.close()

bondOwnChecks()
bondPriceMoves()
