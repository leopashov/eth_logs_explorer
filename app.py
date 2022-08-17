from flask import Flask, redirect, render_template, request, session
import sqlite3
from flask_session.__init__ import Session
import web3

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def value_corrector(value):
    """Some contract calls do a number of operations, and are not simple transfers
    e.g sync or swap. These come with large data fields (e.g 258 characters representing
    4 numbers. This function splits those characters into batches of 64 chars
    (with a '0x' at the start)"""
    output = []
    # remove '0x' from front
    value = value[2::]
    # if data field larger than simple transfer

    while len(value) > 64:

        output.append(int(value[0:64], 16))
        value = value[64::]

    output.append(int(value, 16))
    # print(f"value corrector output: ", output)
    return output

@app.route("/")
def main():
    avado_url = "http://ethchain-geth.my.ava.do:8545"
    w3 = web3.Web3(web3.Web3.HTTPProvider(avado_url))
    print(f"connection active? ", w3.isConnected())

    con = sqlite3.connect("./token_lists/tokens.db")
    # create cursor to execute database commands
    cur = con.cursor()

      # request the latest block number
    ending_blocknumber = w3.eth.blockNumber

    # latest block number minus 100 blocks
    starting_blocknumber = ending_blocknumber - 1

    # create an empty dictionary we will add transaction data to
    tx_dictionary = {}
    tx_list = []
    token_value = 0
    token = 0
    tx_reciepts = []
    for x in range(starting_blocknumber, ending_blocknumber):
        block = w3.eth.getBlock(x, True)
        for transaction in block.transactions:
            logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
            for log in logs:
                #log["data"] = value_corrector(log["data"])
                print((log["data"]))
                try:
                    token = log["address"]
                except:
                    token=0

            tx_list.append(
            {"hash" : transaction["hash"].hex(), 
            "input": transaction["input"], 
            "value": web3.Web3.fromWei(transaction["value"],"ether"), 
            "logs": logs,
            "token": token,
            "token_value": token_value
            }
            )
    print(tx_list[0])

    return render_template(
        "index.html",
        tx_list = tx_list
    )