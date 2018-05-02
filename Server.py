import socket  # Import socket module
import os
import struct
from Packet import Packet, calc_checksum
import threading, time
import random
from RDTProtocols import *

class Server:

    def __init__(self, file_name):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = socket.gethostbyname('localhost')
        file = open(file_name, 'r')
        self.port = int(file.readline())
        self.window_size = int(file.readline())
        self.random_seed = int(file.readline())
        self.probability = float(file.readline())
        self.client_num = 0
        self.client_port = self.port
        self.pkt_list = []
        file.close()

    def get_lost_packets(self, total_packets, probability, seed):
        random.seed(seed)
        list = random.sample(range(total_packets), int(probability * total_packets))
        list.sort()
        return list

    def get_bytes_from_file(self,file_name):
        return open(file_name, 'rb').read()

    def get_packets_from_file(self,file_name):
        file_bytes = self.get_bytes_from_file(file_name)
        file_length = len(file_bytes)
        seq_count = 0
        pkt_list = []
        for i in range(0, file_length, 500):
            if i + 500 > file_length:
                pkt = Packet(seqno=seq_count, data=file_bytes[i:], type='bytes')
            else:
                pkt = Packet(seqno=seq_count, data=file_bytes[i:i + 500], type='bytes')
            pkt_list.append(pkt)
            seq_count += 1
        self.file_len = len(pkt_list)
        self.pkt_list = pkt_list
        return pkt_list

    def handle_client(self, address, protocol):
        cl_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        cl_sock.bind((self.host,self.client_port))
        print('Connection acquired with client: '+str(address[1])+'... handling')
        self.send(protocol,[self,cl_sock,address])

    def send_client_port(self, socket, address):
        self.client_num += 1
        self.client_port = self.port+self.client_num
        pkt = Packet(seqno=0, data=self.client_port.__str__().encode()).pack()
        socket.sendto(pkt, address)
        ack, add = socket.recvfrom(600)
        ack_p = Packet(pkd_data=ack, type='ack')
        if ack_p.checksum == calc_checksum(str(self.client_port)):
            print('Received new port ack...')

    def send_file_len(self, socket, address, data):
        recv_pkt = Packet(pkd_data=data)
        # print(recv_pkt.seqno, recv_pkt.data.decode())
        print('Required file: '+str(recv_pkt.data.decode()))
        self.req_file = str(recv_pkt.data.decode())
        self.get_packets_from_file(self.req_file)
        pkt = Packet(seqno=0, data=str(self.file_len).encode()).pack()
        socket.sendto(pkt, address)
        ack, add = socket.recvfrom(600)
        ack_p = Packet(pkd_data=ack, type='ack')
        if ack_p.checksum == calc_checksum(str(self.file_len)):
            print('Received file len ack...')

    def send_rdt_protocol(self,socket, data,address):
        pkt= Packet(data=data.encode()).pack()
        socket.sendto(pkt,address)
        ack, add = socket.recvfrom(600)
        ack_p = Packet(pkd_data=ack, type='ack')
        if ack_p.checksum == calc_checksum(str(self.client_port)):
            print('Received protocol ack...')

    def send(self, protocol, params):
        rdt = RDTProtocols(self)
        send_call = getattr(rdt, protocol)
        if send_call:
            send_call(*params)

    def start(self):
        self.socket.bind((self.host, self.port))
        while True:
            print('Waiting for connection...')
            data, address = server.socket.recvfrom(600)
            print('Client# ', self.client_num+1, ' connected.')
            self.send_file_len(server.socket, address, data)
            self.send_client_port(server.socket, address)
            pid = os.fork()
            if pid == 0:
                self.handle_client(address,'go_back_n')
                print('Client# ',self.client_num,' finished successfully.')


server = Server('server.in')
server.start()