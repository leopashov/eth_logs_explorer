import sqlite3

con = sqlite3.connect("./ABIs/contracts.db")
cur = con.cursor()


cur.execute("DELETE FROM contract WHERE length(ABI) < 105")
con.commit()


