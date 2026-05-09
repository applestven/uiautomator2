from paddleocr import PaddleOCR
import sys
sys.stdout.reconfigure(encoding='utf-8')
ocr = PaddleOCR(use_angle_cls=False, lang='ch')

result = ocr.ocr("screen.png")

print(result)