#!/bin/bash

#Environment
numnodes=$1
numconns=$2
m=$((numnodes + 10))
testdir=poctest
btcd=btcbin/bitcoind
btccli=btcbin/bitcoin-cli
net=-regtest
baseport=1900

omal=-malicious
runmalicious=false
malnum=2

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
 else
   echo "Running N$n"
 fi

 mkdir $datadir 
 run $btcd $net -datadir=$datadir -port=$(port n) -rpcport=$(rport n) -debug=net -logips $@ -daemon
 sleep 3
}

function runmalnode(){
  echo "Running malicious node"
  tmp=$btcd
  btcd=$btcd-malicious
  runnode $@
  btcd=$tmp
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

##### START TEST #####

#Check connections are not above the limit (n(n-1))/2
maxconn=$(( numnodes*(numnodes-1) / 2 ))
if [ $numconns -gt $maxconn ]; then
 echo "ERR: Max connections = $maxconn"
 exit 1
fi

#Reset Test dir
rm -rf $testdir
mkdir $testdir

#Create Nodes
for i in $(seq 1 $numnodes)
do
  if [ $i = $malnum ] && [ $runmalicious = true ]; then
    runmalnode $i
  else
    runnode $i
  fi
done

# TODO: if numnodes > 4 check at least one outbound per each node
#Create connections
for i in $(seq 1 $numconns)
do
  status=1

  #If addconn fails, try a different connection
  while [ $status -ne 0 ]
  do
    n1=$(($RANDOM % $numnodes + 1))
    n2=$(($RANDOM % $numnodes + 1))

    #Make sure n1 != n2
    while [[ ( "$n1" = "$n2" ) || ( "$runmalicious" = "true" && "$n1" = "$malnum" && "$n2" = "1" ) ]]
    do
      n2=$(($RANDOM % $numnodes + 1))
    done

    addconn $n1 $n2
    status=$?
  done
done


#Run Monitor
runnode $m -pocmon
for i in $(seq 1 $numnodes)
do
 addconn $m $i
 sleep 1
done

#Get Nodes Info
sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo

#Remove node
removed=$(($RANDOM % $numnodes + 1))
echo "Removing node$removed"
nodecli $removed stop
sleep 2

echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
sleep 2

#Add new node
newnode=$(($numnodes + 1))
runnode $newnode

#Create connections
connadded=0

while [ $connadded -ne 1 ]
do
  for i in $(seq 1 $numnodes)
  do
    connect=$(($RANDOM % 6))

    #If addconn fails, try a different connection
    if [ $i -ne $removed ] && [ $connect -gt 1 ]; then
      connadded=1
      outbound=$(($RANDOM % 2))
      if [ "$outbound" = "1" ]; then
        addconn $newnode $i
      else
        addconn $i $newnode
      fi
    fi
  done
done

addconn $m $newnode
sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
numnodes=$(($numnodes + 1))

sleep 5

#Stop Nodes
#numnodes=$(($numnodes - 1));
for i in $(seq 1 $numnodes)
  do
    if [ $i -ne $removed ]; then
      nodecli $i stop
    fi
  done
  nodecli $m stop
  sleep 3

for i in $(seq 1 $numnodes)
do
  echo "__________ LOG Node$i __________" > log.txt
  cat poctest/btcnode$i/regtest/debug.log | grep '\[POC\]' >> log.txt
done
echo "__________ MONITOR LOG __________" >> log.txt
cat poctest/btcnode$m/regtest/debug.log | grep '\[POC\]' >> log.txt

exit 0

