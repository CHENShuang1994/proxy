# -*- coding: utf-8 -*-
"""
Created on Sat May 07 16:05:17 2016

@author: CHEN Shuang
"""
import re
from socket import *
#class define 
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
        
#parameter definition
serverPort = 8080
httpPort = 80
recvSize = 65507
#http header
Header = httpHeader()
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(100)
print "the proxy server is listening"
while True:
    #recv from client
    connectionSocket, addr = serverSocket.accept()
    httpRequest = connectionSocket.recv(recvSize)
    #proxy processing
    parseHttpHeader(httpRequest, Header)
    print httpRequest
    try:
        #print repr(Header.host)
        proxyClientSocket = socket(AF_INET, SOCK_STREAM)
        #print getaddrinfo(Header.host, httpPort)[0][4]
        proxyClientSocket.connect(getaddrinfo(Header.host, httpPort)[0][4])
        #proxyClientSocket.connect((Header.host, httpPort))
        print "Proxy server connect host: %s succeed" % Header.host
        proxyClientSocket.send(httpRequest)
        httpResponse = proxyClientSocket.recv(recvSize)
        print httpRequest
        #print Header    
        #send back to client
        connectionSocket.send(httpResponse)
    except:
        print "Connect %s failed" % Header.host
        proxyClientSocket.close()
        connectionSocket.close()
        continue
    else:
        proxyClientSocket.close()
        connectionSocket.close()        
#    