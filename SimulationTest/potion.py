
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

numMonitors = 4

def runNode(name,opts):
    print "ADD "+name+" ("+opts+")"
    os.system("docker run -it -d --name "+name+ " ubuntu /bin/bash >/dev/null") #--net atomnet
    os.system("docker cp ../btcbin/ "+name+":/")
    os.system("docker exec -t "+name+" /btcbin/bitcoind -regtest "+opts+" -debug=net -nodebuglogfile -daemon >/dev/null")

def createBlockchain(nodesNumber, maliciousNumber):
    print "CREATING NETWORK: "+str(nodesNumber)+" nodes + "+str(maliciousNumber)+" malicious"

    # try:
    #     os.system( "docker network create --subnet=172.18.0.0/16 atomnet" )
    # except:
    #     pass

    for i in range(1, int(nodesNumber)+1):
        runNode("node"+str(i),"")

    for i in range(int(nodesNumber)+1, int(nodesNumber)+1+int(maliciousNumber)):
        runNode("node"+str(i),"-malicious")

    for i in range(1, numMonitors+1):
        runNode("nodeMonitor"+str(i),"-pocmon")

    totnodes = int(nodesNumber)+1+int(maliciousNumber)
    
    # Connect monitors
    for m in range(1,numMonitors+1):
        print "Connecting nodeMonitor"+str(m)
        for i in range(2, totnodes+1):
            os.system('docker exec -t nodeMonitor'+str(m)+' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(i) + ':18444" "onetry"')

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
    # print peers

    return 

def deleteBlockchain():
    os.system("docker stop $(docker ps -a -q) >/dev/null")
    os.system("docker rm $(docker ps -a -q) >/dev/null")

    os.system("rm potion.pyc")
    return