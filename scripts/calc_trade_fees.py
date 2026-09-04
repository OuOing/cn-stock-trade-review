#!/usr/bin/env python3
"""Estimate net P&L for Chinese A-share trades.

Each --buy/--sell value represents one charged order in PRICE:QUANTITY form.
"""

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_leg(value: str) -> tuple[Decimal, int]:
    price_text, quantity_text = value.split(":", 1)
    price = Decimal(price_text)
    quantity = int(quantity_text)
    if price <= 0 or quantity <= 0:
        raise argparse.ArgumentTypeError("price and quantity must be positive")
    return price, quantity


def commission(amount: Decimal, rate: Decimal, minimum: Decimal) -> Decimal:
    return money(max(amount * rate, minimum))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buy", action="append", required=True, type=parse_leg)
    parser.add_argument("--sell", action="append", required=True, type=parse_leg)
    parser.add_argument("--commission-rate", default=Decimal("0.0005"), type=Decimal)
    parser.add_argument("--minimum-commission", default=Decimal("5"), type=Decimal)
    parser.add_argument("--stamp-rate", default=Decimal("0.0005"), type=Decimal)
    parser.add_argument("--transfer-rate", default=Decimal("0.00001"), type=Decimal)
    args = parser.parse_args()

    buy_amounts = [price * quantity for price, quantity in args.buy]
    sell_amounts = [price * quantity for price, quantity in args.sell]
    buy_total = sum(buy_amounts, Decimal(0))
    sell_total = sum(sell_amounts, Decimal(0))

    buy_commission = sum(
        (commission(amount, args.commission_rate, args.minimum_commission) for amount in buy_amounts),
        Decimal(0),
    )
    sell_commission = sum(
        (commission(amount, args.commission_rate, args.minimum_commission) for amount in sell_amounts),
        Decimal(0),
    )
    transfer_fee = money((buy_total + sell_total) * args.transfer_rate)
    stamp_duty = money(sell_total * args.stamp_rate)
    total_fees = buy_commission + sell_commission + transfer_fee + stamp_duty
    gross_profit = sell_total - buy_total
    net_profit = gross_profit - total_fees
    invested = buy_total + buy_commission + money(buy_total * args.transfer_rate)
    net_return = net_profit / invested if invested else Decimal(0)

    result = {
        "buy_amount": str(money(buy_total)),
        "sell_amount": str(money(sell_total)),
        "gross_profit": str(money(gross_profit)),
        "buy_commission": str(money(buy_commission)),
        "sell_commission": str(money(sell_commission)),
        "stamp_duty": str(stamp_duty),
        "transfer_fee": str(transfer_fee),
        "total_fees": str(money(total_fees)),
        "net_profit": str(money(net_profit)),
        "net_return_percent": str((net_return * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
