
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

def createBlockchain(nodesNumber, maliciousNumber):
    os.system("docker run -it -d --name node1 ubuntu /bin/bash")
    os.system("docker cp ../btcbin/ node1:/")
    os.system("docker exec -t node1 /btcbin/bitcoind -regtest -debug=net -daemon")

    for i in range(2, int(nodesNumber)+1):
        os.system("docker run -it -d --name node" + str(i) + " ubuntu /bin/bash")
        os.system("docker cp ../btcbin/ node" + str(i) + ":/")
        os.system("docker exec -t node" + str(i) + " /btcbin/bitcoind -regtest -debug=net -daemon")

    for i in range(int(nodesNumber)+1, int(nodesNumber)+1+int(maliciousNumber)):
        os.system("docker run -it -d --name node" + str(i) + " ubuntu /bin/bash")
        os.system("docker cp ../btcbin/ node" + str(i) + ":/")
        os.system("docker exec -t node" + str(i) + " /btcbin/bitcoind -malicious -regtest -debug=net -daemon")

    for i in range(1, int(nodesNumber)+1):
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber)+1)) + ':18444" "onetry"')
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber)+1)) + ':18444" "onetry"')

    for i in range(int(nodesNumber)+1, int(nodesNumber)+1+int(maliciousNumber)):
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber)+1)) + ':18444" "onetry"')
        os.system('docker exec -t node' + str(i) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(randint(2, int(nodesNumber)+1)) + ':18444" "onetry"')

    os.system("docker run -it -d --name nodeMonitor ubuntu /bin/bash")
    os.system("docker cp ../btcbin/ nodeMonitor:/")
    os.system("docker exec -t nodeMonitor /btcbin/bitcoind -regtest -pocmon -debug=net -daemon")

    os.system("docker run -it -d --name nodeMonitor2 ubuntu /bin/bash")
    os.system("docker cp ../btcbin/ nodeMonitor2:/")
    os.system("docker exec -t nodeMonitor2 /btcbin/bitcoind -regtest -pocmon -debug=net -daemon")
    
    os.system("docker run -it -d --name nodeMonitor3 ubuntu /bin/bash")
    os.system("docker cp ../btcbin/ nodeMonitor3:/")
    os.system("docker exec -t nodeMonitor3 /btcbin/bitcoind -regtest -pocmon -debug=net -daemon")
    
    os.system("docker run -it -d --name nodeMonitor4 ubuntu /bin/bash")
    os.system("docker cp ../btcbin/ nodeMonitor4:/")
    os.system("docker exec -t nodeMonitor4 /btcbin/bitcoind -regtest -pocmon -debug=net -daemon")
    time.sleep(5)

    for i in range(2, int(nodesNumber)+2):
        os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor2 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor3 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')
        os.system('docker exec -t nodeMonitor4 /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')

    return 

def deleteBlockchain(nodesNumber, chainType):
    for i in range(1, int(nodesNumber)+2):
        os.system("docker kill node" + str(i))
        os.system("docker rm node" + str(i))

    os.system("docker kill nodeMonitor")
    os.system("docker rm nodeMonitor")

    os.system("docker kill nodeMonitor2")
    os.system("docker rm nodeMonitor2")

    os.system("docker kill nodeMonitor3")
    os.system("docker rm nodeMonitor3")

    os.system("docker kill nodeMonitor4")
    os.system("docker rm nodeMonitor4")

    os.system("rm -rf database")
    os.system("rm potion.pyc")
    return