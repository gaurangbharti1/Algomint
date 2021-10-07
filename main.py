from algosdk.v2client import algod
from algosdk import account, mnemonic
import json
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, AssetFreezeTxn

mnemonic1 = "damp gate tape grid tragic process pizza captain when float stairs rebel vicious favorite price polar this pretty law video viable drip tumble able refuse"
mnemonic2 = "midnight video letter pen lazy despair favorite result life solution draw relax shrug carry limb crunch joy abandon taxi once comic buffalo stereo absorb pepper"
mnemonic3 = "glimpse inject eyebrow enemy gun belt glimpse magnet coconut that dinosaur nation proof come uncover dune scale advance spell quote arch buzz siege absorb soft"

#Following Documentation to avoid unnecessary mistakes

accounts = {}
counter = 1
for m in [mnemonic1, mnemonic2, mnemonic3]:
    accounts[counter] = {}
    accounts[counter]['pk'] = mnemonic.to_public_key(m)
    accounts[counter]['sk'] = mnemonic.to_private_key(m)
    counter += 1

#Unsure of what to change/put here so leaving it unchanged
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address)

def wait_for_confirmation(client, txid, timeout):
   
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1

        #Added this to timeout if not completed within desired round. Unsure of how long 1 round takes to complete, otherwise I would perform some maths to convert user's desired timeout time to rounds
        if last_round > timeout:
            print("Transcation could not be completed within time")
            break
        
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo
    

def print_created_asset(algodclient, account, assetid):    

    account_info = algodclient.account_info(account)
    idx = 0;
    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1       
        if (scrutinized_asset['index'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break

def print_asset_holding(algodclient, account, assetid):
    
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break

print("Account 1 address: {}".format(accounts[1]['pk']))
print("Account 2 address: {}".format(accounts[2]['pk']))
print("Account 3 address: {}".format(accounts[3]['pk']))


#Creating an Asset

params = algod_client.suggested_params()

txn = AssetConfigTxn(
    sender=accounts[1]['pk'],
    sp=params,
    total=1000,
    default_frozen=False,
    unit_name="ALGOTEST",
    asset_name="AlgoTest",
    manager=accounts[2]['pk'],
    reserve=accounts[2]['pk'],
    freeze=accounts[2]['pk'],
    clawback=accounts[2]['pk'], 
    decimals=1,
    note = "Gaurang Bharti")

stxn = txn.sign(accounts[1]['sk'])

txid = algod_client.send_transaction(stxn)
print('TXID: ' + str(txid))

wait_for_confirmation(algod_client,txid, 20000000) #Using this everywhere to standardise the testing. Transcation fails if under these many rounds

try:
    ptx = algod_client.pending_transaction_info(txid)
    asset_id = ptx["asset-index"]
    print_created_asset(algod_client, accounts[1]['pk'], asset_id)
    print_asset_holding(algod_client, accounts[1]['pk'], asset_id)
except Exception as e:
    print(e)

#Transferring Assets

#Opt-in

params =   algod_client.suggested_params()

account_info = algod_client.account_info(accounts[3]['pk'])
holding = None
idx = 0
for my_account_info in account_info['assets']:
    scrutinized_asset = account_info['assets'][idx]
    idx = idx + 1    
    if (scrutinized_asset['asset-id'] == asset_id):
        holding = True
        break

if not holding:

    # Use the AssetTransferTxn class to transfer assets and opt-in
    txn = AssetTransferTxn(
        sender=accounts[3]['pk'],
        sp=params,
        receiver=accounts[3]["pk"],
        amt=0,
        index=asset_id)
    stxn = txn.sign(accounts[3]['sk'])
    txid = algod_client.send_transaction(stxn)
    print('TXID: ' + str(txid))
   
    wait_for_confirmation(algod_client, txid, 20000000)
   
    # This should now show a holding with a balance of 0.
    print_asset_holding(algod_client, accounts[3]['pk'], asset_id)

#Transferring

params = algod_client.suggested_params()

txn = AssetTransferTxn(
    sender=accounts[1]['pk'],
    sp=params,
    receiver=accounts[3]["pk"],
    amt=10,
    index=asset_id)

stxn = txn.sign(accounts[1]['sk'])

txid = algod_client.send_transaction(stxn)

print('TXID: ' + str(txid))

wait_for_confirmation(algod_client, txid, 20000000)

print_asset_holding(algod_client, accounts[3]['pk'], asset_id)


#Freezing Assets

ams = algod_client.suggested_params()

txn = AssetFreezeTxn(
    sender=accounts[2]['pk'],
    sp=params,
    index=asset_id,
    target=accounts[3]["pk"],
    new_freeze_state=True   
    )
stxn = txn.sign(accounts[2]['sk'])
txid = algod_client.send_transaction(stxn)
print('TXID: ' + str(txid))

wait_for_confirmation(algod_client, txid, 20000000)

print_asset_holding(algod_client, accounts[3]['pk'], asset_id)