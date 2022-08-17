from etherscan_api_scrape_copy import init_connection
import web3


def get_logs(start_block, end_block, w3):
    logs = []
    for x in range (start_block, end_block):
        print(f"getting addresses from block: ", x)
        block = w3.eth.getBlock(x, True)
        # for transaction in block.transactions:
        # print(type(block))
        for transaction in block.transactions:
            tx_logs = w3.eth.get_transaction_receipt(transaction["hash"])["logs"]
            # logs are a list of dictionaries
            for log in tx_logs:
                logs.append((log["address"], log["data"]))
    return logs



def main():
    w3 = init_connection()
    print(get_logs(w3.eth.blockNumber-1, w3.eth.blockNumber, w3))


if __name__ =="__main__":
    main()