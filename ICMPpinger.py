# Attribution: this assignment is based on ICMP Pinger Lab from Computer Networking: a Top-Down Approach by Jim Kurose and Keith Ross. 
# It was modified for use in CSC249: Networks at Smith College by R. Jordan Crouser in Fall 2022, and by Brant Cheikes for Fall 2023.

from socket import * 
import os
import sys 
import struct 
import time 
import select 
import binascii


ICMP_ECHO_REQUEST = 8

# -------------------------------------
# This method takes care of calculating
#   a checksum to make sure nothing was
#   corrupted in transit.
#  
# You do not need to modify this method
# -------------------------------------
def checksum(string): 
    #init variables
    csum = 0
    countTo = (len(string) // 2) * 2 #used to iteratre thru string 2 char at a time
    count = 0

    #loop iterates thru pairs of characters in string, converts pair to numerical val,
    # adds it to csum, and ensures that csum does not exceed 32 bits
    while count < countTo: 
        thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
        csum = csum + thisVal
        csum = csum & 0xffffffff 
        count = count + 2

    #handles strings of odd lengths by processing last char separately
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1]) 
        csum = csum & 0xffffffff

    #finalizes csum by shifting bits of csum 16 positions to the right (extracts upper 16 
    # bits of csum), extracts lower 16 bits of csum using bitwise AND operation, adds upper
    # and lower together, and adds any remaining carry
    csum = (csum >> 16) + (csum & 0xffff) 
    csum = csum + (csum >> 16)

    #calculates complement of csum
    answer = ~csum

    #masks to 16 bits
    answer = answer & 0xffff
 
    #swaps byte order
    answer = answer >> 8 | (answer << 8 & 0xff00) 
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr): 
    
    timeLeft = timeout
    
    while True:
        startedSelect = time.time()

        #wait for the socket to become ready for reading
        #timeLeft = max time function will wait for socket to be ready
        #howLongInSelect counts how long function is waiting
        whatReady = select.select([mySocket], [], [], timeLeft) 
        howLongInSelect = (time.time() - startedSelect)

        #checks to see if the list of sockets ready for reading is empty (AKA it timed out)
        if whatReady[0] == []: # Timeout 
            return "Request timed out."

        #records time when ICMP echo reply packet is received, stores info from packet
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #---------------#
        # Fill in start #
        #---------------#

            # TODO: Fetch the ICMP header from the IP packet
            # Soluton can be implemented in 6 lines of Python code.

        ####### NOTES #######

        # recPacket is in bytes
        # in IPv4 header, the last 4 bits in the first byte is called IHL (internet header length)
        # to calculate the length of IP header, multiply IHL by 4

        #pulls out the IHL value and assigns it to header_length
        ip_header_length = (recPacket[0] & 0xF) * 4

        print("IP header len = ", ip_header_length)

        #icmp header is 8 bytes, so starting where the IP header ends (header_length) and extending 
        # 8 more bytes to include the standard size for an ICMP header
        icmp_header = recPacket[ip_header_length:ip_header_length + 8]

        #unpacking using the same format that was used to pack in sendOnePing
        icmp_header_val = struct.unpack("bbHHh", icmp_header)

        print(type(icmp_header_val))
        print(icmp_header_val)

        #icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = icmp_header_values


            #look at length of recPacket
            #know where ICMP header sits in comparison to start of IP packet
            #request vs. reply ICMP echo
            #use wireshark
            #recPacket is IP packet, header + data
            #the response will include the time that you sent originally, subtract to find roudtrip time

        #-------------#
        # Fill in end #
        #-------------#

        #updates remaining time
        timeLeft = timeLeft - howLongInSelect 
        
        #checks if remaining time is less than or equal to 0, ensures loop continues for specified time
        if timeLeft <= 0:
            return "Request timed out."

#constructs and sends an ICMP echo request packet
def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy header with a 0 checksum
 
    # struct -- Interpret strings as packed binary data
    #creates ICMP header for echo request packet
    #use4s struct.pack to pack values into a binary string
    # "bbHHh" = 1 byte, 1 byte, 2 shorts, 1 short
    #data line creates the data portion of the packet which includes time stamp in 
    # a packed double format "d"
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1) #LOOK INTO STRUCT.PACK
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header. 
    myChecksum = checksum(''.join(map(chr, header+data)))

    # Get the right checksum, and put in the header 
    #checks OS (darwin is macOS) and adjusts checksum to accordingly, nothing needs to be done on windows
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order 
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    #header is recontructed with correct checksum (no change on windows)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1) 
    packet = header + data

    #sends packet to specified destination address
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str 
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

#performs single round-trip ping operation by initializing raw socket, generating process ID,
# sends ICMP echo request, receives reply, calculates round-trip time, returns delay
def doOnePing(destAddr, timeout): 
    #retrieves ICMP protocol number
    icmp = getprotobyname("icmp")

    #creates raw socket using ICMP protocol, allows program to send/receive ICMP packets directly
    # SOCK_RAW is a powerful socket type. For more details:	http://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    #reutrns current process ID
    #bitwise AND to ensure ID is within 16 bit range
    #sends ping
    #receives ping and processes packet to calculate round-trip time ("delay")
    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
 
    #close socket and return delay time
    mySocket.close() 
    return delay

#resolves host, prints ping info, loops to send pings, prints round-trip time, returns delay of last ping
def ping(host, timeout=1, repeat=3):

    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost 

    #resolves the provided host to an IP address
    dest = gethostbyname(host)
    print(f"Pinging {host} [{dest}] {repeat} times using Python:")

    # Send ping requests to a server separated by approximately one second 
    # Do this only a fixed number of times as determined by 'repeat' argument
    numPings = 1
    while (numPings <= repeat) :
        delay = doOnePing(dest, timeout) 
        print(f"Ping {numPings} RTT {delay} sec")
        time.sleep(1) # one second 
        numPings += 1
    return delay

# Runs program
if __name__ == "__main__":
    # get target address from command line
    target = sys.argv[1]

    #takes URL, since ping function will resolve domain name
    ping(target)
