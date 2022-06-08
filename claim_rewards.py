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
gas_fees = float(os.environ.get('GAS_FEES'))
restake_min_balance = float(os.environ.get('RESTAKE_MIN_BALANCE'))
restake_wallet_address = os.environ.get('RESTAKE_WALLET_ADDRESS')
restake_wallet_percentage = float(os.environ.get('RESTAKE_WALLET_PERCENTAGE'))
external_min_balance = float(os.environ.get('EXTERNAL_MIN_BALANCE'))
external_wallet_address = os.environ.get('EXTERNAL_WALLET_ADDRESS')
external_wallet_percentage = float(os.environ.get('EXTERNAL_WALLET_PERCENTAGE'))

print('===== Running script =======\n')

total_percentage = restake_wallet_percentage + external_wallet_percentage
if total_percentage > 100:
    print('Restake and withdraw cannot be bigger than 100%!')
    exit(1)


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

    inner_command_result = {}
    for line in stdout.splitlines():
        try:
            inner_command_result[line.split(':')[0].strip()] = line.split(':')[1].strip()
        except:
            print('Stdout is not as expected. Different issue?', stdout, line)
            exit(1)

    if 'raw_log' not in inner_command_result:
        print("Error: Raw log not found", command, inner_command_result)
        exit(1)

    if inner_command_result['raw_log'] != "'[]'":
        print("Error: Raw log provided... ", command, inner_command_result)
        exit(1)

    return inner_command_result


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
              + binary + ' tx staking delegate ' + validator + ' ' + format(stake_balance, 'f') + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' -y --fees ' + format(gas_fees, 'f') + denom

    return run_command(command)


# Send tokens between wallets
def send_token(amount, gas_fees):
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx bank send ' + restake_wallet_address + ' ' + external_wallet_address \
              + ' ' + format(amount, 'f') + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' -y --fees ' + format(gas_fees, 'f') + denom

    return run_command(command)


# Wait for changes on the wallet balance
def wait_for_wallet_balance(wait_original_balance, wait_attempts):
    wait_attempts_count = 0
    wait_current_balance = get_wallet_balance(restake_wallet_address)
    while wait_attempts_count < wait_attempts and wait_original_balance == wait_current_balance:
        print('Validator balance was not updated... trying again in 10 seconds...')
        time.sleep(10)
        wait_current_balance = get_wallet_balance(restake_wallet_address)
        wait_attempts_count += 1

    if wait_original_balance == wait_current_balance:
        print('Validator balance was not updated has expected')
        exit(1)


if __name__ == '__main__':
    original_validator_balance = get_wallet_balance(restake_wallet_address)
    print("Validator balance:" + str(original_validator_balance) + '\n\n')

    print(' -- Claim Rewards -- ')
    command_result = claim_rewards(gas_fees)
    print('Claim requested...')
    print(get_mintscan_url(command_result['txhash']))
    print('Waiting for it to be accepted...')

    time.sleep(10)

    attempts = 0
    balance = get_wallet_balance(restake_wallet_address)
    while attempts < 3 and original_validator_balance == balance:
        print('Validator balance was not updated... trying again in 10 seconds...')
        time.sleep(10)
        balance = get_wallet_balance(restake_wallet_address)
        attempts += 1

    if original_validator_balance == balance:
        print('Validator balance was not updated. Commission probably wasn\'t accepted? Please check TX', command_result)
        exit(1)

    print(' -- Claim Successful -- \n')

    print(' -- Stake and Send -- ')

    balance -= 1000000
    restake_amount = balance*restake_wallet_percentage/100
    external_amount = balance*external_wallet_percentage/100

    print('Your workable (balance - 1token for fees) is ' + format(balance, 'f') + denom)

    if restake_amount > 0.001:
        print('You possible restake amount is ' + format(restake_amount, 'f') + denom)
    if external_amount > 0.001:
        print('Your possible external amount is ' + format(external_amount, 'f') + denom)

    if (0.001 < restake_amount < restake_min_balance) or (0.001 < external_amount < external_min_balance):
        print('Minimums are not. Min restake balance is set to ' + format(restake_min_balance, 'f') +
              ' and external min balance is set to ' + format(external_min_balance, 'f'))
        exit(0)

    if restake_amount > 0.001:
        balance_before_restake = get_wallet_balance(restake_wallet_address)
        print('Staking ' + format(restake_amount, 'f') + denom + ' please wait...')
        command_result = stake(restake_amount, gas_fees)
        print(get_mintscan_url(command_result['txhash']))
        time.sleep(10)
        wait_for_wallet_balance(balance_before_restake, 5)

    if external_amount > 0.001:
        print('Sending ' + format(external_amount, 'f') + denom + ' to external wallet please wait...')
        command_result = send_token(external_amount, gas_fees)
        print(get_mintscan_url(command_result['txhash']))
        time.sleep(10)

    print(' -- Stake and Send Completed -- \n')
