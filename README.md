# Tedcrypto Validator Commission Scripts

This are scripts to promote validators commissions and what you do with it.

The most generic use-case will be restake commission so you self-delegate
and earn more with your rewards.

## Prepare

You need to install some libraries before being able to run all the scripts

```shell
sudo apt-get update && sudo apt-get install python3-pip python3 -y \
 && pip3 install -r requirements.txt
```

You need to copy and fill .env file

```shell
BINARY -- Your node binary
VALIDATOR -- Validator address, usually has valoper in it
KEYRING_WALLET_NAME -- Your wallet name from keyring
KEYRING_PASSWORD -- Password to open keyring
CHAIN_NAME -- Chain name (for mintscan purposes)
CHAIN_ID -- Chain id 
DENOM -- Denomination the `u` version e.g. utoken
GAS_FEES -- The gas fees to be used as default on your commands
NODE -- Can be public, one of your nodes or http://localhost:26657 if you are running locally
VALIDATOR_WALLET_ADDRESS -- Validator wallet address
KEEP_BALANCE -- Amount of tokens you want to keep to pay for TXs and such
```

## Configuration

You will need to also configure your tasks, e.g.: stake and payments

Copy the `configuration.yaml.dist` to `configuration.yaml`

You can configure `payments` and `stake` you can stake to multiple
validators and you can send/pay to multiple wallets. As of now
it only works with percentages and the sum of those percentages need to 
be equal to `100%`


## Example of script working

![image](https://user-images.githubusercontent.com/3440849/168132499-76d0f917-9352-4deb-b324-280a1e02e6da.png)

