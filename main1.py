
'''
server
1. socket//생성
2. bind //ip, port 할당
3. listen //연결대기
4. accept //연결승인
5. send/recv // 통신
6. close //socket닫기
'''

'''
>>
self.host
self.port
self.size와 통신데이터 형식(우리가 보내는 데이터가 배열이면 어떻게보내, 인코디코대신 할 것?)
send vs sendall
listen()값
socket버퍼 동작원리(쓰레기값?, 안보내면 비어있나? recv하면 사라지나?)
'''
#%% DAQ library
import os
from threading import Thread  
import sys 
import serial 
import struct 
#%% Socket library
import socket
import threading
import numpy as np
import time



class Server:
#%%
    def __init__(self):
#%% DAQ 변수
        self.ch = 6 
        self.Slice = 1000

        self.port = 'COM7' 
        self.baud = 2000000 
        self.start = 0x0b 
        self.end = 0x0c 
        self.i = 0 
        self.ser = serial.Serial(self.port, self.baud) 
        self.ser.set_buffer_size(rx_size = 16384, tx_size = 16384) 
        self.ser.flush() 
         
        self.indexStep = 5000 
        self.indexLimit = self.indexStep 
       
        self.samplingTime = 5000000
        
        self.emgData = np.zeros((self.indexStep, self.ch), dtype=float) 
        self.targetPacketBytes = self.ch*2*50 
       
#%% Socket 변수
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "168.188.117.139"
        self.port = 54321
        self.flag = False
        self.size = 48000
        self.code = 'ok'
        # self.emgData = np.ones((1000,6))
        
        server_config = (self.host, self.port)
        self.server.bind(server_config)
        
        self.server.listen(5)
        print('-----Server is ready-----')
        self.clientsocket, self.addr = self.server.accept()
        print('-----Client is connected-----\n\n\n')
        # self.clientsocket가지고 recv, send

#%% DAQ 데이터 측정 및 버퍼
    def backgroundThread(self): 
      
        while True:
            
            if self.i >= self.indexLimit: #버퍼 늘리는용
                
                self.indexLimit += self.indexStep 
                self.emgData = np.vstack((self.emgData, np.zeros((self.indexStep, self.ch)))) 
           
            if self.ser.in_waiting >= self.targetPacketBytes: 
                
                readData = self.ser.read(self.targetPacketBytes)
                
                for _t in range(50): 
                    for _Ch in range(self.ch): 
                        self.emgData[self.i + _t, _Ch] = (struct.unpack(">h", readData[int( _t*self.ch + _Ch )*2:int( _t*self.ch + _Ch )*2 + 2])[0])/32768*5 
                self.i = self.i + 50 
                

#%% DAQ 시작 0x0b 송신 코드
    def sendData(self,x): 
        self.ser.write(struct.pack("<h",x)) 
        # print("handshaking ok")  

#%% DAQ main 코드
    def main(self): 
        print("main start")
        self.sendData(self.start) 
        self.backgroundThread()

#%%
    def socket_Daq(self):
        
        try:
            time.sleep(10)
            
            self.emgData_box = self.emgData[0:self.i,:]
            servingData = self.emgData_box[-1000:,:]
            print(servingData)
            # print(type(servingData))

            # servingData = np.asarray(servingData)
            # msg = str(servingData.tolist()) 
            # print('msg')
            # self.clientsocket.sendall(msg.encode()) # unity 배열보내기
            # print('client')
        
            print(servingData)
            
            self.clientsocket.send(servingData.tobytes())
            print('\nFirst data send')
            
            while True:
                data = self.clientsocket.recv(self.size).decode() #1024사이즈 반환
                
                #쓰레기값을 계속 보낼수도 있나, 데이터를 안보내면 비어있나? 받으면 사라지나?
                if data == self.code: #handshake code가 1
                    self.flag = True
                    data = 'no'
                    print('1. ok is received')

                if self.flag==True:
                    print('2. flag is True')
                    self.emgData_box = self.emgData[0:self.i,:]
                    servingData = self.emgData_box[-1000:,:]
                    print(servingData)
                    self.clientsocket.send(servingData.tobytes())  #.decode() #.encode() #encoding?해야하나 #msg.encode() # sendall은 뭐여
                    print('3. Data is sended\n')
                    self.flag = False   
                   
        except Exception as ex:
            print(ex)


#%%
if __name__ == '__main__':
    S = Server()
    th1 = threading.Thread(target=S.main)
    th2 = threading.Thread(target=S.socket_Daq)
    
    th1.start()
    
    th2.start()
    
        
    th1.join()
    th2.join()

    S.clientsocket.close()
    # print('closed')
