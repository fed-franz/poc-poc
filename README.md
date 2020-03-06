## AToM Simulation setup

Files for performing the setup using docker are placed into the `/SimulationTest` folder. 

### Usage

```
sudo python main.py [OPTION] [arg]
```
Where [OPTION] can be:

-s : Creates a bitcoin blockchain of [arg] nodes, placed into different docker containers. The nodes are connected randomly between them, whereas there is a non-connected node called nodeMonitor. Other nodes are called nodeX where X is an incremental number. Moreover, every node randomly mines blocks and sends fundings to other nodes randomly selected.

-d : Deletes the bitcoin blockchain and all the containers.

-b : Prints the bitcoin balances of the nodes.

-a : Prints the bitcoin addresses of the nodes.


## Bitcoin Core
Binaries of Bitcon Core implementing the POC protocol are in the 'btcbin' folder

Source code can be found [here](https://github.com/frz-dev/bitcoin-autodaps/tree/proof-of-connection). 

## SimpleTest
Usage:
`./poc-test.sh NUMNODES NUMCONNECTIONS`  

The script creates `NUMNODES` nodes and `NUMCONNECTIONS` random connections between nodes.

Data is stored in a folder named `poctest`.  
WARNING: If the folder exists, it will be DELETED.
