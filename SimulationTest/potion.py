
#################################################
#                                               #
# ATOM: proof of connection                     #
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
from random import choice

def createBlockchain(nodesNumber, maliciousNumber):
    for i in range(1, int(nodesNumber)+1):
        print "ADD node"+str(i)
        os.system("docker run -it -d --name node" + str(i) + " ubuntu /bin/bash >/dev/null")
        os.system("docker cp ../btcbin/ node" + str(i) + ":/")
        os.system("docker exec -t node" + str(i) + " /btcbin/bitcoind -regtest -debug=net -daemon >/dev/null")

    for i in range(int(nodesNumber)+1, int(nodesNumber)+1+int(maliciousNumber)):
        print "ADD MALICIOUS node"+str(i)
        os.system("docker run -it -d --name node" + str(i) + " ubuntu /bin/bash >/dev/null")
        os.system("docker cp ../btcbin/ node" + str(i) + ":/")
        os.system("docker exec -t node" + str(i) + " /btcbin/bitcoind -malicious -regtest -debug=net -daemon >/dev/null")

    numMonitors = 4
    for i in range(1, numMonitors):
        print "ADD nodeMonitor"+str(i)
        os.system("docker run -it -d --name nodeMonitor"+i+"ubuntu /bin/bash")
        os.system("docker cp ../btcbin/ nodeMonitor:/")
        os.system("docker exec -t nodeMonitor /btcbin/bitcoind -regtest -pocmon -debug=net -daemon >/dev/null")
        time.sleep(1)

    time.sleep(5)

    totnodes = int(nodesNumber)+1+int(maliciousNumber)
    
    # Connect monitors
    for i in range(2, totnodes+1):
        os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor2 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor3 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor4 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')

    # Connect peers
    peers = {}
    for i in range(1, totnodes):
        peers[i] = [i]
    for i in range(1, totnodes):
        for _ in range(3):
            try:
                pto = choice([r for r in range(1,totnodes) if r not in peers[i] ])
                print "node"+str(i)+"-->"+"node"+str(pto)
                os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(pto+1) + ':18444" "onetry"')
                peers[i].append(pto)
                peers[pto].append(i)
            except:
                print "ERR: could not connect node"+str(i) #TODO: handle this 
    print peers

    return 

def deleteBlockchain(nodesNumber, chainType):
    os.system("docker stop $(docker ps -a -q)")
    os.system("docker rm $(docker ps -a -q)")

    os.system("rm -rf database")
    os.system("rm potion.pyc")
    return