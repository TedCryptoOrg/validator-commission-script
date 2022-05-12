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
NODE -- Can be public, one of your nodes or http://localhost:26657 if you are running locally
RESTAKE_MIN_BALANCE -- Min balance you want to restake, to avoid paying high fees for small amounts (default: 10000)
RESTAKE_WALLET_ADDRESS -- Usually your validator address (commission wallet)
RESTAKE_WALLET_PERCENTAGE -- Percentage of commission you want to restake (0 - 100)
EXTERNAL_MIN_BALANCE -- Min balance you want to move out (default: 10000)
EXTERNAL_WALLET_ADDRESS -- External wallet, can be one you delegate outside your node
EXTERNAL_WALLET_PERCENTAGE -- Percentage of comission you want to move out (0 - 100)
```

Special conditions:
 - If the min balance is not met for restake or external move then no stake and external will be done

## Example of script working

![image](https://user-images.githubusercontent.com/3440849/168132499-76d0f917-9352-4deb-b324-280a1e02e6da.png)

