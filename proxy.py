# -*- coding: utf-8 -*-
"""
Created on Sat May 07 16:05:17 2016

@author: CHEN Shuang
"""
import re
import time
from socket import *
import thread
#class define 
def recv_timeout(from_socket, to_socket,timeout=2):
    from_socket.setblocking(0)
    #total_data=[];
    data='';
    begin=time.time()
    recvGzero = False
    while 1:
    #if you got some data, then break after wait sec
        if recvGzero and time.time()-begin>timeout:
            break
    #if you got no data at all, wait a little longer
        elif time.time()-begin>timeout*2:
            break
        try:
            data=from_socket.recv(8192)
            if data:
                recvGzero = True
                to_socket.sendall(data)
                #total_data.append(data)
                begin=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return True
class httpHeader(object):
    def __init__(self, method=None, url=None, cookie=None, host=None):
        self.method = method
        self.url = url 
        self.cookie = cookie
        self.host = host
    def __str__(self):
        return "httpheader extraction\nmethod: %s\nurl: %s\ncookie: %s\nhost: %s\n" % (self.method, self.url, self.cookie, self.host)
#parse httpheader fill the method/ url/ cookie/ host
def parseHttpHeader(request, header): 
    result = re.search(r'Host: (.*)\s{2}', request)
    if(result):
        header.host = result.group(1)
    else:
        print "Host in request is null"
    result = re.search(r'(.*)\s{2}', request)
    if(result):
        line = result.group().split()
        header.method = line[0]
        header.url = line[1]
    else:
        print "request content is null"
    result = re.search(r'Cookie: (.*)\s{2}', request)
    if(result):
        header.cookie = result.group(1)
    else:
        print "Cookie in request is null"    
def startNewConnection(threadname, conn):
    print '----%s----\n' % threadname
    lockN = thread.allocate_lock()
    lockN.acquire()
    global threadn
    threadn = threadn + 1
    lockN.release()
#    lock = thread.allocate_lock()
#    lock.acquire()
#    global serverSocket
#    connectionSocket, addr = serverSocket.accept()
#    lock.release()
    httpRequest = conn.recv(recvSize)
    localHeader = httpHeader()
    #proxy processing
    parseHttpHeader(httpRequest, localHeader)
    try:
        #print repr(Header.host)
        proxyClientSocket = socket(AF_INET, SOCK_STREAM)
        (soc_family, _, _, _, address) = getaddrinfo(localHeader.host, httpPort)[0]     
        proxyClientSocket.connect(address)        
        print "Proxy server connect host: %s succeed" % localHeader.host
        proxyClientSocket.sendall(httpRequest)
        recv_timeout(proxyClientSocket, conn, 0.5)
        print "Send to Host %s succeed" % localHeader.host
        proxyClientSocket.close()
        conn.close()
        responsesFile.close()
    except:
        print "Connect %s failed" % localHeader.host
        proxyClientSocket.close()
        conn.close()
    lockN.acquire()
    threadn = threadn - 1
    lockN.release()
    print 'exiting thread %s\n' % threadname

#parameter definition
serverPort = 8080
httpPort = 80
recvSize = 8960
maxThreads = 10
threadn = 0
#http header
Header = httpHeader()
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(20)
print "the proxy server is listening"
while True:
    if (threadn < maxThreads):
        connectionSocket, addr = serverSocket.accept()
        thread.start_new_thread(startNewConnection, ('thread '+str(threadn),connectionSocket))
    else:
        time.sleep(2)