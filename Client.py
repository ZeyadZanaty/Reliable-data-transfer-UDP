import socket
import threading
from Packet import Packet
from Packet import calc_checksum
import sys
import time

class Client:

    def __init__(self,file_name):
        input_file = open(file_name,'r')
        self.server_ip = input_file.readline().split('\n')[0]
        self.server_port = int(input_file.readline())
        self.client_port = int(input_file.readline())
        self.requested_filename = input_file.readline().split('\n')[0]
        self.window_size = int(input_file.readline())
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.connect((self.server_ip, self.server_port))
        self.socket.settimeout(10)
        self.recv_pkt_list = []
        input_file.close()

    def request_file(self,requested_file):
        self.recv_pkt_list=[]
        self.requested_filename=requested_file
        request_packet = Packet(seqno=0, data=requested_file,type='str')
        pkd_packet = request_packet.pack(type='str')
        print(pkd_packet)
        self.socket.send(pkd_packet)
        print('File: '+str(requested_file)+' has been requested from the server.')
        self.socket.connect((self.server_ip,self.server_port+self.socket.getsockname()[1]-1000))

    def recv_and_send_ack(self):
        print('Connected to socket #'+str(self.socket.getsockname()[1]))
        exp_pkt_num = 0
        while True:
            try:
                pkt, adr = self.socket.recvfrom(600)
                recv_pkt = Packet(pkd_data=pkt)
                if adr[0] == self.server_ip:
                    print('Received packet# '+str(recv_pkt.seqno))
                    cs= calc_checksum(recv_pkt.data,type='bytes')
                    ack = Packet(type='ack',seqno=recv_pkt.seqno,chk_sum=cs)
                    pkd_ack = ack.pack(type='ack')
                    if recv_pkt.seqno == exp_pkt_num:
                        self.recv_pkt_list.append(recv_pkt)
                        self.socket.send(pkd_ack)
                        exp_pkt_num+=1
                    else:
                        continue
                print(len(self.recv_pkt_list))
            except socket.timeout:
                print('Timed Out')
                break

    def write_file(self,pkt_list):
        file = open('dl_'+str(self.requested_filename),'wb')
        for pkt in pkt_list:
            file.write(pkt.data)
        print('File Received!')


client = Client(sys.argv[2])
client.request_file(sys.argv[1])
client.recv_and_send_ack()
client.write_file(client.recv_pkt_list)