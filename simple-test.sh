#!/bin/bash

#Environment
numnodes=$1
numadds=$2
m=$((numnodes + 10))
m2=$((m + 1))
testdir=poctest
btcd=btcbin/bitcoind-f1-t01
btccli=btcbin/bitcoin-cli
net=-regtest
baseport=1900

omal=-malicious
runmalicious=false
malnum=2

removed=0

declare -A CONNS 

### MACROS ###
port(){ 
 np=$1
 echo $((baseport + 10*np))
}

rport(){ 
 np=$1
 echo $((baseport + 10*np + 1))
}

ddir(){
 echo $testdir/btcnode$1
}

run(){
 echo $@
 $@
 return $?
}

### FUNCTIONS ###
function runnode() {
 n=$1
 shift
 datadir=$(ddir $n)

 if [ $n = $m ]; then
   echo "Running M"
 elif [ $n = $m2 ]; then
   echo "Running M2"
 else
   echo "Running N$n"
 fi

 mkdir $datadir 
 run $btcd $net -datadir=$datadir -port=$(port n) -rpcport=$(rport n) -debug=net -logips $@ -daemon
 sleep 4
}

function nodecli() {
 nc=$1
 shift

 run $btccli $net -rpcport=$(rport $nc) -datadir=$(ddir $nc) $@
}

function addconn() {
 n1=$1
 n2=$2

  ##TODO: Check n1 != n2 
 if [ ${CONNS[$n1$n2]} ] || [ ${CONNS[$n2$n1]} ]; then
  #echo "ERR: Nodes are already connected"
  return -1
 fi

 if [ $n1 = $m ]; then
   echo "Connecting M to N$n2"
 elif [ $n1 = $m2 ]; then
   echo "Connecting M2 to N$n2"
 else
   echo "Connecting N$n1 to N$n2"
 fi
 run $btccli $net -rpcport=$(rport $n1) -datadir=$(ddir $n1) addnode 127.0.0.1:$(port $n2) onetry

 if [ $? = 0 ]; then
  CONNS[$n1$n2]=true
 fi

 sleep 1

 return $?
}

function addconns() {
 node=$1

 connadded=0
 while [ $connadded -ne 1 ]
 do
   for i in $(seq 1 $numnodes)
   do
     connect=$(($RANDOM % 6))

     if [ $i -ne $node ] && [ "$i" -ne "$removed" ] && [ $connect -gt 1 ]; then
       connadded=1
       outbound=$(($RANDOM % 2))
       if [ "$outbound" = "1" ]; then
         addconn $node $i
       else
         addconn $i $node
       fi
     fi
   done
 done
}

function addnode() {
  newnode=$(($numnodes + 1))
  runnode $newnode

  #Connect monitors to new node
  addconn $m $newnode
  addconn $m2 $newnode

  #Create connections to new node
  addconns $newnode
  numnodes=$(($numnodes + 1))

  sleep 1
}

function getnodesinfo() {
  monitor=$1

  echo "GETNETNODESINFO"
  nodecli $m getnetnodesinfo | grep "node\|addr\|inbound"

}

##### START TEST #####

#Reset Test dir
rm -rf $testdir
mkdir $testdir

#Create Nodes
for i in $(seq 1 $numnodes)
do
  if [ $i = $malnum ] && [ $runmalicious = true ]; then
    runnode $i $omal
  else
    runnode $i
  fi
done

#Run Monitors and connect to all nodes
runnode $m -pocmon
runnode $m2 -pocmon
for i in $(seq 1 $numnodes)
do
 addconn $m $i
 addconn $m2 $i
done

#Create connections
for i in $(seq 1 $numnodes)
do
 addconns $i
done

sleep 2

### Init Monitorint ###
#touch poctest/m1.out
m2out=poctest/m2.out
touch $m2out

#Get Nodes Info
getnodesinfo $m
getnodesinfo $m2 > $m2out

for i in $(seq 1 $numadds)
do
  #Add new nodes
  addnode
  #Get Nodes Info
  getnodesinfo $m
  getnodesinfo $m2 > $m2out
done
sleep 2

#Remove node
removed=$(($RANDOM % $numnodes + 1))
echo "REMOVING NODE N$removed"
nodecli $removed stop
sleep 1
#Get Nodes Info
getnodesinfo $m
getnodesinfo $m2 > $m2out

sleep 5
#Get Nodes Info
echo "FINAL GETNODESINFO"
getnodesinfo $m
getnodesinfo $m2 > $m2out
sleep 2

#Stop Nodes
echo "STOPPING NODES"
for i in $(seq 1 $numnodes)
  do
    if [ $i -ne $removed ]; then
      nodecli $i stop
    fi
  done
  nodecli $m stop
  nodecli $m2 stop
  sleep 3

#Merging logs
for i in $(seq 1 $numnodes)
do
  echo "__________ LOG Node$i __________" > log.txt
  cat poctest/btcnode$i/regtest/debug.log | grep '\[POC\]' >> log.txt
done
echo "__________ MONITOR LOG __________" >> log.txt
cat poctest/btcnode$m/regtest/debug.log | grep '\[POC\]' >> log.txt

exit 0

