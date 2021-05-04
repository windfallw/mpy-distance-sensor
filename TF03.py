import machine


class TF03:
    """
    TF03 激光测距模块

    """

    buff = b''  # 实时帧(9字节)
    distance = 99999  # 实时测距值(buff转换后) 单位cm 测距模块最大测量距离为 18000  预设报警阈值最大为 18000 将初始值设为99999等待重置。

    def __init__(self, Uart, RX, TX, limit=200, debug=False):
        self.laser = machine.UART(Uart, baudrate=115200, bits=8, rx=RX, tx=TX, stop=1, parity=None, timeout=0)
        self.limit = limit  # 报警预设值 单位cm (小于该值触发报警)
        self.debug = debug

    def unpack(self):
        """
        Byte0 帧头 0x59
        Byte1 帧头 0x59
        Byte2 DIST_L DIST 低八位
        Byte3 DIST_H DIST 高八位
        Byte4 Byte5 Byte6 Byte7 保留
        Byte8 校验

        """

        if len(self.buff) == 9 and self.buff[0] == self.buff[1] == 0x59 and self.checksum():
            self.distance = self.buff[2] + (self.buff[3] << 8)
            # print(self.buff[2], self.buff[3] << 8, self.extent)
            # print(self.extent / 100)  # 单位厘米换算成米
            return True
        elif self.debug:
            print(self.buff)
        return False

    def checksum(self):
        """
        checksum = 前 Len–1 字节数据和的低 8bit
        取高八位：num >> 8;
        取低八位：num & 0xff。

        """

        bytesum = 178  # 0x59+0x59=178
        for byte in self.buff[2:-1]:
            bytesum += byte
        if bytesum & 0xff == self.buff[-1]:
            return True
        return False

    def checkExtent(self):
        """
        小于预设范围触发报警

        """

        if self.distance < self.limit:
            return True
        return False

    def any(self):
        """
        测量值大于预设报警值返回True，通过此函数判断是否触发报警

        """

        if self.laser.any():
            self.buff = self.laser.read(9)
            if self.unpack():
                return self.checkExtent()
