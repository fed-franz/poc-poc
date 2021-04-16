

runTest(){
    nodes=$1
    malicious=$2
    freq=$3
    minutes=$4

    #Create network
    numMalicious=$(( nodes*malicious/100 ))
    numNodes=$(( nodes-malicious ))
    python main.py -s $numNodes $numMalicious \
    #Change network
    &&  python main.py -r $freq $malicious &
    sleep 30
    #Test AToM
    python main.py -t $minutes 60 "tst-mal$malicious-var$freq.out"

    #Terminate
    pkill python
    python main.py -d
    rm lock*

    echo "DONE"

    cat results/tst-mal$malicious-var$freq.out
}

#       nodes %mal  var   minutes
runTest  50    0     1      10
runTest  50    0     5      10
runTest  50    0     10     10

runTest  50    10    1      10
runTest  50    10    5      10
runTest  50    10    10     10

runTest  50    20    1      10
runTest  50    20    5      10
runTest  50    20    10     10

runTest  50    30    1      10
runTest  50    30    5      10
runTest  50    30    10     10

runTest  50    40    1      10
runTest  50    40    5      10
runTest  50    40    10     10

runTest  50    50    1      10
runTest  50    50    5      10
runTest  50    50    10     10