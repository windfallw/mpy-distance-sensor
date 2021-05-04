import machine
import time


class SK60:
    """
    SK60激光测距模块
    手动测距需要使用定时器
    自动测距无需使用定时器

    """

    ctrlCmd = \
        {
            'open': 'O',
            'close': 'C',
            'readStatus': 'S',
            'auto': 'D',
            'fast': 'F',
            'slow': 'M',
            'version': 'V',
            'powerOff': 'X'
        }
    distance = 999
    accurate = 0
    NoResponse = 0

    def __init__(self, UartNum, rx, tx, ctlPin):
        """
        :param UartNum: 使用哪个串口 1-2
        :param rx: rx的映射管脚
        :param tx: tx的映射管脚
        :param ctlPin: 连续测距的控制管脚
        :param Timer: 使用哪个定时器 0-3

        """

        self.laserContinue = machine.Pin(ctlPin, machine.Pin.OUT)
        self.uart = machine.UART(UartNum, baudrate=19200, bits=8, rx=rx, tx=tx, stop=1, parity=None, timeout=1500)
        self.uart.write('O')

    def AutoMode(self):
        self.laserContinue.value(0)
        self.uart.write('F')
        self.recvData()

    def ManualMode(self, Timer):
        self.laserContinue.value(1)
        self.uart.write('F')
        tim = machine.Timer(Timer)
        tim.init(period=1500, mode=machine.Timer.PERIODIC,
                 callback=lambda t: self.measure())
        self.recvData()

    def measure(self):
        self.uart.write('F')

    def recvData(self):
        while True:
            try:
                if self.NoResponse == 1000:
                    # print("One laser maybe error.")
                    self.uart.write('F')
                    self.NoResponse = 0

                if self.uart.any():
                    UartRecv = self.uart.readline().decode()
                    data = UartRecv.replace('F', '').replace(':', '').replace(' ', '') \
                        .replace('m', '').replace('\r\n', '').split(',')
                    self.distance = float(data[0])
                    self.accurate = int(data[1])
                    print(self.distance, self.accurate)
                    self.NoResponse = 0

                else:
                    self.NoResponse += 1
                    time.sleep_ms(50)  # 找点事做防止线程卡死循环

            except Exception as e:
                print(UartRecv)
                print('Uart error: ', e)
