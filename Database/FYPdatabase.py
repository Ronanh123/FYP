import sqlite3

def GetCandidates():
    connection = sqlite3.connect('Database\TallyBotDB.db')
    c = connection.cursor()
    c.execute("SELECT * FROM Candidates")
    connection.commit()
    return list(c.fetchall())
    connection.close()

def GetParties():
    connection = sqlite3.connect('Database\TallyBotDB.db')
    c = connection.cursor()
    c.execute("SELECT party FROM Candidates")
    connection.commit()
    return list(c.fetchall())
    connection.close()

def GetPartyVotes(party):
    connection = sqlite3.connect('Database\TallyBotDB.db')
    c = connection.cursor()
    c.execute("SELECT name FROM Candidates WHERE party = ?",(str(party),))
    connection.commit()
    return list(c.fetchall())
    connection.close()

# connection = sqlite3.connect('TallyBotDB.db')
# c = connection.cursor()
# c.execute("SELECT * FROM Candidates")
# connection.commit()
# connection.close()

print(GetCandidates())
