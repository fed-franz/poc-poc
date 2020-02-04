# -*- coding: utf-8 -*-

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
        print "Where [OPTION] means:"
        print "-s : Create a bitcoin blockchain of [arg] trusty nodes plus [arg2] malicious nodes."
        print "-d : Delete bitcoin blockchain."
        print "-t : Run a [arg] tests and get results waiting [arg2] seconds between tests."
        print ""

    else:
        if (sys.argv[1] == '-s'):
            nodes = sys.argv[2]
            malicious = sys.argv[3]
            totalNodes = int(nodes) + int(malicious)
            os.system("mkdir database")
            f = open('database/bitcoin', 'w')
            f.write(str(totalNodes))
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
            nodes = f.read()
            command = "nohup python -c 'import potion; potion.deleteBlockchain(" + nodes + ", \"s\")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            f.close()

            print "\nDestroying blockchain...\n"
    
            items = list(range(1, int(nodes)))
            l = len(items)
            for i, item in enumerate(items):
                while True:
                    if not (os.popen("docker ps | grep -oP node" + str(i+1)).read()):
                        printProgressBar(i + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                        break

            while True:
                if not (os.popen("docker ps | grep -oP nodeMonitor").read()):
                    printProgressBar(l + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                    break

        if (sys.argv[1] == '-t'):
            t = open('database/bitcoin', 'r')
            nodes = int(t.read())
            t.close()
            nodesNew = nodes
            addressMonitor = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nodeMonitor").read()
            f = open("database/results", "w")
            p = open("database/potionout", "w")
            c = open("database/nodes", "w")
            f.write("[<Test>] <correct_connections> | <missing_connections> | <poc_verified_connections> :\n")

            for i in range(0,int(sys.argv[2])):
                print "\x1b[6;30;42m[log]\x1b[0m : Performing test " + str(i) + "... ",
                what = random.randint(0,1)
                if (what):
                    change = str(random.randint(1, nodes))
                    address = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' node" + str(change)).read()
                    print "Killing node" + str(change) + " with IP " + address,
                    try:
                        os.system("docker kill node" + str(change))
                        os.system("docker rm node" + str(change))
                    except:
                        pass
                else:
                    nodesNew += 1
                    os.system("docker run -it -d --name node" + str(nodesNew) + " ubuntu /bin/bash")
                    os.system("docker cp ../btcbin node" + str(nodesNew) + ":/")
                    os.system("docker exec -t node" + str(nodesNew) + " /btcbin/bitcoind -regtest -debug=net -daemon")
                    time.sleep(5)
                    os.system('docker exec -t node' + str(nodesNew) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(random.randint(2, int(nodes)+1)) + ':18444" "onetry"')
                    address = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' node" + str(nodesNew)).read()
                    os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                    t = open('database/bitcoin', 'w')
                    t.write(str(nodesNew))
                    t.close()
                    print "Creating node" + str(nodesNew) + " with IP " + address,

                potionOutput = ""
                time.sleep(int(sys.argv[3]))

                try:
                    info = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodesNew-1):
                        for b in range(0,nodesNew-1):
                            try:
                                if (data[a]["peers"][b]["verified"]):
                                    potionOutput = potionOutput + data[a]["peers"][b]["bind"] + " " + data[a]["peers"][b]["addr"] + "\n"
                            except:
                                pass
                except:
                    pass

                correct = 0
                missing = 0

                for x in range(1,nodesNew+1):
                    try:
                        info = os.popen("docker exec -t node" + str(x) + " /btcbin/bitcoin-cli -regtest getpeerinfo").read()
                        data = json.loads(info)
                        a = 0
                        while True:
                            try:
                                if (addressMonitor[:len(addressMonitor)-1] not in data[a]["addr"]):
                                    c.write(data[a]["addrbind"] + " " + data[a]["addr"] + "\n")
                                    if (data[a]["addrbind"] + " " + data[a]["addr"] in potionOutput): correct += 1
                                    else: 
                                        missing += 1
                                        print "\x1b[6;30;42m[log]\x1b[0m : New missing connection --->" + data[a]["addrbind"] + " " + data[a]["addr"]
                                a+=1
                            except:
                                break
                    except:
                        pass
                res = "[" + str(i) + "] " + str(correct) + " | " + str(missing) + " | " + str(potionOutput.count('\n'))
                f.write(res + "\n")
                print "\x1b[6;30;42m[log]\x1b[0m : Test result ---> " + res
                p.write(potionOutput + "\n\n")
                c.write("\n")
            f.close()
            p.close()


def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print " Done!\n"

main()