# Crypto-Balances
Command line tool to display multiple cryptocurrency balances for specified addresses

## Examples
```

# Add single address by type
python cryptobalances.py -a btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v
python cryptobalances.py -a xcp 1Co1dcFX6u1wQ8cW8mnj1DEgW7xQMEaChD

# Remove single address by type
python cryptobalances.py -r btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v
python cryptobalances.py -r xcp 1Co1dcFX6u1wQ8cW8mnj1DEgW7xQMEaChD

# Add multiple addresses by type
python cryptobalances.py -a btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v 3Kg7Cmooris7cLErTsijq6qR1FH3cTiK2G
python cryptobalances.py -a xcp 1Co1dcFX6u1wQ8cW8mnj1DEgW7xQMEaChD 1EjnVKygHrwvzdZdEQYnTKKH6yjeVbDEuZ

# Remove multiple addresses by type
python cryptobalances.py -a btc 3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v 3Kg7Cmooris7cLErTsijq6qR1FH3cTiK2G
python cryptobalances.py -a xcp 1Co1dcFX6u1wQ8cW8mnj1DEgW7xQMEaChD 1EjnVKygHrwvzdZdEQYnTKKH6yjeVbDEuZ

# Print asset balances for each address individually
python cryptobalances.py -i

```
