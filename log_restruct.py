import os
from pickle import FALSE, TRUE
from etherscan_api_scrape_copy import init_connection, call_api
import web3
import sqlite3
from dotenv import load_dotenv
import json


# get logs - this outputs 'address' and 'data' of the logs in the block range as
# a list of tuples
def get_logs(start_block, end_block, w3):
    logs = []
    for x in range (start_block, end_block):
        print(f"getting logs from block: ", x)
        block = w3.eth.getBlock(x, True)
        # for transaction in block.transactions:
        # print(type(block))
        for transaction in block.transactions:
            tx_logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
            # logs are a list of dictionaries
            for log in tx_logs:
                logs.append((log["address"], log["data"]))
    # logs is a list of tuples comtaining address and data.
    return logs

### get ABI of contract from db (or etherscan if not in db)

def contract_in_db(address):
    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()
    return cur.execute("SELECT address FROM contract WHERE address = (?)", (address,)).fetchone() is not None
 
def getABI(address):
        # check if contract in db
    if contract_in_db(address):
        # if yes, get and parse abi
        print("fetching from db")
        ABI = getAbiDb(address)
        # sql request for contract abi
    else:
        # if no, call etherscan api to get and parse abi
        print("fetching from etherscan")
        ABI = getAbiEtherscan(address)
    return ABI

def getAbiEtherscan(address):
    """ get abi from etherscan and write it to database. """
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()
    response = call_api(address, ETHERSCAN_TOKEN)
    cur.execute("INSERT INTO contract (address, ABI) VALUES (?, ?)",(address, response))
    return json.loads(response)

def getAbiDb(address):
    """ get abi from database"""
    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()
    AbiJson = cur.execute("SELECT ABI from contract WHERE address = (?)", (address,)).fetchone()
    ABI = json.loads(AbiJson[0])
    return ABI

def zipAbiData(ABI, data):
# do banteg zip of abi and log data
    pass
    



def main():
    w3 = init_connection()
    # print(get_logs(w3.eth.blockNumber-1, w3.eth.blockNumber, w3))
    # log is an individual address data tuple
    for blockNumber in range (w3.eth.blockNumber, w3.eth.blockNumber-5, -1):
        print(f"getting logs from block: ", blockNumber)
        block = w3.eth.getBlock(blockNumber, True)
        # print(type(block))
        for transaction in block.transactions:
            tx_logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
            # logs are a list of dictionaries
            for log in tx_logs:
                print(f"log: ",log)
                ABI = getABI(log["address"])
                zipAbiData(ABI, log["data"])
    print("actually finished")

if __name__ =="__main__":
    main()