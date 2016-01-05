# Crypto-Balances
Command line tool to display multiple cryptocurrency balances for specified addresses

## Examples
```
# Add/remove single address by type
cryptobalances.py address --add btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v
cryptobalances.py address --remove btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v

# Add/remove multiple addresses by type
cryptobalances.py address --add btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v 3Kg7Cmooris7cLErTsijq6qR1FH3cTiK2G
cryptobalances.py address --remove btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v 3Kg7Cmooris7cLErTsijq6qR1FH3cTiK2G

# Add/remove assets from exclusion list (prevents them from being included in balances)
cryptobalances.py exclusion --add ZEROVALUECOIN
cryptobalances.py exclusion --remove ZEROVALUECOIN

# Add/remove multiple assets from exclusion list
cryptobalances.py exclusion --add ZEROVALUECOIN SPAMCOIN
cryptobalances.py exclusion --remove ZEROVALUECOIN SPAMCOIN

# Display itemized balances for each address asset
cryptobalances.py --itemize

# Change base denomination used to display asset values
cryptobalances.py base USD

# Display currently added addresses for each address type
cryptobalances.py address

# Display currently excluded assets
cryptobalances.py exclusion
```
