# -*- coding: utf-8 -*-

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

import sys
from subprocess import Popen
import potion
import os
import json
import time
import random

def main():
    if (len(sys.argv) < 2):
        print "\nUSAGE:\n"
        print "sudo python main.py [OPTION] [arg]\n"
        print "Where 'a' means:"
        print "-s : Create and populate a bitcoin blockchain of [arg] nodes where [arg2] malicious."
        print "-d : Delete bitcoin blockchain."
        print "-b : Get balances of the nodes."
        print "-a : Retrieve addresses of nodes."
        print "-t : Test everything for [arg] nodes."
        print ""

    else:
        if (sys.argv[1] == '-s'):
            nodes = sys.argv[2]
            malicious = sys.argv[3]
            os.system("mkdir database")
            f = open('database/bitcoin', 'w')
            f.write(nodes)
            f.close()

            command = "nohup python -c 'import potion; potion.createBlockchain(" + nodes + ", " + malicious + ")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

            print "\nCreating blockchain...\n"
	
            items = list(range(1, int(nodes)))
            l = len(items)
            for i, item in enumerate(items):
                while True:
                    if (os.popen("docker ps | grep -oP node" + str(i+1)).read()):
                        printProgressBar(i + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                        break

            while True:
                if (os.popen("docker ps | grep -oP nodeMonitor").read()):
                    printProgressBar(l + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                    break

        if (sys.argv[1] == '-d'):
            f = open('database/bitcoin', 'r')
            command = "nohup python -c 'import potion; potion.deleteBlockchain(" + f.read() + ", \"s\")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            f.close()

        if (sys.argv[1] == '-b'):
            f = open('database/bitcoin', 'r')
            potion.getBalances(f.read())
            f.close()

        if (sys.argv[1] == '-a'):
            f = open('database/bitcoin', 'r')
            with open("database/addresses", "r") as ins:
                it = 1
                snodes = int(f.read())
                print ""
                for line in ins:
                    if (snodes < it ):
                        print "Address Monitor: " + line[:len(line)-1]
                    else:
                        print "Address " + str(it) + ": " + line[:len(line)-1]
                        it += 1
            print ""

        if (sys.argv[1] == '-t'):
            nodes = int(sys.argv[2])
            nodesNew = nodes
            f = open("results.txt", "w")
            f.write("Test results. Format [<minute>] <correct_connections> | <poc_verified_connections> :\n")

            for i in range(0,10):

                what = random.randint(0,1)
                if (what):
                    change = str(random.randint(1, nodes))
                    os.system("docker kill node" + str(change))
                    os.system("docker rm node" + str(change))
                else:
                    nodesNew += 1
                    os.system("docker run -it -d --name node" + str(nodesNew) + " ubuntu /bin/bash")
                    os.system("docker cp ../btcbin node" + str(nodesNew) + ":/")
                    os.system("docker exec -t node" + str(nodesNew) + " /btcbin/bitcoind -regtest -debug=net -daemon")
                    time.sleep(7)
                    os.system('docker exec -t node' + str(nodesNew) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(random.randint(2, int(nodes)+1)) + ':18444" "onetry"')
                    address = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' node" + str(nodesNew)).read()
                    os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')

                potionOutput = ""
                try:
                    info = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodes-1):
                        for b in range(0,nodes-1):
                            potionOutput = potionOutput + data[a]["node"] + " " + data[a]["peers"][b]["addr"] + "\n"
                except:
                    break

                correct = 0

                for x in range(1,nodes+1):
                    try:
                        info = os.popen("docker exec -t node" + str(x) + " /btcbin/bitcoin-cli -regtest getpeerinfo").read()
                        data = json.loads(info)
                        a = 0
                        while True:
                            try:
                                if ("172.17.0." + str(x+1) + ":18444 " + data[a]["addr"] in potionOutput): correct += 1
                                print "172.17.0." + str(x+1) + ":18444 " + data[a]["addr"]
                                a+=1
                            except:
                                break
                    except:
                        pass
                f.write("[" + str(i) + "]" + str(correct) + " " + str(potionOutput.count('\n')) + "\n")
                time.sleep(60)
            f.close()


def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print " Done!\n"

main()