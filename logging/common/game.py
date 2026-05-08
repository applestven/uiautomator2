## 游戏是画面 没有xpath 一般是ocr识别文字 输出坐标

## cpu 方式
# pip install paddlepaddle==2.6.2
# pip install paddleocr==2.8.1

# python -m pip install --force-reinstall paddlepaddle==2.6.1
# python -m pip install --force-reinstall paddleocr==2.8.1

## 是否安装 

## python -m pip show paddlepaddle

# 如果你是 CPU 跑就够了；GPU 另配。

##  查本机CUDA ：nvidia-smi
# NVIDIA-SMI 555.97                 Driver Version: 555.97         CUDA Version: 12.5   

# 然后可以直接这样：

from paddleocr import PaddleOCR
import time

ocr = PaddleOCR(use_angle_cls=False, lang="ch")


def click_text(d, target_text, timeout=10, interval=1, img_path="screen.png"):
    start = time.time()

    while time.time() - start < timeout:
        d.screenshot(img_path)

        result = ocr.ocr(img_path, cls=False)

        if not result or not result[0]:
            time.sleep(interval)
            continue

        for line in result[0]:
            box = line[0]
            text = line[1][0]

            if target_text in text:
                x = int((box[0][0] + box[2][0]) / 2)
                y = int((box[0][1] + box[2][1]) / 2)
                d.click(x, y)
                return True

        time.sleep(interval)

    return False

# 调用方式：

# import uiautomator2 as u2

# d = u2.connect_usb()

# click_text(d, "进入游戏")
# click_text(d, "确定")
# click_text(d, "刷新")