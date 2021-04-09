# Crypto Bot

Simple bot to automate crypto trades. Strategy revolves around the MACD indicator. When the MACS crosses above the signal line, the bot will attempt to open a long position in BTC. When the MACD crosses below the signal and BTC is currently held, the bot will attempt to sell all held BTC as long as the current bid price is above the cost basis + fees. Written in python with pandas and numpy libraries for data manipulation. Backtesting for BTCUSD on 1 minute time period over the last year shows an annualized return of about 444%. Account integration via coinbase pro API. Ability to track account balances and place orders via Coinbase pro API key. Uses python requests for rest API requests and responses.
## Disclaimer

## Usage

## Analysis

## Testing

## Build
