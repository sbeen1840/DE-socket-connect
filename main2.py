import socket
import threading
import numpy as np
import time
import os
import sys
from scipy import signal
import RealTime_DataMaker as RDM
import joblib
import torch


'''
Client
1.  socket //소켓생성
3.5 connect //연결요청  (3. 연결대기listen   --- 5. 연결승인accept)
5.  send/recv //통신
6.  close  //소켓닫기
'''
#%% 필요한 값 불러오기





class Client:

    # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) # (socket, level, optname, optval, optlen)
    
#%%
    def __init__(self):
        
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        self.host = "168.188.117.139"
        self.port = 54321
        self.port2 = 9999
        
        # client
        client_config = (self.host, self.port)
        self.client.connect(client_config)
        print('-----client is connected-----')
        
        # server
        server_config = (self.host, self.port2)
        self.server.bind(server_config)
        self.server.listen()
        self.clientsocket, self.addr = self.server.accept()
        print('-----Server accepted-----\n\n\n')

        
        self.flag = False
        self.size = 48000
        self.code = 'ok'

#%%
        self.x_scaler = joblib.load('C:/Users/Jinsungho/Desktop/python practice/Fixed_and_Random_Data_ver2/X_scaler.pkl') 
        self.baseline = [0.0244,-0.0493,0.0269,0.0376,-0.006,-0.0099]
        self._slicing_size = 1000
        self.model = torch.load('C:/Users/Jinsungho/Desktop/python practice/Deep_Learning_models/model_0922_Y1000_116_LSTM_seqlength_nonchange_kernal606030.pth')
        self.model.eval()
        self._dummy = torch.zeros((1,30,self._slicing_size)).cuda()
        self.model(self._dummy)
        

#%%
    def MainSystem(self):
        try:
            
            while True:
                start = time.time()

                emgdata = self.client.recv(self.size)
                print('\n1. Emgdata get')
                # emgdata = emgdata.decode("UTF-8")
                # self.ux.append(eval(angledata))
                emgdata = np.frombuffer(emgdata,dtype=np.float64)
                emgdata = np.reshape(emgdata,(1000,6))
                print(emgdata)
                self.emg = emgdata.copy()
                for _i in range(6):
                    self.emg[:,_i] = self.emg[:,_i]-self.baseline[_i]
                print('1')
                sos1 = signal.butter(4, [20, 450] , 'bandpass', fs=1000, output='sos')#band pass filter
                sos2 = signal.butter(4, [59.9, 60.2] , 'bandstop', fs=1000, output='sos')#60Hz notch filter
                print('2')
                self.emg = signal.sosfilt(sos1,self.emg.T)
                self.emg = signal.sosfilt(sos2,self.emg).T
                print('3')
                b = RDM.Feature_Extraction_Realtime(self.emg)
                featured_data = b.Datamaking()
                print('4')       
                result = self.x_scaler.transform(featured_data)
                print('5')
                result = torch.from_numpy(result.T).float()
                result = torch.unsqueeze(result,0).cuda()
                print('6')
                with torch.no_grad():
                    pred = self.model(result)
                pred = pred.squeeze()
                pred = pred[-1,:]
                
                print('7')        
                
                print("time :", time.time() - start)
                print(type(pred))
                print(pred)
                
                print('8')            
                pred = pred.cpu()
                pred = pred.detach().numpy() #이 과정에서 데이터 Unity로 송신
                print('9')
                
                msg = str(pred.tolist()) 
                self.clientsocket.sendall(msg.encode()) # unity 배열보내기
                print('3. unity sending is end')
                self.client.send(self.code.encode()) # daq ok사인보내기
                print('4. sending ok\n')
        
        except Exception as ex:
            print(ex)

#%%
if __name__ == '__main__':

    try:
        S = Client()
        S.MainSystem()
        
        S.clientsocket.close()
        print('closed')
    except Exception as ex:
        print(ex)
