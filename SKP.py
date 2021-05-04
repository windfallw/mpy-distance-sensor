import machine
import struct

crcTable \
    = [0, 49, 98, 83, 196, 245, 166, 151, 185, 136, 219, 234, 125, 76, 31, 46, 67, 114, 33, 16, 135, 182, 229, 212,
       250, 203, 152, 169, 62, 15, 92, 109, 134, 183, 228, 213, 66, 115, 32, 17, 63, 14, 93, 108, 251, 202, 153, 168,
       197, 244, 167, 150, 1, 48, 99, 82, 124, 77, 30, 47, 184, 137, 218, 235, 61, 12, 95, 110, 249, 200, 155, 170,
       132, 181, 230, 215, 64, 113, 34, 19, 126, 79, 28, 45, 186, 139, 216, 233, 199, 246, 165, 148, 3, 50, 97, 80,
       187, 138, 217, 232, 127, 78, 29, 44, 2, 51, 96, 81, 198, 247, 164, 149, 248, 201, 154, 171, 60, 13, 94, 111,
       65, 112, 35, 18, 133, 180, 231, 214, 122, 75, 24, 41, 190, 143, 220, 237, 195, 242, 161, 144, 7, 54, 101, 84,
       57, 8, 91, 106, 253, 204, 159, 174, 128, 177, 226, 211, 68, 117, 38, 23, 252, 205, 158, 175, 56, 9, 90, 107,
       69, 116, 39, 22, 129, 176, 227, 210, 191, 142, 221, 236, 123, 74, 25, 40, 6, 55, 100, 85, 194, 243, 160, 145,
       71, 118, 37, 20, 131, 178, 225, 208, 254, 207, 156, 173, 58, 11, 88, 105, 4, 53, 102, 87, 192, 241, 162, 147,
       189, 140, 223, 238, 121, 72, 27, 42, 193, 240, 163, 146, 5, 52, 103, 86, 120, 73, 26, 43, 188, 141, 222, 239,
       130, 179, 224, 209, 70, 119, 36, 21, 59, 10, 89, 104, 255, 206, 157, 172]


def digest(buff):
    crc = 0x00
    for i in range(1, 6):  # 1-5 key1 value4
        crc ^= buff[i]
        crc = crcTable[crc]  # 查表法
        # ==================循环计算法==================
        # for j in range(8):
        #     if crc & 0x80:
        #         crc = ((crc << 1) & 0xFF) ^ 0x31
        #     else:
        #         crc = (crc << 1) & 0xFF
        # ============================================
    if crc == buff[6]:
        return True
    return False


class LP20:
    """
    LP20/40 激光测距模块
    """
    buff = b''
    buffs = ()

    limit = 0
    distance = 99999

    startMeasure = b'\x55\x05\x00\x00\x00\x00\xCC\xAA'  # 启动测量
    stopMeasure = b'\x55\x06\x00\x00\x00\x00\x88\xAA'  # 停止测量

    singleMode = b'\x55\x0D\x00\x00\x00\x01\xC3\xAA'  # 测量模式为单次测量（需要发测量命令给设备）
    autoMode = b'\x55\x0D\x00\x00\x00\x00\xF2\xAA'  # 测量模式为连续测量开机启动
    autoButCloseMode = b'\x55\x0D\x00\x00\x00\x02\x90\xAA'  # 测量模式为连续测量开机不启动

    deviceInfo = b'\x55\x01\x00\x00\x00\x00\xD3\xAA'  # 获取设备信息（返回二帧的设备信息数据）
    byteOutPut = b'\x55\x04\x00\x00\x00\x01\x2E\xAA'  # 设置设备输出数据的格式为字节（默认）
    pixhawkOutPut = b'\x55\x04\x00\x00\x00\x02\x7D\xAA'  # 设置设备输出数据的格式为Pixhawk格式（就是字符串直接输出简单粗暴，但是影响速度不推荐）

    def __init__(self, Uart, RX, TX, debug=False, auto=True):
        self.laser = machine.UART(Uart, baudrate=921600, bits=8, rx=RX, tx=TX, stop=1, parity=None, timeout=0)
        self.debug = debug
        self.auto = auto

        if self.auto:
            self.write(self.autoMode)
        else:
            self.write(self.singleMode)

    def write(self, cmd):
        self.laser.write(cmd)

    def start(self):
        """
        可用做自动测量的第一次启动指令，也可用做单次测量模式每次发送的指令

        """

        self.write(self.startMeasure)

    def checkExtent(self):
        if self.distance < self.limit:
            return True
        return False

    def unpack(self):
        if len(self.buff) == 8 and self.buff[0] == 0x55 and self.buff[7] == 0xAA and digest(self.buff):
            self.buffs = struct.unpack('!ssIss', self.buff)
            if self.buff[1] == 0x07 and self.buff[2] == 0x00:
                self.distance = self.buffs[2] / 1000  # 单位毫米换算成米
                # print(self.distance)
                return True
        elif self.debug:
            print(self.buff)
        return False

    def any(self):
        if not self.auto:
            self.start()
        if self.laser.any():
            self.buff = self.laser.read(8)
            if self.unpack():
                return self.checkExtent()
