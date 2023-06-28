import socket
import threading
import numpy as np
import time
'''
Client
1.  socket //소켓생성
3.5 connect //연결요청  (3. 연결대기listen   --- 5. 연결승인accept)
5.  send/recv //통신
6.  close  //소켓닫기
'''

class Client:

    # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) # (socket, level, optname, optval, optlen)
    
#%%
    def __init__(self):
        
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        self.host = "168.188.117.139"
        self.port2 = 9999
        
        # client
        client_config = (self.host, self.port2)
        self.client.connect(client_config)
        print('-----client is connected-----\n\n\n')


        self.size = 48000
        self.i = 0
        self.ux = []

#%%
    def receive(self):
        
        try:
            while True:
                angledata = self.client.recv(self.size)
                angledata = angledata.decode()
                self.ux = angledata
                
                print('1. recv3 :',self.ux)
    
        except Exception as ex:
            print(ex)

#%%
    def mainSystem(self):
       
        self.th = threading.Thread(target=self.receive)
        self.th.daemon = True
        self.th.start()
        
        while True:
            
            print('2. self.ux의 값들을 하나씩 출력합니다:',self.ux)
            self.i += 1
#%%
if __name__ == '__main__':
    S = Client()
    S.mainSystem()
    S.th.join()
