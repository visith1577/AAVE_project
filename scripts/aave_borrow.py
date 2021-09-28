from brownie import network, config, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3

Amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config['networks'][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()

    lending_pool = get_lending_pool()
    approve_erc20(Amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, Amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited..!!")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Borrowing Dai.")
    dai_eth_price = get_asset_price(config['networks'][network.show_active()]["dai_eth_price_feed"])
    amount_of_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_of_dai_to_borrow}")
    dai_address = config['networks'][network.show_active()]["dai_token"]
    borrow_dai = lending_pool.borrow(dai_address, Web3.toWei(amount_of_dai_to_borrow, "ether"),
                                     1,
                                     0,
                                     account.address, {"from" : account})
    borrow_dai.wait(1)
    print("We borrowed some ETH")
    get_borrowable_data(lending_pool, account)
    repay_all(Amount, lending_pool, account)
    print("You just deposited, borrowed and repayed with Aave")


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config['networks'][network.show_active()]['lending_pool_addresses_provider']
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 .....")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!!!")
    return tx


def get_borrowable_data(lending_pool, account):
    (
        total_collateral,
        total_debt,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.toWei(available_borrow_eth, "ether")
    total_collateral = Web3.toWei(total_collateral, "ether")
    total_debt = Web3.toWei(total_debt, "ether")
    print(f"You have {total_collateral} worth of ETH deposited")
    print(f"You have {total_debt} worth of ETH borrowed")
    print(f"You can borrow {available_borrow_eth} worth of ETH")
    return float(available_borrow_eth), float(total_debt)


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    print(f"DAI/ETH price is {Web3.fromWei(latest_price, 'ether')}")
    return float(latest_price)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config['network'][network.show_active()]["dai_token"],
        account
    )
    repay_tx = lending_pool.repay(
        config['network'][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account}
    )
    repay_tx.wait(1)
    print("Repayed...!!!")