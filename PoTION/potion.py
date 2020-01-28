
#################################################
#                                               #
# PoTION: Proof of connecTION                   #
#                                               #
# Authors:                                      #
# Vanesa Daza - vanesa.daza@upf.edu             #
# Federico Franzoni - federico.franzoni@upf.edu #
# Xavier Salleras - xavier.salleras@upf.edu     #
#                                               #
#################################################

import os
import time
from random import randint

def createBlockchain(nodesNumber):
    os.system("docker run -it -d --name node1 ubuntu /bin/bash")
    os.system("docker cp ../btcbin node1:/")
    os.system("docker exec -t node1 /btcbin/bitcoind -regtest -debug=net -daemon")
    #os.system("docker exec -t node1 apt update")
    #os.system("docker exec -t node1 apt install net-tools -y")

    #ip = os.popen("docker exec -t node1 ifconfig | grep -o '172.17.0[^ ]*'").read()
    #ipParsed = ip[:len(ip)-1]
    ipParsed = "172.17.0.2"
    addresses = []

    address = os.popen("docker exec -t node1 /btcbin/bitcoin-cli -regtest getnewaddress").read()

    addresses.append(address[:len(address)])
    f = open('database/addresses', 'a+')
    f.write(address)

    for i in range(2, int(nodesNumber) + 1):
        os.system("docker run -it -d --name node" + str(i) + " ubuntu /bin/bash")
        os.system("docker cp ../btcbin node" + str(i) + ":/")
        os.system("docker exec -t node" + str(i) + " /btcbin/bitcoind -regtest -debug=net -daemon")

    for i in range(2, int(nodesNumber) + 1):
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber))) + ':18444" "onetry"')
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber))) + ':18444" "onetry"')
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber))) + ':18444" "onetry"')
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber))) + ':18444" "onetry"')

        address = os.popen("docker exec -t node" + str(i) + " /btcbin/bitcoin-cli -regtest getnewaddress").read()
        addresses.append(address)
        f.write(address)

    os.system("docker run -it -d --name nodeMonitor ubuntu /bin/bash")
    os.system("docker cp ../btcbin nodeMonitor:/")
    os.system("docker exec -t nodeMonitor /btcbin/bitcoind -regtest -pocmon -debug=net -daemon")
    time.sleep(5)

    for i in range(2, int(nodesNumber) + 2):
        os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')

    address = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getnewaddress").read()
    f.write(address)
    
    f.close()

    os.system("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest generatetoaddress 101 " + address)
    time.sleep(5)

    while True:
        for i in range(1, int(nodesNumber) + 1):
            os.system("docker exec -t node" + str(i) + " /btcbin/bitcoin-cli -regtest generatetoaddress " + str(randint(30, 50)) + " " + addresses[i-1])	
            time.sleep(5)

        for i in range(1, int(nodesNumber) + 1):
            j = randint(0, len(addresses)-1)

            while(i == j+1):
                j = randint(0, len(addresses)-1)	
                os.system("docker exec -t node" + str(i) + " /btcbin/bitcoin-cli -regtest sendtoaddress " + addresses[j] + " 1.00")
                time.sleep(5)

            os.system("docker exec -t node" + str(i) + " /btcbin/bitcoin-cli -regtest generatetoaddress 1 " + address[i-1])	
            time.sleep(15)
    return 

def deleteBlockchain(nodesNumber, chainType):
    for i in range(1, int(nodesNumber) + 1):
        os.system("docker kill node" + str(i))
        os.system("docker rm node" + str(i))

    os.system("docker kill nodeMonitor")
    os.system("docker rm nodeMonitor")

    os.system("rm -rf database")
    os.system("rm potion.pyc")
    return

def getBalances(nodesNumber):
    print ""
    balance = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getbalance").read()
    print "nodeMonitor: " + balance[:len(balance)-1]

    for i in range(1, int(nodesNumber) + 1):
        balance = os.popen("docker exec -t node" + str(i) + " /btcbin/bitcoin-cli -regtest getbalance").read()
        print "node" + str(i) + ": " + balance[:len(balance)-1]

    print ""
    return