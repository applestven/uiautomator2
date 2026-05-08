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
import cv2
import time
import os
import numpy as np

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

def _imread_robust(path: str):
    """Windows 下 cv2.imread 对中文路径可能失败，用 imdecode 兜底。"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def click_icon(
    d,
    template_path,
    timeout=10,
    interval=1,
    threshold=0.8,
    img_path="screen.png",
    debug=False,
    debug_dir="debug",
    scales=None,
    grayscale=True,
):
    """
    template_path: 小图标路径，比如 gift.png
    threshold: 匹配阈值，越高越严格（推荐 0.65~0.9）
    scales: 多尺度匹配缩放列表，None 则使用默认 [0.7..1.3]
    grayscale: 灰度匹配通常更稳（降低颜色/发光影响）
    debug: 为 True 时会落盘截图与匹配可视化，便于调参/确认模板是否正确
    """
    template_path = os.path.abspath(template_path)

    if scales is None:
        scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

    template = _imread_robust(template_path)
    if template is None:
        template = cv2.imread(template_path)

    if template is None:
        # 输出更可读的诊断信息
        exists = os.path.exists(template_path)
        parent = os.path.dirname(template_path)
        try:
            siblings = os.listdir(parent) if os.path.isdir(parent) else []
        except Exception:
            siblings = []
        raise Exception(
            "模板图不存在或无法读取: {path}\n"
            "- exists: {exists}\n"
            "- parent: {parent}\n"
            "- files: {files}".format(
                path=template_path,
                exists=exists,
                parent=parent,
                files=siblings,
            )
        )

    if grayscale:
        template_base = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    else:
        template_base = template

    start = time.time()
    best = {"score": -1.0, "loc": None, "scale": None, "w": None, "h": None}

    if debug:
        os.makedirs(debug_dir, exist_ok=True)

    while time.time() - start < timeout:
        d.screenshot(img_path)

        screen = _imread_robust(img_path)
        if screen is None:
            screen = cv2.imread(img_path)
        if screen is None:
            time.sleep(interval)
            continue

        if grayscale:
            screen_m = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        else:
            screen_m = screen

        # 多尺度匹配
        cur_best = {"score": -1.0, "loc": None, "scale": None, "w": None, "h": None}
        for s in scales:
            if s == 1.0:
                tpl = template_base
            else:
                tpl = cv2.resize(template_base, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

            h, w = tpl.shape[:2]
            # 模板太大直接跳过
            if h >= screen_m.shape[0] or w >= screen_m.shape[1] or h < 8 or w < 8:
                continue

            res = cv2.matchTemplate(screen_m, tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val > cur_best["score"]:
                cur_best = {"score": float(max_val), "loc": max_loc, "scale": float(s), "w": int(w), "h": int(h)}

        if cur_best["score"] > best["score"]:
            best = cur_best

        print(
            "icon match best(score={score:.3f}, scale={scale}) threshold={th:.3f} template={name}".format(
                score=cur_best["score"],
                scale=cur_best["scale"],
                th=threshold,
                name=os.path.basename(template_path),
            )
        )

        if debug:
            ts = time.strftime("%Y%m%d_%H%M%S")
            # 落盘当前截图
            cv2.imencode('.png', screen)[1].tofile(os.path.join(debug_dir, f"{ts}_screen.png"))

            if cur_best["loc"] is not None:
                vis = screen.copy()
                x0, y0 = cur_best["loc"]
                w, h = cur_best["w"], cur_best["h"]
                cv2.rectangle(vis, (x0, y0), (x0 + w, y0 + h), (0, 255, 0), 2)
                cv2.putText(
                    vis,
                    f"score={cur_best['score']:.3f} scale={cur_best['scale']}",
                    (x0, max(20, y0 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.imencode('.png', vis)[1].tofile(os.path.join(debug_dir, f"{ts}_vis.png"))

        if cur_best["score"] >= threshold and cur_best["loc"] is not None:
            x0, y0 = cur_best["loc"]
            x = x0 + cur_best["w"] // 2
            y = y0 + cur_best["h"] // 2
            d.click(x, y)
            print(
                f"点击图标成功: {template_path} ({x},{y}) score={cur_best['score']:.3f} scale={cur_best['scale']}"
            )
            return True

        time.sleep(interval)

    print(
        f"未找到图标: {template_path} best_score={best['score']:.3f} best_loc={best['loc']} best_scale={best['scale']}"
    )
    return False


# 调用方式：

# import uiautomator2 as u2

# d = u2.connect_usb()

# click_text(d, "进入游戏")
# click_text(d, "确定")
# click_text(d, "刷新")