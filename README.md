# proof-of-connection-poc
Proof of Concept of the Proof of Connection (POC) protocol

## Bitcoin Core
Binaries of Bitcon Core implementing the POC protocol are in the 'btcbin' folder

Source code can be found at https://github.com/frz-dev/bitcoin-autodaps/tree/proof-of-connection

## Test
Usage:
`./poc-test.sh NUMNODES NUMCONNECTIONS`  

The script creates `NUMNODES` nodes and `NUMCONNECTIONS` random connections between nodes.

Data is stored in a folder named `poctest`.  
WARNING: If the folder exists, it will be DELETED.