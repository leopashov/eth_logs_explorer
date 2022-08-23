import os
from dotenv import load_dotenv
import requests
import web3
import time
import sqlite3
from ratelimit import limits, sleep_and_retry
import json

# run function in command line: python -c 'from foo import hello; print hello()'

start_time = time.time()

def init_connection():
    avado_url = "http://ethchain-geth.my.ava.do:8545"
    w3 = web3.Web3(web3.Web3.HTTPProvider(avado_url))
    print(f"connection active? ", w3.isConnected())
    return w3

def writeDistinctABIs(cur, log, ETHERSCAN_TOKEN, db_add_count):
    if cur.execute("SELECT address FROM contract WHERE address = (?)",(log["address"],)).fetchone() is None:
        print(f"getting and writing ABI for address: ", log["address"])
        response = call_api(log["address"], ETHERSCAN_TOKEN)
    # ABI column in db is just text, must be json parsed.
        if response is not None:
            cur.execute("INSERT INTO contract (address, ABI) VALUES (?, ?)",(log["address"], response))
            db_add_count += 1
            print(response)
        
    else:
        print("## address already in db ##")
    return db_add_count

def get_addresses_from_block(blockNumber, w3, ETHERSCAN_TOKEN, db_add_count):
    count = 0
    con = sqlite3.connect("./ABIs/contracts.db")
    cur = con.cursor()
    print(f"getting addresses from block: ", blockNumber)
    block = w3.eth.getBlock(blockNumber, True)
    # for transaction in block.transactions:
    # print(type(block))
    for transaction in block.transactions:
        print(f"getting transaction: ", count)
        count += 1
        tx_logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
        # logs are a list of dictionaries
        for log in tx_logs:
            # Don't actually know if having this new function is an improvement
            db_add_count = writeDistinctABIs(cur, log, ETHERSCAN_TOKEN, db_add_count)

    con.commit()
    con.close()
    return db_add_count
                
            # print(addresses)
    # return(addresses)

@sleep_and_retry
@limits(calls=5, period=1)
def call_api(address, ETHERSCAN_TOKEN):
    URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_TOKEN}"
    response = json.loads(requests.get(URL).content)
    if int(response["status"]) == 1:
        return requests.get(URL).content

    # b'{"status":"0","message":"NOTOK","result":"Too many invalid api key attempts, please try again later"}'
    
        
# eth_getCode -> to check if an address is a contract


def main():
    # get etherscan token from .env file
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    # connect to avado
    w3 = init_connection()
    db_add_count = 0
    block_at_run = w3.eth.blockNumber
    # cycle through each block starting at most recent
    for blockNumber in range(block_at_run, block_at_run-1, -1):
        new_addresses = get_addresses_from_block(blockNumber, w3, ETHERSCAN_TOKEN, db_add_count)

        # get abi for each contract
        # URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_TOKEN}"
        # get_ABIs(addresses, ETHERSCAN_TOKEN)
    #response = requests.get(URL)

    # write contracts + ABIs to pandas or sql 


    """ TO GET DICT FROM JSON ABI IN DATABASE:
    response = cur.execute("SELECT ABI FROM contract WHERE address = (?)", ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",))
    ABI = json.loads(response.fetchall()[0][0])
    print(f"ABI : ", ABI["result"])"""

    # open("./ABIs/abis.json", "wb").write(response.content)
    print(f"Done! ", new_addresses,"distinct addresses found and written to database")
    print("--- %s seconds ---" % (time.time()-start_time))

if __name__ == "__main__":
    main()
