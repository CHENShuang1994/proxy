# -*- coding: utf-8 -*-
"""
Created on Sat May 07 16:05:17 2016

@author: CHEN Shuang
"""
import re
import time
from socket import *
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
        print repr(header.host)
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
responsesFile = open("response.txt", 'w')    
#parameter definition
serverPort = 8080
httpPort = 80
recvSize = 8960
timeout = 10
#http header
Header = httpHeader()
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(50)
print "the proxy server is listening"
while True:
    #recv from client
    connectionSocket, addr = serverSocket.accept()
    httpRequest = connectionSocket.recv(recvSize)
    #proxy processing
    parseHttpHeader(httpRequest, Header)
    httpResponse = ''
    try:
        #print repr(Header.host)
        #print getaddrinfo(Header.host, httpPort)[0][4]
        proxyClientSocket = socket(AF_INET, SOCK_STREAM)
        (soc_family, _, _, _, address) = getaddrinfo(Header.host, httpPort)[0]     
        print address
        proxyClientSocket.connect(address)        
        #proxyClientSocket.connect((Header.host, httpPort))
        print "Proxy server connect host: %s succeed" % Header.host
        
        #print httpRequest
        #print httpRequest
        proxyClientSocket.sendall(httpRequest)
        recv_timeout(proxyClientSocket, connectionSocket)
        proxyClientSocket.close()
        connectionSocket.close()
#        ret = proxyClientSocket.recv(recvSize)
#        print "Http response", ret
#        connectionSocket.send(ret)
#        proxyClientSocket.close()
#        connectionSocket.close()
#        begin = time.time()
#        while (True):
#            print "beginrecv"
#            ret = proxyClientSocket.recv() 
#            print "endrecv"            
#            if (ret):
#                print '----'
#                print ret
#                print '---'
#                connectionSocket.send(ret)
#            else:
#                print "---------------------------\nhttpResponse send to %s succeed" % Header.host
#                proxyClientSocket.close()
#                connectionSocket.close()   
#                break
        responsesFile.close()
        #print httpResponse
        #print Header    
        #send back to client
#        print httpResponse
#        connectionSocket.sendall(httpResponse
    except:
        #assert  (Header.host!='today.hit.edu.cn')
        print "Connect %s failed" % Header.host
        proxyClientSocket.close()
        connectionSocket.close()
        continue
responsesFile.close()