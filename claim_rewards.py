import json
import os
import subprocess
import time

from subprocess import PIPE
from dotenv import load_dotenv

load_dotenv()

# ENVIRONMENT SETTINGS
binary = os.environ.get('BINARY')
validator = os.environ.get('VALIDATOR')
keyring_wallet_name = os.environ.get('KEYRING_WALLET_NAME')
keyring_password = os.environ.get('KEYRING_PASSWORD')
chain_name = os.environ.get('CHAIN_NAME')
chain_id = os.environ.get('CHAIN_ID')
denom = os.environ.get('DENOM')
node = os.environ.get('NODE')
restake_min_balance = float(os.environ.get('RESTAKE_MIN_BALANCE'))
restake_wallet_address = os.environ.get('RESTAKE_WALLET_ADDRESS')
restake_wallet_percentage = float(os.environ.get('RESTAKE_WALLET_PERCENTAGE'))
external_min_balance = float(os.environ.get('EXTERNAL_MIN_BALANCE'))
external_wallet_address = os.environ.get('EXTERNAL_WALLET_ADDRESS')
external_wallet_percentage = float(os.environ.get('EXTERNAL_WALLET_PERCENTAGE'))

print('===== Running script =======')


# GET MINTSCAN TX URL
def get_mintscan_url(tx):
    return 'https://www.mintscan.io/' + chain_name + '/txs/' + tx


# GET WALLET BALANCE
def get_wallet_balance(wallet_address):
    command = binary + ' query bank balances ' + wallet_address + ' --node ' + node + ' -o json'
    result = subprocess.run(command, shell=True, check=True, stdout=PIPE, stderr=PIPE)

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
    result = subprocess.run(command, shell=True, check=True, stdout=PIPE, stderr=PIPE)
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
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx distribution withdraw-rewards ' + validator \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' --commission' \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


# STAKE FUNCTION
def stake(stake_balance, gas_fees):
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx staking delegate ' + validator + ' ' + stake_balance + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


# Send tokens between wallets
def send_token(amount, gas_fees):
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx bank send ' + restake_wallet_address + ' ' + str(amount) \
              + ' ' + str(amount) + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


original_validator_balance = get_wallet_balance(restake_wallet_address)

print("Validator balance:" + str(original_validator_balance))

print(' -- Claim Rewards -- ')
command_result = claim_rewards(2500)

print('Claim requested...')
print(get_mintscan_url(command_result['txhash']))
print('Waiting for it to be accepted...')

time.sleep(10)

balance = get_wallet_balance(restake_wallet_address)
if original_validator_balance == balance:
    print('Validator balance was not updated. Commission probably wasn\'t accepted? Please check TX', command_result)
    exit(1)

print(' -- Claim Successful -- ')

balance -= 1000000
restake_amount = balance*restake_wallet_percentage/100
external_amount = balance*external_wallet_percentage/100

print('Your workable (balance - 1token for fees) is ' + str(balance))

if restake_amount > 0.001:
    print('You possible restake amount is ' + str(restake_amount) + denom)
if external_amount > 0.001:
    print('Your possible external amount is ' + str(external_amount) + denom)

if restake_amount < restake_min_balance or external_amount < external_min_balance:
    print('Minimums are not. Min restake balance is set to ' + str(restake_min_balance) + ' and external min balance is set to ' + str(external_min_balance))
    exit(0)

stake(restake_amount, 2500)
time.sleep(10)
send_token(external_amount, 2500)
