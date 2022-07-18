import json
import os
import subprocess
import time
import yaml

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
validator_wallet_address = os.environ.get('VALIDATOR_WALLET_ADDRESS')

print('===== Running script =======\n')

with open("configuration.yaml", 'r') as stream:
    configuration_data = yaml.safe_load(stream)

# Make sure that the percentage between all tasks are 100% of the funds
total_percentage = 0
if 'stake' in configuration_data['tasks']:
    for task in configuration_data['tasks']['stake']:
        total_percentage += task['percentage']
if 'payments' in configuration_data['tasks']:
    for task in configuration_data['tasks']['payments']:
        total_percentage += int(task['percentage'])

if total_percentage != 100:
    print('Percentages do not match. Total: ', total_percentage)
    exit(1)


# GET MINTSCAN TX URL
def get_mintscan_url(tx):
    return 'https://www.mintscan.io/' + chain_name + '/txs/' + tx


# GET WALLET BALANCE
def get_wallet_balance(wallet_address):
    command = binary + ' query bank balances ' + wallet_address + ' --node ' + node + ' -o json'
    result = None
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=PIPE, stderr=PIPE)
    except subprocess.CalledProcessError as e:
        print("Error running command \n", command, "\n Output: \n", e.stderr.decode('utf-8'))
        exit(1)
    stdout = result.stdout.decode('utf-8')

    if result.returncode != 0:
        print("Error. Command: ", command, stdout)
        exit(1)

    balance_object = json.loads(stdout)
    if 'balances' not in balance_object:
        print("Balance object is not as expected.", balance_object)
        exit(1)

    return float(balance_object['balances'][0]['amount'])


# RUN COMMAND
def run_command(command):
    result = None
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=PIPE, stderr=PIPE)
    except subprocess.CalledProcessError as e:
        print("Error running command \n", command, "\n Output: \n", e.stderr.decode('utf-8'))
        exit(1)
    stdout = result.stdout.decode('utf-8')
    if result.returncode != 0:
        print("Error. Command: ", command, stdout)
        exit(1)

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
              + ' --gas auto' \
              + ' -y --fees ' + str(gas_fees) + denom

    return run_command(command)


# STAKE FUNCTION
def stake(address, stake_balance, gas_fees):
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx staking delegate ' + address + ' ' + format(stake_balance, 'f') + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' --gas auto' \
              + ' -y --fees ' + format(gas_fees, 'f') + denom

    return run_command(command)


# Send tokens between wallets
def send_token(address, amount, gas_fees):
    command = 'echo -e "' + keyring_password + "\n" + keyring_password + '\n" | ' \
              + binary + ' tx bank send ' + validator_wallet_address + ' ' + address \
              + ' ' + format(amount, 'f') + denom \
              + ' --chain-id ' + chain_id \
              + ' --node ' + node \
              + ' --from ' + keyring_wallet_name \
              + ' --gas auto' \
              + ' -y --fees ' + format(gas_fees, 'f') + denom

    return run_command(command)


# Wait for changes on the wallet balance
def wait_for_wallet_balance(wait_original_balance, wait_attempts):
    wait_attempts_count = 0
    wait_current_balance = get_wallet_balance(validator_wallet_address)
    while wait_attempts_count < wait_attempts and wait_original_balance == wait_current_balance:
        print('Validator balance was not updated... trying again in 60 seconds...')
        time.sleep(10)
        wait_current_balance = get_wallet_balance(validator_wallet_address)
        wait_attempts_count += 1

    if wait_original_balance == wait_current_balance:
        print('Validator balance was not updated has expected')
        exit(1)

    return wait_current_balance


if __name__ == '__main__':
    original_validator_balance = get_wallet_balance(validator_wallet_address)
    print("Validator balance:" + format(original_validator_balance, 'f') + '\n\n')

    print(' -- Claim Rewards -- ')
    command_result = claim_rewards(gas_fees)
    print('Claim requested...')
    print(get_mintscan_url(command_result['txhash']))
    print('Waiting for it to be accepted...')

    time.sleep(10)

    balance = wait_for_wallet_balance(original_validator_balance, 4)

    print(' -- Claim Successful -- \n')

    print(' -- Running tasks -- ')

    balance -= 1000000

    print('Your workable (balance - 1token for fees) is ' + format(balance, 'f') + denom)

    # Check if tasks have any stake that needs to be done
    if 'stake' in configuration_data['tasks']:
        for task in configuration_data['tasks']['stake']:
            balance_before_task = get_wallet_balance(validator_wallet_address)
            task_amount = balance * task['percentage'] / 100
            print('Staking ' + format(task_amount, 'f') + denom + ' to validator ' + task['address'])
            command_result = stake(task['address'], task_amount, gas_fees)
            print('Stake requested...')
            print(get_mintscan_url(command_result['txhash']))
            print('Waiting for it to be accepted...')

            time.sleep(10)

            wait_for_wallet_balance(balance_before_task, 4)

    # Check if tasks have any payment that needs to be sent
    if 'payments' in configuration_data['tasks']:
        for task in configuration_data['tasks']['payments']:
            balance_before_task = get_wallet_balance(validator_wallet_address)
            task_amount = balance * task['percentage'] / 100
            print('Sending ' + format(task_amount, 'f') + denom + ' to ' + task['address'])
            command_result = send_token(task['address'], task_amount, gas_fees)
            print('Payment requested...')
            print(get_mintscan_url(command_result['txhash']))
            print('Waiting for it to be accepted...')

            time.sleep(10)

            wait_for_wallet_balance(balance_before_task, 4)

    print(' -- Tasks Completed -- \n')
