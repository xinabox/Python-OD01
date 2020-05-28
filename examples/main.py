from xCore import xCore
from xOD01 import xOD01

OD01 = xOD01()

OD01.clear()

while True:

    OD01.text("Hello World", 0, 0)
    # scroll right
    OD01.hw_scroll_h()
    xCore.sleep(3000)
    # scroll left
    OD01.hw_scroll_h(False)
    xCore.sleep(3000)
    OD01.hw_scroll_off()
    xCore.sleep(3000)
    OD01.clear()
    xCore.sleep(1000)