import os
import json
from flask import Flask, request, redirect, render_template as render
from web3 import Web3
from pathlib import Path

app = Flask(__name__)

with open('/home/gabriel/prog/json_config/wimm.json') as config_file:
    config = json.load(config_file)


@app.route('/')
def home():
    ganache_url = config["GANACHE_URL"]
    send_wallet = config["SENDER_WALLET"]
    private_key = config["PRIVATE_KEY"]
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    # get balance
    wei_balance = web3.eth.get_balance(send_wallet)
    balance = web3.fromWei(wei_balance, 'ether')

    context = {"send_wallet":send_wallet, "balance":balance}
    return render('home.html', **context)


def infuraBlock():
    infura_url = config['INFURA_URL']
    web3 = Web3(Web3.HTTPProvider(infura_url))
    balance = web3.eth.getBalance("0xFC58C26caf80ef110B4552C1AcCb0986de5142F3")

    print(web3.isConnected())
    print(web3.eth.blockNumber)
    print(web3.fromWei(balance, "ether"))
    return


def ganacheBlock():
    ganache_url = config['GANACHE_URL']
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    print(web3.isConnected())
    return


@app.route('/read_transaction', methods=['GET', 'POST'])
def read_transaction():
    if request.method == "POST":
        infura_url = config['INFURA_URL']
        web3 = Web3(Web3.HTTPProvider(infura_url))
        address = request.form.get("address")
        abi = json.loads(request.form.get("abi"))
        contract = web3.eth.contract(address=address, abi=abi)

        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        contract = web3.eth.contract(address=address, abi=abi)
        totalSupply = contract.functions.totalSupply().call()
        totalSupplyFormated = web3.fromWei(totalSupply, 'ether')
        balance = contract.functions.balanceOf(address).call()

        context = {"name":name, "symbol":symbol, "contract":contract, "totalSupplyFormated":totalSupplyFormated, "balance":balance}
        return render('displayReed.html', **context)

    return render('readTran.html')


@app.route('/send_transaction', methods=['GET', 'POST'])
def send_transaction():
    if request.method == "POST":
        address = request.form.get("address")
        amount = request.form.get("amount")

        ganache_url = config["GANACHE_URL"]
        send_wallet = config["SENDER_WALLET"]
        private_key = config["PRIVATE_KEY"]
        web3 = Web3(Web3.HTTPProvider(ganache_url))

        # get the nonce
        nonce = web3.eth.getTransactionCount(send_wallet)

        # build a transaction
        tx = {
            'nonce': nonce,
            'to': address,
            'value': web3.toWei(amount, 'ether'),
            'gas': 2000000,
            'gasPrice': web3.toWei('50', 'gwei')
        }
        
        # sign transaction
        signed_tx = web3.eth.account.signTransaction(tx, private_key)

        # send transaction
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)

        # get transaction hash
        hash = web3.toHex(tx_hash)

        # get balance
        wei_balance = web3.eth.get_balance(send_wallet)
        balance = web3.fromWei(wei_balance, 'ether')

        context = {"send_wallet":send_wallet, "address":address, "amount":amount, "hash":hash, "balance":balance}
        return render('displaySend.html', **context)

    return render('sendTran.html')


if __name__ == '__main__':
    app.run(port=5000, debug=True)