import uiautomator2 as u2
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')
d = u2.connect()

print("设备尺寸:", d.window_size())

img = Image.open("screen.png")
print("截图尺寸:", img.size)