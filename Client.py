import socket
import threading
from Packet import Packet
from Packet import calc_checksum
import sys
import time,random

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
        self.recv_pkt_list = []
        input_file.close()

    def request_file(self,requested_file):
        self.recv_pkt_list=[]
        self.requested_filename=requested_file
        self.socket.settimeout(5)
        while True:
            request_packet = Packet(seqno=0, data=requested_file,type='str')
            pkd_packet = request_packet.pack(type='str')
            # print(pkd_packet)
            self.socket.send(pkd_packet)
            print('File: '+str(requested_file)+' has been requested from the server.')
            try:
                ack_pkt,address = self.socket.recvfrom(1024)
                ack_pkt = Packet(type='ack',pkd_data=ack_pkt)
                print('Request ack recevied.')
                break
            except socket.timeout:
                continue
        self.socket.settimeout(None)
        self.recv_port_num()
        self.recv_file_len()

    def get_corrupted_packets(self,packets_num, probability, seed):
        random.seed(seed)
        corrupted = random.sample(range(packets_num), int(probability * packets_num))
        corrupted = [i for i in corrupted]
        corrupted.sort()
        return corrupted

    def recv_port_num(self):
        pkt,adr = self.socket.recvfrom(600)
        unpkd = Packet(pkd_data=pkt)
        self.server_port = int(unpkd.data.decode())
        self.socket.connect((self.server_ip,self.server_port))

    def recv_file_len(self):
        pkt, adr = self.socket.recvfrom(600)
        unpkd = Packet(pkd_data=pkt)
        ack = Packet(type='ack', chk_sum=calc_checksum(unpkd.data.decode())).pack(type='ack')
        self.socket.send(ack)
        self.file_len = int(unpkd.data)
        print('Required file length = ',self.file_len,' packets.')

    def recv_and_send_ack(self):
        print('Connected to socket #'+str(self.socket.getsockname()[1]))
        corrupted = self.get_corrupted_packets(self.file_len,0,5)
        exp_pkt_num = 0
        while True:
            try:
                # self.socket.settimeout(5)
                pkt, adr = self.socket.recvfrom(600)
                recv_pkt = Packet(pkd_data=pkt)
                if recv_pkt.seqno in corrupted:
                    recv_pkt.checksum = recv_pkt.checksum-10
                    corrupted.remove(recv_pkt.seqno)
                if adr[0] == self.server_ip:
                    print('Received packet# '+str(recv_pkt.seqno))
                    cs= calc_checksum(recv_pkt.data,type='bytes')
                    ack = Packet(type='ack',seqno=recv_pkt.seqno,chk_sum=cs)
                    pkd_ack = ack.pack(type='ack')
                    if recv_pkt.seqno == exp_pkt_num and recv_pkt.checksum == calc_checksum(recv_pkt.data, type='bytes'):
                        print('Sending Ack# ' + str(recv_pkt.seqno))
                        self.recv_pkt_list.append(recv_pkt)
                        self.socket.send(pkd_ack)
                        exp_pkt_num += 1
                    else:
                        if recv_pkt.checksum != calc_checksum(recv_pkt.data, type='bytes'):
                            print('Packet # ', recv_pkt.seqno, 'is corrupted, re-receiving')
                        continue
                if self.file_len == len(self.recv_pkt_list):
                    print('File received successfully.')
                    break
            except socket.timeout:
                print('Packet# ',exp_pkt_num,' timed out, re-receiving.')
                continue

    def write_file(self,pkt_list):
        file = open('dl_'+str(self.requested_filename), 'wb')
        for pkt in pkt_list:
            file.write(pkt.data)
        print('File written successfully!')


client = Client(sys.argv[2])
client.request_file(sys.argv[1])
client.recv_and_send_ack()
client.write_file(client.recv_pkt_list)