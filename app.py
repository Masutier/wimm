import os
import json
from flask import Flask, request, redirect, jsonify, flash, render_template as render
from pathlib import Path

from web3 import Web3
from solcx import compile_source

with open('/home/gabriel/prog/json_config/wimm.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.config.update(
    TESTING = True,
    SECRET_KEY = config["PRIVATE_KEY"]
)


@app.route('/')
def home():
    ganache_url = config["GANACHE_URL"]
    send_wallet = config["SENDER_WALLET"]
    private_key = config["PRIVATE_KEY"]
    web3 = Web3(Web3.HTTPProvider(ganache_url))

    if web3.isConnected():
        # get balance
        wei_balance = web3.eth.get_balance(send_wallet)
        balance = web3.fromWei(wei_balance, 'ether')
        endpoint = "Ganache Local Blockchain"

        context = {"send_wallet":send_wallet, "balance":balance, "endpoint":endpoint}
        return render('home.html', **context)
    else:
        web3 = Web3(Web3.HTTPProvider(config['INFURA_URL']))
        address = config["SENDER_WALLET"]
        wei_balance = web3.eth.getBalance(address)
        balance = web3.fromWei(wei_balance, 'ether')
        endpoint = "Infura Main Net"

        flash("Please connect to local provider")
        context = {"send_wallet":address, "balance":balance, "endpoint":endpoint}
        return render('home.html', **context)


@app.route('/infuraPoint', methods=['GET', 'POST'])
def infuraBlock():
    if request.method == "POST":
        option = request.form.getlist('options')
        if option == ['option1']:
            web3 = Web3(Web3.HTTPProvider(config['INFURA_URL']))
            endpoint = "Infura Main Net"
        elif option == ['option2']:
            web3 = Web3(Web3.HTTPProvider(config['KOVAN_URL']))
            endpoint = "Infura Kovan Net"
        elif option == ['option3']:
            web3 = Web3(Web3.HTTPProvider(config['RINKEBY_URL']))
            endpoint = "Infura Rinkeby Net"
        else:
            flash("Something went wrong, please try again")
            return redirect('infuraPoint.html')
        address = request.form.get("address")
        yes = web3.isAddress(address)
        balance = web3.eth.getBalance(address)
        blockNumber = web3.eth.blockNumber
        weiBalance = web3.fromWei(balance, "ether")

        context = {"balance":balance, "blockNumber":blockNumber, "weiBalance":weiBalance, "endpoint":endpoint, "yes":yes}
        return render('displayNet.html', **context)

    return render('infuraPoint.html')


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


@app.route('/contract')
def contractHello():
    # we can code the contract in https://remix.ethereum.org to verify the format is good and copy here beteen """ """
    
    compiled_solidity = compile_source(
        """
        // SPDX-License-Identifier: MIT
        pragma solidity 0.8.14;
        contract HelloWorld {
            string public message;
            constructor() {message = "Hello World";}
            function setMessage(string memory _message) public {message = _message;}
            function sayMessage() view public returns (string memory) {return message;}
        }
        """,
        output_values = ['abi', 'bin']
    )

    contract_id, contract_interface = compiled_solidity.popitem()
    abi = contract_interface['abi']
    bin = contract_interface['bin']

    context = {"abi":abi, "bin":bin, "contract_id":contract_id}
    return render('contractHello,html', **context)
    # return jsonify(compiled_solidity)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
