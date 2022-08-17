import os
from dotenv import load_dotenv
import requests
import web3
import time
import sqlite3
import json
from ratelimit import limits, sleep_and_retry

start_time = time.time()

def init_connection():
    avado_url = "http://ethchain-geth.my.ava.do:8545"
    w3 = web3.Web3(web3.Web3.HTTPProvider(avado_url))
    print(f"connection active? ", w3.isConnected())
    return w3

def get_addresses(start, end, w3):
    addresses = []
    seen = set()
    
    for x in range (start, end):
        print(f"getting addresses from block: ", x)
        block = w3.eth.getBlock(x, True)
        # for transaction in block.transactions:
        # print(type(block))
        for transaction in block.transactions:
            tx_logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
            # logs are a list of dictionaries
            for log in tx_logs:
                if log["address"] not in seen:
                    seen.add(log["address"])
                    addresses.append(log["address"])
        # print(addresses)
    return(addresses)
    
@sleep_and_retry
@limits(calls=5, period=1)
def call_api(address, ETHERSCAN_TOKEN):
    URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_TOKEN}"
    return requests.get(URL).content


def get_ABIs(addresses, ETHERSCAN_TOKEN):
    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()

    for address in addresses:
        # get abi and add address to db only if not already in db
        # might be too slow querying sql each time - but sql is fast?
        # print(f"sql return value: ",cur.execute("SELECT address FROM contract WHERE address = (?)",(address,)).fetchone())
        # print(f"address value: ",address)
        # if db call returns none, address is not in db, so add it.
        if cur.execute("SELECT address FROM contract WHERE address = (?)",(address,)).fetchone() is None:
            print(f"getting and writing ABI for address: ", address)
            response = call_api(address, ETHERSCAN_TOKEN)
        # ABI column in db is actually response; must be parsed as json later
            cur.execute("INSERT INTO contract (address, ABI) VALUES (?, ?)",(address, response))
        # print(response)
    con.commit()
    con.close()
        
# eth_getCode -> to check if an address is a contract


def main():
    # get etherscan token from .env file
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')

    # connect to avado
    w3 = init_connection()
    # get all distinct contracts used in last 2 years
    addresses = get_addresses(w3.eth.blockNumber-3, w3.eth.blockNumber, w3)
    # get abi for each contract
    # URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_TOKEN}"
    get_ABIs(addresses, ETHERSCAN_TOKEN)
    #response = requests.get(URL)

    # write contracts + ABIs to pandas or sql 

    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()

    """ TO GET DICT FROM JSON ABI IN DATABASE:
    response = cur.execute("SELECT ABI FROM contract WHERE address = (?)", ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",))
    ABI = json.loads(response.fetchall()[0][0])
    print(f"ABI : ", ABI["result"])"""

    # open("./ABIs/abis.json", "wb").write(response.content)
    print(f"Done! ", len(addresses),"distinct addresses found and written to database")
    print("--- %s seconds ---" % (time.time()-start_time))

if __name__ == "__main__":
    main()
