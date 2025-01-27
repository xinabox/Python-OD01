# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

import time
import framebuf
from xCore import xCore

# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)
SET_HWSCROLL_OFF    = const(0x2e)
SET_HWSCROLL_ON     = const(0x2f)
SET_HWSCROLL_RIGHT  = const(0x26)
SET_HWSCROLL_LEFT   = const(0x27)
#SET_HWSCROLL_VR     = const(0x29)
#SET_HWSCROLL_VL     = const(0x2a)


class xOD01:
    def __init__(self, addr=0x3c, width=128, height=64,external_vcc=False):
        self.i2c = xCore()
        self.addr = addr
        self.temp = bytearray(2)
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer1(self.buffer, self.width, self.height)
        self.poweron()
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, # off
            # address setting
            SET_MEM_ADDR, 0x00, # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL, 0x30, # 0.83*Vcc
            # display
            SET_CONTRAST, 0xff, # maximum
            SET_ENTIRE_ON, # output follows RAM contents
            SET_NORM_INV, # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)
        self.show()

    def clear(self):
        self.fill(0)
        self.show()

    def hw_scroll_off(self):
        self.write_cmd(SET_HWSCROLL_OFF) # turn off scroll

    def hw_scroll_h(self, direction=True):   # default to scroll right
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_LEFT)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x07) # start page = page 7
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x00) # end page = page 0
        else:
            self.write_cmd(SET_HWSCROLL_RIGHT)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x00) # start page = page 0
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x07) # end page = page 7

        self.write_cmd(0x00)
        self.write_cmd(0xff)
        self.write_cmd(SET_HWSCROLL_ON) # activate scroll

    def write_cmd(self, cmd):
        self.temp[0] = 0x80 # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.write(self.addr, self.temp)

    def write_data(self, buf):
        self.temp[0] = self.addr << 1
        self.temp[1] = 0x40 # Co=0, D/C#=1
        self.i2c.start()
        self.i2c.write_(self.temp)
        self.i2c.write_(buf)
        self.i2c.stop()

    def poweron(self):
        pass
"""
    # This is for the diagonal scroll, it shows wierd actifacts on the lcd!!
    def hw_scroll_diag(self, direction=True):   # default to scroll verticle and right
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_VL)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x07) # start page = page 7
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x00) # end page = page 0
            self.write_cmd(self.height)
        else:
            self.write_cmd(SET_HWSCROLL_VR)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x00) # start page = page 0
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x07) # end page = page 7
            self.write_cmd(self.height)

        self.write_cmd(0x00)
        self.write_cmd(0xff)
        self.write_cmd(SET_HWSCROLL_ON) # activate scroll
"""
