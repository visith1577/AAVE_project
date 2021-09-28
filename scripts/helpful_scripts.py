from brownie import network, accounts,config


LOCAL_ENVIRONMENTS = ["development", "ganache-local", "mainnet-fork", "hardhat"]


def get_account(index=None, _id=None):
    if index:
        return accounts[index]
    if _id:
        return accounts.load(_id)
    if network.show_active() in LOCAL_ENVIRONMENTS:
        return accounts[0]
    if network.show_active() in config['networks']:
        return accounts.add(config['wallets']['from_key'])
    return None