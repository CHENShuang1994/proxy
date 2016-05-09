# -*- coding: utf-8 -*-
"""
Created on Sat May 07 16:05:17 2016

@author: CHEN Shuang
"""
import re
import time
from socket import *
import thread
import hashlib
#class define 
class httpHeader(object):
    def __init__(self, method=None, url=None, cookie=None, host=None):
        self.method = method
        self.url = url 
        self.cookie = cookie
        self.host = host
    def __str__(self):
        return "httpheader extraction\nmethod: %s\nurl: %s\ncookie: %s\nhost: %s\n" % (self.method, self.url, self.cookie, self.host)
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
def cacheFromResponse(from_socket, timeout=0.5):
    from_socket.setblocking(0)
    total_data=[];
    data='';
    begin=time.time()
    while 1:
        #print total_data
    #if you got some data, then break after wait sec
        if total_data and time.time()-begin>timeout:
            break
    #if you got no data at all, wait a little longer
        elif time.time()-begin>timeout*2:
            break
        try:
            data=from_socket.recv(8192)
            if data:
                total_data.append(data)
                #total_data.append(data)
                begin=time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return ''.join(total_data)
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
#multiple thread start point 
def startNewConnection(threadname, conn):
    print '----%s----\n' % threadname
    lockN = thread.allocate_lock()
    lockN.acquire()
    global threadn, cache 
    threadn = threadn + 1
    lockN.release()
    httpRequest = conn.recv(recvSize)
    localHeader = httpHeader()
    #proxy processing
    parseHttpHeader(httpRequest, localHeader)
    #-------------------------------------------------
    if (localHeader.url in cache):
        #extract the since-modified-date and forward to destination server and check reponse state
        print "hit in cache"
        filename = cache[localHeader.url][1]
        date = cache[localHeader.url][0]
#        fp = open(filename, 'r')
#        content = ''.join(fp.readlines())
#        close(fp)
#        ret = re.search(r'If-Modified-Since: (.*)\s{2}', content)
#        if (ret):
#            date = ret.group(1)
#        else:
#            print "http Header has no \"If-Modified-Since\" filed\n"
        modifiedRequest = re.sub(r'If-Modified-Since: (.*)\s{2}', 'If-Modified-Since: '+date+'\r\n', httpRequest)
        print 'date is %s' % date
        print 'modifiedRequest is %s\n' % modifiedRequest
        try:
            #print repr(Header.host)
            proxyClientSocket = socket(AF_INET, SOCK_STREAM)
            (soc_family, _, _, _, address) = getaddrinfo(localHeader.host, httpPort)[0]     
            proxyClientSocket.connect(address)     
            #forward directly
            print "Proxy server connect host: %s succeed" % localHeader.host
            proxyClientSocket.sendall(modifiedRequest)
            response = cacheFromResponse(proxyClientSocket)
            matchResult = re.search(r'.* (.*) ', response)
            #extract the status code             
            statusCode = matchResult.group(1)
            print "status code is %s" % statusCode
            if (statusCode == "304"):
                #not modified search in Cache, directly forward it 
                #set file lock
                Flock = thread.allocate_lock()
                Flock.acquire()                
                fp = open(filename, 'r')
                content = ''.join(fp.readlines())
                fp.close()
                Flock.release()
                conn.sendall(content)
            else:
                #update cache and forward the response to client 
                conn.sendall(response)
                reDate = re.search(r'Last-Modified: (.*)\s{2}', response)  
                if (reDate):
                    modifiedDate = reDate.group(1)
                    #update file
                    Flock = thread.allocate_lock()
                    Flock.acquire()
                    fp = open(filename, 'w')
                    fp.write(response)
                    fp.close()
                    Flock.release()
                    #update the date:
                    cache[localHeader.url] = (modifiedDate, filename)
                else:
                    print "response content has no \"Last-Modified\" field\n"
           # recv_timeout(proxyClientSocket, conn, 0.5)
            print "Send to Host %s succeed" % localHeader.host
            proxyClientSocket.close()
            conn.close()
        except:
            print "Connect %s failed" % localHeader.host
            proxyClientSocket.close()
            conn.close()
    else:
        print "not hit"
        #forward directly and save to cache 
        try:
            #print repr(Header.host)
            proxyClientSocket = socket(AF_INET, SOCK_STREAM)
            (soc_family, _, _, _, address) = getaddrinfo(localHeader.host, httpPort)[0]     
            proxyClientSocket.connect(address)     
            #forward directly
            print "Proxy server connect host: %s succeed" % localHeader.host
            proxyClientSocket.sendall(httpRequest)
            #recv_timeout(proxyClientSocket, conn, 0.5)
            #print "Before cacheFromResponse"
            content = cacheFromResponse(proxyClientSocket) #can be optimized  
            #print '---response-----\n%s\n-------------\n' % repr(content)
            #print "after cacheFromResponse"
            conn.sendall(content)
            reobj = re.search(r'Last-Modified: (.*)\s{2}', content)
            if (reobj):
                modifiedDate = reobj.group(1)
                print 'modifiedDate is %s \n' % modifiedDate
                Flock = thread.allocate_lock()
                Flock.acquire()
                #print "before write to file %s.txt" % localHeader.url 
                filename = hashlib.md5(localHeader.url).hexdigest()+'.txt'
                fp = open(filename, 'w')
                fp.write(content)
                fp.close()
                Flock.release()
                #print "after write to file %s.txt" % localHeader.url         
                cache[localHeader.url] = (modifiedDate, filename)
            else:
                print "resoonse content has no \"Last-Modified\" field\n"
            print "Send to Host %s succeed" % localHeader.host
            proxyClientSocket.close()
            conn.close()
        except Exception, e: 
            print str(e)
            print "Connect %s failed" % localHeader.host
            proxyClientSocket.close()
            conn.close()
        except:
            print "Connect %s failed" % localHeader.host
            proxyClientSocket.close()
            conn.close()
        
    #------------------------------------------------
#    try:
#        #print repr(Header.host)
#        proxyClientSocket = socket(AF_INET, SOCK_STREAM)
#        (soc_family, _, _, _, address) = getaddrinfo(localHeader.host, httpPort)[0]     
#        proxyClientSocket.connect(address)     
#        #forward directly
#        print "Proxy server connect host: %s succeed" % localHeader.host
#        proxyClientSocket.sendall(httpRequest)
#        recv_timeout(proxyClientSocket, conn, 0.5)
#        print "Send to Host %s succeed" % localHeader.host
#        proxyClientSocket.close()
#        conn.close()
#    except:
#        print "Connect %s failed" % localHeader.host
#        proxyClientSocket.close()
#        conn.close()
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
cache = dict()
#format: {url: (date, filename)}
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