## 游戏是画面 没有xpath 一般是ocr识别文字 输出坐标
## 注意你在什么分辨率下截的图 就要在什么分辨率下打开模拟器否则识别不到点击

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
import logging
import json
import urllib.request

# 关闭 PaddleOCR / ppocr 的 DEBUG 日志
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("ppocr").setLevel(logging.WARNING)
logging.getLogger("paddle").setLevel(logging.WARNING)

ocr = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False)

def click_text(d, target_text, timeout=10, interval=1, img_path="screen.png", debug=False, debug_dir="debug"):
    start = time.time()
    last_texts = []

    if debug:
        os.makedirs(debug_dir, exist_ok=True)

    print(f"尝试点击文字: {target_text}")

    while time.time() - start < timeout:
        d.screenshot(img_path)

        result = ocr.ocr(img_path, cls=False)

        texts = []
        if result and result[0]:
            for line in result[0]:
                try:
                    text = line[1][0]
                except Exception:
                    continue
                texts.append(text)

        last_texts = texts

        if debug:
            print(f"OCR识别到: {texts}")
            ts = time.strftime("%Y%m%d_%H%M%S")
            try:
                img = _imread_robust(img_path)
                if img is None:
                    img = cv2.imread(img_path)
                if img is not None:
                    cv2.imencode('.png', img)[1].tofile(os.path.join(debug_dir, f"{ts}_ocr.png"))
            except Exception:
                pass

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

    print(f"未找到文字: {target_text}；最后一次OCR={last_texts}")
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

def _log_request(message: str, level: str = "info", url: str = "http://127.0.0.1:9191/log"):
    """向本地日志服务发送一条日志（避免引入额外依赖）。"""
    try:
        payload = json.dumps({"message": message, "level": level}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            resp.read()
    except Exception:
        # 日志上报失败不影响主流程
        pass

# 添加参数 是否点击文字
def click_icon(
    d,
    template_path,
    is_click_text=False,
    timeout=10,
    interval=1,
    threshold=0.8,
    img_path="screen.png",
    debug=False,
    debug_dir="debug",
    scales=None,
    grayscale=True,
    log_request: bool = True,
    log_url: str = "http://127.0.0.1:9191/log",
):
    """
    template_path: 小图标路径，比如 gift.png
    threshold: 匹配阈值，越高越严格（推荐 0.65~0.9）
    scales: 多尺度匹配缩放列表，None 则使用默认 [0.7..1.3]
    grayscale: 灰度匹配通常更稳（降低颜色/发光影响）
    debug: 为 True 时会落盘截图与匹配可视化，便于调参/确认模板是否正确
    log_request: 是否调用本地日志接口上报“点击：<图片名>”
    """
    template_path = os.path.abspath(template_path)

    ## 获取template_path的文件名（不含扩展名）作为目标文字
    target_text = os.path.splitext(os.path.basename(template_path))[0]

    if log_request:
        _log_request(f"点击：{target_text}", level="info", url=log_url)

    ## 根据is_click_text 先尝试使用文字匹配点击，如果成功则直接返回，避免后续的模板匹配计算开销
    if is_click_text and click_text(d, target_text, timeout=timeout, interval=interval, debug=debug, debug_dir=debug_dir):
        print(f"点击文字成功click_icon: {template_path}")
        return True

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


def wait_for_text_disappear(
    d,
    target_text: str,
    interval: float = 1.0,
    initial_wait: float = 3.0,
    img_path: str = "screen.png",
    debug: bool = False,
    debug_dir: str = "debug",
    appear_timeout: float = 10.0,
    disappear_timeout: float = 60.0,
) -> bool:
    """等待某段文字从屏幕上消失（严格 有->无 才 True）。

    参数：
      - appear_timeout：等待文字“首次出现”的最长时间（秒）。超时仍未出现 => False
      - disappear_timeout：文字出现后，等待其“消失”的最长时间（秒）。超时仍未消失 => False

    返回：
      - True：检测到文字经历了“有 -> 无”
      - False：未在 appear_timeout 内出现；或出现后未在 disappear_timeout 内消失
    """

    if initial_wait and initial_wait > 0:
        time.sleep(initial_wait)

    if debug:
        os.makedirs(debug_dir, exist_ok=True)

    # 先等出现
    start_appear = time.time()
    while time.time() - start_appear < appear_timeout:
        d.screenshot(img_path)
        result = ocr.ocr(img_path, cls=False)

        found = False
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                if target_text in text:
                    found = True
                    break

        if found:
            if debug:
                print(f"检测到文字首次出现: {target_text}")
            break

        if debug:
            elapsed = time.time() - start_appear
            print(f"等待文字出现中: {target_text} elapsed={elapsed:.1f}s")

        time.sleep(interval)
    else:
        if debug:
            print(f"等待文字出现超时: {target_text} appear_timeout={appear_timeout}s")
        return False

    # 再等消失
    start_disappear = time.time()
    while time.time() - start_disappear < disappear_timeout:
        d.screenshot(img_path)
        result = ocr.ocr(img_path, cls=False)

        found = False
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                if target_text in text:
                    found = True
                    break

        if not found:
            print(f"文字已从有到无: {target_text}")
            return True

        if debug:
            elapsed = time.time() - start_disappear
            print(f"等待文字消失中: {target_text} elapsed={elapsed:.1f}s")
            ts = time.strftime("%Y%m%d_%H%M%S")
            try:
                img = _imread_robust(img_path)
                if img is None:
                    img = cv2.imread(img_path)
                if img is not None:
                    cv2.imencode('.png', img)[1].tofile(os.path.join(debug_dir, f"{ts}_wait_{target_text}.png"))
            except Exception:
                pass

        time.sleep(interval)

    if debug:
        print(f"等待文字消失超时: {target_text} disappear_timeout={disappear_timeout}s")
    return False


def wait_for_text_appear(d, target_text, timeout=10, interval=1):
    start = time.time()

    while time.time() - start < timeout:
        d.screenshot("screen.png")
        result = ocr.ocr("screen.png", cls=False)

        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                if target_text in text:
                    print(f"检测到文字: {target_text}")
                    return True

        print(f"等待文字出现中: {target_text}")
        time.sleep(interval)

    print(f"等待文字出现超时: {target_text} timeout={timeout}s")
    return False