def bondMoves():
    now = datetime.now()
    nowStr = now.strftime("%Y-%m-%d")
    findQuery = "SELECT uID, bondID, fullValue FROM bonds WHERE maturityDate = '"+str(nowStr)+"';"
    cursor = db.cursor()
    cursor.execute(findQuery)
    bonds = cursor.fetchall()
    if not bond:
        print("No Bonds")
        return
    for bond in bonds:
        uID = bond[0]
        query2 = "SELECT discID FROM users WHERE uID = '"+str(uID)+"';"
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
