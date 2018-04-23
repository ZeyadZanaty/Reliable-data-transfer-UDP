import struct


def calc_checksum(data, type='str'):
    encoded_data = data
    if type is not 'bytes':
        encoded_data = data.encode()
    i = 0
    checksum = 0
    while i < len(encoded_data):
        short1 = 0
        short1 = encoded_data[i]
        if (i + 1) < len(encoded_data):
            short1 += (encoded_data[i + 1] << 8)
        checksum += short1
        if (checksum & 0x10000) > 0:
            checksum = (checksum + 1) & 0xFFFF
        i += 2
    return ~checksum & 0xFFFF


class Packet:

    def __init__(self, pkd_data=None, seqno=0, data='', type='bytes', chk_sum=0):
        if pkd_data and type is not 'ack':
            var, data = self.unpack(pkd_data)
            self.checksum = var[0]
            self.length = var[1]
            self.seqno = var[2]
            if type == 'str':
                self.data = data.decode()
            else:
                self.data = data
        elif type == 'ack':
            if pkd_data:
                var = self.unpack(pkd_data,type=type)
                self.checksum = var[0]
                self.seqno = var[1]
            else:
                self.seqno = seqno
                self.checksum = chk_sum
        else:
            self.length = len(data) + 8
            self.seqno = seqno
            self.data = data
            self.checksum = calc_checksum(data,type=type)

    def unpack(self, data, type='bytes'):
        if type == 'ack':
            return struct.unpack('HH', data)
        else:
            size = struct.calcsize('HHI')
            return struct.unpack('HHI', data[:size]), data[size:]

    def pack(self, type='bytes'):
        if type == 'ack':
            return struct.pack('HH', self.checksum,self.seqno)
        if type == 'str':
            encoded_data = self.data.encode()
        else:
            encoded_data = self.data
        str_len = len(encoded_data)
        fmt = 'HHI%ds' % str_len
        packed_packet = struct.pack(fmt, self.checksum, self.length, self.seqno, encoded_data)
        return packed_packet
