import json
import os
import subprocess
import time
from dotenv import load_dotenv
load_dotenv()

# ENVIRONMENT SETTINGS
binary = os.environ.get('binary')
validator_wallet = os.environ.get('validator_wallet')
node = os.environ.get('node')
validator_address = os.environ.get('validator_address')
password = os.environ.get('keyring_password')
chain_id = os.environ.get('chain_id')
wallet_name = os.environ.get('keyring_wallet_name')
denom = os.environ.get('denom')
chain_name = os.environ.get('chain_name')
restake_percentage = os.environ.get('restake_percentage')
min_stake_balance = float(os.environ.get('min_stake_balance'))

print('===== Running script =======')


# GET MINTSCAN TX URL
def get_mintscan_url(tx):
    return 'https://www.mintscan.io/' + chain_name + '/txs/' + tx


# GET WALLET BALACNE
def get_wallet_balance(wallet_address, node = None):
    command = binary + ' query bank balances ' + wallet_address + ' -o json'
    if node:
        command += ' --node ' + node
    result = subprocess.run(command, shell=True, check=True, capture_output=True)

    if result.returncode != 0:
        print("Error. Command: ", command)
        exit(1)

    stdout = result.stdout.decode('utf-8')
    balance_object = json.loads(stdout)
    if 'balances' not in balance_object:
        print("Balance object is not as expected.", balance_object)
        exit(1)

    return float(balance_object['balances'][0]['amount'])


# RUN COMMAND
def run_command(command):
    result = subprocess.run(command, shell=True, check=True, capture_output=True)
    if result.returncode != 0:
        print("Error. Command: ", command)
        exit(1)
    stdout = result.stdout.decode('utf-8')

    command_result = {}
    for line in stdout.splitlines():
        command_result[line.split(':')[0].strip()] = line.split(':')[1].strip()

    if 'raw_log' not in command_result:
        print("Error: Raw log not found", command, command_result)
        exit(1)

    if command_result['raw_log'] != "'[]'":
        print("Error: Raw log provided... ", command, command_result)
        exit(1)

    return command_result


# CLAIM REWARDS
def claim_rewards(gas_fees):
    command = 'echo -e "' + password + "\n" + password + '\n" | ' \
              + binary + ' tx distribution withdraw-rewards ' + validator_address \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + wallet_name \
              + ' --commission' \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


# STAKE FUNCTION
def stake(validator_address, stake_balance, gas_fees):
    command = 'echo -e "' + password + "\n" + password + '\n" | ' \
              + binary + ' tx staking delegate ' + validator_address + ' ' + stake_balance + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + wallet_name \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


original_validator_balance = get_wallet_balance(validator_wallet, node)

print("Validator balance:" + str(original_validator_balance))

print(' -- Claim Rewards -- ')
command_result = claim_rewards(2500)

print('Claim requested...')
print(get_mintscan_url(command_result['txhash']))
print('Waiting for it to be accepted...')

time.sleep(10)

balance = get_wallet_balance(validator_wallet, node)
if original_validator_balance == balance:
    print('Validator balance was not updated. Commission probably wasn\'t accepted? Please check TX', command_result)
    exit(1)

print(' -- Claim Successful -- ')

balance -= 1000000
restake_balance = balance*float(restake_percentage)/100

print('Your safe stake balance is "'+ str(balance) + denom + '"... You are going to stake ' + str(restake_percentage) + ' which is ' + str(restake_balance) + denom)

if restake_balance > min_stake_balance:
    stake(validator_address, restake_balance, 2500)
else:
    print('Re-stake balance does not meet your min stake balance')
