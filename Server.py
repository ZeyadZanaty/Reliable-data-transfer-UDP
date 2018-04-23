import socket  # Import socket module
import os
import struct
from Packet import Packet
import threading


def get_bytes_from_file(file_name):
    return open(file_name, 'rb').read()


def get_packets_from_file(file_name):
    file_bytes = get_bytes_from_file(file_name)
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
    return pkt_list


def go_back_n(file_name, server_socket, client_address,window_size=5):
    pkt_list = get_packets_from_file(file_name)
    # server_socket.settimeout(3)
    flag = False
    i = 0
    while i < len(pkt_list):
        current_pkt = pkt_list[i:window_size+i]
        if window_size+i > len(pkt_list):
            current_pkt = pkt_list[i:]
        for pkt in current_pkt:
            # pkt =pkt_list[w]
            pkd_packet = pkt.pack(type='bytes')
            server_socket.sendto(pkd_packet,client_address)
            if flag is True:
                flag = False
                break
        for pkt in current_pkt:
            # pkt = pkt_list[w]
            try:
                ack = server_socket.recv(6000)
                unpkd_ack = Packet(pkd_data=ack,type='ack')
                print('Ack# '+ str(unpkd_ack.seqno) + ' received')
                if unpkd_ack.checksum == pkt.checksum:
                    i += 1
                else:
                    flag = True
                    break
            except socket.timeout as e:
                print('Packet # '+str(pkt.seqno)+' ack has timed out....resending')
                break
    # for i, pkt in enumerate(pkt_list):
    #     # print(pkt.length, pkt.seqno)
    #     pkd_packet = pkt.pack(type='bytes')
    #     server_socket.sendto(pkd_packet, client_address)
    #     try:
    #         ack = server_socket.recv(6000)
    #         unpkd_ack = Packet(pkd_data=ack,type='ack')
    #         print('Ack# '+ str(unpkd_ack.seqno) + ' received')
    #         i += 1
    #     except socket.timeout as e:
    #         print('Packet #' + str(pkt.seqno) + 'has timed out....resending')
    #         break


class Server:

    def __init__(self, file_name):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = socket.gethostbyname('localhost')
        file = open(file_name, 'r')
        self.port = int(file.readline())
        self.window_size = int(file.readline())
        self.random_seed = int(file.readline())
        self.probability = float(file.readline())
        file.close()

    def handle_client(self, data, address):
        cl_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        cl_sock.bind((self.host,self.port+address[1]-1000))
        print(cl_sock.getsockname())
        print('Connection acquired with client: '+str(address[1])+'... handling')
        recv_pkt = Packet(pkd_data=data)
        print(recv_pkt.seqno, recv_pkt.data.decode())
        print('Required file: ' + str(recv_pkt.data.decode()))
        go_back_n(recv_pkt.data.decode(), cl_sock, address)

    def start(self):
        self.socket.bind((server.host, server.port))
        while True:
            print('Waiting for connection...')
            data, address = server.socket.recvfrom(6000)
            pid = os.fork()
            if pid == 0:
                self.handle_client(data, address)

server = Server('server.in')
server.start()