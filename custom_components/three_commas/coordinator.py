"""DataUpdateCoordinator for three_commas."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ThreeCommasApiClient,
    ThreeCommasApiClientAuthenticationError,
    ThreeCommasApiClientCommunicationError,
    ThreeCommasApiClientError,
)
from .const import DOMAIN, LOGGER


class ThreeCommasDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        client: ThreeCommasApiClient,
        update_interval: timedelta,
        config_entry=None,
    ) -> None:
        """Initialize."""
        self.client = client
        self.config_entry = config_entry

        super().__init__(
            hass=hass,
            logger=logger,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            data = {}

            # Fetch bot stats data
            bot_stats = await self.client.async_get_bot_stats()

            # Log the full response for debugging
            LOGGER.debug("Bot stats data: %s", bot_stats)

            # Verify that the expected data structure is present
            if not bot_stats or "profits_in_usd" not in bot_stats:
                LOGGER.warning(
                    "Missing expected data structure in bot stats response: %s",
                    bot_stats,
                )
                data["profit_data"] = {}
            else:
                # Create a simplified data structure with just the profit values
                data["profit_data"] = {
                    "overall_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "overall_usd_profit"
                    ),
                    "today_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "today_usd_profit"
                    ),
                    "active_deals_usd_profit": bot_stats.get("profits_in_usd", {}).get(
                        "active_deals_usd_profit"
                    ),
                    "funds_locked_in_active_deals": bot_stats.get(
                        "profits_in_usd", {}
                    ).get("funds_locked_in_active_deals"),
                }

            # Fetch accounts data
            accounts = await self.client.async_get_accounts()

            # Log the full response for debugging
            # LOGGER.debug("Accounts data: %s", accounts)

            # Process accounts data
            if accounts:
                data["accounts"] = {}
                data["bots"] = {}

                for account in accounts:
                    account_id = account.get("id")
                    if account_id:
                        data["accounts"][account_id] = {
                            "id": account_id,
                            "name": account.get("name", "Unknown Account"),
                            "exchange_name": account.get(
                                "exchange_name", "Unknown Exchange"
                            ),
                            "usd_amount": account.get("usd_amount", 0),
                            "market_code": account.get("market_code", "unknown"),
                        }

                        # Fetch bots for this account
                        try:
                            account_bots = await self.client.async_get_bots(
                                account_id=account_id
                            )
                            LOGGER.debug(
                                "Bots for account %s: %s", account_id, account_bots
                            )

                            # Store bots by account ID
                            if account_bots:
                                if account_id not in data["bots"]:
                                    data["bots"][account_id] = []

                                # Process each bot
                                total_account_investment = 0.0
                                for bot in account_bots:
                                    # Calculate investment amount
                                    base_order_volume = bot.get(
                                        "base_order_volume", "0.0"
                                    )
                                    safety_order_volume = bot.get(
                                        "safety_order_volume", "0.0"
                                    )
                                    max_safety_orders = int(
                                        bot.get("max_safety_orders", 0)
                                    )
                                    max_active_deals = int(
                                        bot.get("max_active_deals", 1)
                                    )
                                    martingale_volume_coefficient = float(
                                        bot.get("martingale_volume_coefficient", "1.0")
                                    )
                                    leverage_custom_value = bot.get(
                                        "leverage_custom_value"
                                    )

                                    investment_amount = 0.0
                                    try:
                                        # Extract numeric values
                                        base_numeric = float(
                                            base_order_volume.split(" ")[0]
                                            if " " in base_order_volume
                                            else base_order_volume
                                        )
                                        safety_numeric = float(
                                            safety_order_volume.split(" ")[0]
                                            if " " in safety_order_volume
                                            else safety_order_volume
                                        )

                                        # Calculate total safety order volume
                                        total_safety_volume = (
                                            safety_numeric * max_safety_orders
                                        )

                                        # Calculate single deal investment
                                        single_deal_investment = (
                                            base_numeric + total_safety_volume
                                        )

                                        # Total investment for all active deals
                                        total_investment = (
                                            single_deal_investment * max_active_deals
                                        )

                                        # Apply leverage if applicable
                                        if (
                                            leverage_custom_value
                                            and float(leverage_custom_value) > 0
                                        ):
                                            investment_amount = (
                                                total_investment
                                                / float(leverage_custom_value)
                                            )
                                        else:
                                            investment_amount = total_investment

                                    except (ValueError, TypeError, AttributeError) as e:
                                        LOGGER.error(
                                            "Error calculating investment amount: %s", e
                                        )

                                    # Log the investment amount
                                    LOGGER.info(
                                        "Bot %s investment amount: %s",
                                        bot.get("name", "Unknown"),
                                        investment_amount,
                                    )

                                    # Add bot to the account's bot list
                                    bot_data = {
                                        **bot,
                                        "investment_amount": investment_amount,
                                    }
                                    data["bots"][account_id].append(bot_data)

                                    # Add to account total
                                    total_account_investment += investment_amount

                                # Log the total investment for this account
                                account_name = data["accounts"][account_id].get(
                                    "name", "Unknown Account"
                                )
                                exchange_name = data["accounts"][account_id].get(
                                    "exchange_name", "Unknown Exchange"
                                )

                                # Get account balance directly from stored data
                                account_balance_raw = data["accounts"][account_id].get(
                                    "usd_amount", 0
                                )
                                account_balance = 0.0

                                # Convert to float if needed
                                try:
                                    if (
                                        isinstance(account_balance_raw, dict)
                                        and "amount" in account_balance_raw
                                    ):
                                        account_balance = float(
                                            str(account_balance_raw["amount"])
                                        )
                                    else:
                                        account_balance = float(
                                            str(account_balance_raw)
                                        )
                                except (ValueError, TypeError) as e:
                                    LOGGER.error(
                                        "Error converting account balance to float: %s",
                                        e,
                                    )

                                # Calculate percentage utilization
                                utilization_percentage = 0.0
                                if account_balance > 0:
                                    utilization_percentage = (
                                        total_account_investment / account_balance
                                    ) * 100
                                    # Round to two decimal places
                                    utilization_percentage = round(
                                        utilization_percentage, 2
                                    )

                                # Log comprehensive account information
                                LOGGER.info(
                                    "Account summary for %s (%s) on %s: "
                                    "Balance: $%.2f | "
                                    "Investment: $%.2f | "
                                    "Utilization: %.2f%%",
                                    account_id,
                                    account_name,
                                    exchange_name,
                                    account_balance,
                                    total_account_investment,
                                    utilization_percentage,
                                )

                                # Store the total investment amount in the account data
                                data["accounts"][account_id][
                                    "total_investment_amount"
                                ] = total_account_investment
                                data["accounts"][account_id][
                                    "utilization_percentage"
                                ] = utilization_percentage

                        except Exception as e:
                            LOGGER.error(
                                "Error fetching bots for account %s: %s", account_id, e
                            )

            return data

        except ThreeCommasApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ThreeCommasApiClientCommunicationError as exception:
            LOGGER.error("Communication error: %s", exception)
            raise UpdateFailed(exception) from exception
        except ThreeCommasApiClientError as exception:
            LOGGER.error("Unknown error: %s", exception)
            raise UpdateFailed(exception) from exception
