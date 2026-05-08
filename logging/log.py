import sys
import time
import threading
import argparse
import subprocess
import uiautomator2 as u2
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

# 可在代码中指定默认设备序列号（优先级低于命令行参数）
# 例如: DEFAULT_SERIAL = 'emulator-5554'
DEFAULT_SERIAL = None


# 点击元素 即拿到元素相关的文本打印 如果没有的话就打印元素的描述
def log_element_click(element, element_info=None):
    """
    记录元素点击的日志信息

    Args:
        element: uiautomator2的元素对象
        element_info: 可选的元素信息字典
    """
    try:
        # 尝试获取元素的文本
        try:
            text = element.get_text()
        except Exception:
            text = None

        if text and text.strip():
            print(f"点击元素 - 文本: {text}")
            return

        # 如果没有文本，尝试获取元素的描述
        info = getattr(element, 'info', {}) or {}
        description = info.get('contentDescription', '')

        if description and description.strip():
            print(f"点击元素 - 描述: {description}")
            return

        # 如果既没有文本也没有描述，打印元素的其他信息
        resource_id = info.get('resourceName', 'N/A')
        class_name = info.get('className', 'N/A')
        print(f"点击元素 - resourceId: {resource_id}, className: {class_name}")

    except Exception as e:
        print(f"获取元素信息失败: {e}")


def click_with_log(d, selector=None, **kwargs):
    """
    带日志的元素点击函数

    Args:
        d: uiautomator2设备对象
        selector: 元素选择器（备用），可以是text等
        **kwargs: 其他选择器参数，如 text, resourceId, className, description

    Returns:
        bool: 点击是否成功
    """
    try:
        # 根据选择器类型查找元素
        if 'text' in kwargs:
            element = d(text=kwargs['text'])
        elif 'resourceId' in kwargs:
            element = d(resourceId=kwargs['resourceId'])
        elif 'className' in kwargs:
            element = d(className=kwargs['className'])
        elif 'description' in kwargs:
            element = d(description=kwargs['description'])
        elif selector is not None:
            element = d(text=selector)
        else:
            print('没有有效的选择器')
            return False

        # 等待元素出现
        timeout = float(kwargs.get('timeout', 5))
        if element.wait(timeout=timeout):
            # 记录元素信息
            log_element_click(element)

            # 点击元素
            element.click()
            return True
        else:
            print(f"未找到元素: {selector or kwargs}")
            return False

    except Exception as e:
        print(f"点击元素失败: {e}")
        return False


def get_connected_adb_devices():
    """返回adb检测到的设备序列号列表（状态为 device）。"""
    try:
        completed = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        lines = completed.stdout.strip().splitlines()
        devices = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'device':
                devices.append(parts[0])
        return devices
    except FileNotFoundError:
        print('找不到 adb，可执行文件未安装或未加入 PATH')
        return []
    except Exception as e:
        print(f'adb 执行失败: {e}')
        return []


def attempt_adb_root():
    """尝试执行 adb root 并返回是否成功或已 root。"""
    try:
        completed = subprocess.run(['adb', 'root'], capture_output=True, text=True)
        out = (completed.stdout or '') + (completed.stderr or '')
        if 'adbd cannot run as root' in out or 'cannot run as root' in out:
            return False
        # some devices reply with 'restarting adbd as root'
        if 'restarting' in out or completed.returncode == 0:
            return True
        return False
    except Exception:
        return False


def parse_bounds(bounds_str):
    # 格式: "[left,top][right,bottom]"
    m = re.findall(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if not m:
        return None
    l, t, r, b = map(int, m[0])
    return (l, t, r, b)


def find_element_at(d, x, y):
    """通过 uiautomator2 dump 的 UI XML 在 (x,y) 找到最小包含该点的元素并返回其属性字典。"""
    try:
        # 尝试获取当前 UI XML
        xml = d.dump_hierarchy() if hasattr(d, 'dump_hierarchy') else d.dump()
    except Exception:
        try:
            xml = d.dump()
        except Exception as e:
            print(f'获取 UI 层级失败: {e}')
            return None

    try:
        root = ET.fromstring(xml)
    except Exception as e:
        print(f'解析 UI XML 失败: {e}')
        return None

    candidates = []
    for node in root.iter():
        attrib = node.attrib
        bounds = attrib.get('bounds') or attrib.get('bounds')
        if not bounds:
            continue
        rect = parse_bounds(bounds)
        if not rect:
            continue
        l, t, r, b = rect
        if l <= x <= r and t <= y <= b:
            area = (r - l) * (b - t)
            candidates.append((area, attrib))

    if not candidates:
        return None

    # 选择最小区域的元素，通常更贴近目标
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def adb_touch_listener(device_ref, stop_event, require_root=True):
    """使用 adb shell getevent 监听触摸，触发后使用 uiautomator2 定位元素并打印信息。"""
    if require_root:
        ok = attempt_adb_root()
        if not ok:
            print('注意: 未能以 root 模式启动 adbd，部分设备可能无法读取触摸事件或坐标。')

    # 启动 getevent
    print('启动 adb getevent 监听触摸（需要设备允许并且可能需要 root）...')
    try:
        p = subprocess.Popen(['adb', 'shell', 'getevent', '-lt'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        print('找不到 adb，可执行文件未安装或未加入 PATH')
        stop_event.set()
        return
    except Exception as e:
        print(f'启动 getevent 失败: {e}')
        stop_event.set()
        return

    current_x = None
    current_y = None
    pressed = False

    try:
        while not stop_event.is_set():
            line = p.stdout.readline()
            if not line:
                if p.poll() is not None:
                    break
                time.sleep(0.01)
                continue
            line = line.strip()
            # 尝试匹配坐标和触摸事件
            # 常见行例如: \t0003 0035 000003e8
            m = re.search(r'0035\s+([0-9a-fA-Fx]+)', line)
            if m:
                try:
                    current_x = int(m.group(1), 0)
                except Exception:
                    pass
                continue
            m = re.search(r'0036\s+([0-9a-fA-Fx]+)', line)
            if m:
                try:
                    current_y = int(m.group(1), 0)
                except Exception:
                    pass
                continue

            # 匹配 BTN_TOUCH (按/抬)
            m = re.search(r'014a\s+00000000\s+0000000([01])', line)
            if m:
                val = m.group(1)
                if val == '1':
                    pressed = True
                else:
                    # 抬起，视为一次点击
                    pressed = False
                    if current_x is not None and current_y is not None:
                        # 使用 uiautomator2 查找元素
                        d = device_ref.get('device')
                        if d is None:
                            print('设备未连接，无法获取元素信息')
                            continue
                        # 屏幕坐标通常以设备像素为单位
                        elem = find_element_at(d, current_x, current_y)
                        if elem:
                            # 打印优先级文本 > content-desc > resource-id > class
                            text = elem.get('text') or elem.get('label') or ''
                            desc = elem.get('content-desc') or elem.get('contentDescription') or elem.get('contentDescription')
                            resource = elem.get('resource-id') or elem.get('resourceName') or elem.get('resourceId')
                            class_name = elem.get('class') or elem.get('className')
                            if text and text.strip():
                                print(f'点击元素 - 文本: {text}')
                            elif desc and desc.strip():
                                print(f'点击元素 - 描述: {desc}')
                            else:
                                print(f'点击元素 - resourceId: {resource or "N/A"}, className: {class_name or "N/A"}')
                        else:
                            print(f'点击坐标: ({current_x},{current_y})，未找到对应元素')
                    # reset coords after reporting
                    current_x = None
                    current_y = None
                continue

            # 有些设备输出格式不同，尝试识别 ABS_MT_POSITION_X/Y 的十进制值
            m = re.search(r'ABS_MT_POSITION_X.*?(\d+)', line)
            if m:
                try:
                    current_x = int(m.group(1))
                except Exception:
                    pass
                continue
            m = re.search(r'ABS_MT_POSITION_Y.*?(\d+)', line)
            if m:
                try:
                    current_y = int(m.group(1))
                except Exception:
                    pass
                continue

    finally:
        try:
            p.terminate()
        except Exception:
            pass



def connect_device(serial, reconnect_attempts=3, reconnect_interval=2):
    """尝试连接到指定设备，失败则重试，成功返回 uiautomator2 设备对象或 None。"""
    for attempt in range(1, reconnect_attempts + 1):
        try:
            d = u2.connect(serial)
            # 简单的健康检查
            _ = d.info
            print(f'已连接设备: {serial}')
            return d
        except Exception as e:
            print(f'连接设备 {serial} 失败（第 {attempt} 次）: {e}')
            time.sleep(reconnect_interval)
    return None


def command_thread_func(device_ref, stop_event):
    """后台线程：从 stdin 读取命令并执行，目前支持 click 命令和 exit。"""
    print('输入命令示例: click text=登录 或 click resourceId=com.example:id/btn; 输入 exit 退出')
    while not stop_event.is_set():
        try:
            line = input()
        except EOFError:
            break
        except Exception:
            break

        line = line.strip()
        if not line:
            continue
        if line.lower() == 'exit':
            print('收到 exit，退出进程')
            stop_event.set()
            break

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == 'click':
            kwargs = {}
            selector = None
            for a in args:
                if '=' in a:
                    k, v = a.split('=', 1)
                    kwargs[k] = v
                else:
                    # 不带 key 的第一个参数当作 selector
                    if selector is None:
                        selector = a

            d = device_ref.get('device')
            if d is None:
                print('设备未连接，无法执行 click')
                continue

            ok = click_with_log(d, selector, **kwargs)
            print('click ->', '成功' if ok else '失败')
        else:
            print(f'未知命令: {cmd}')


def main():
    parser = argparse.ArgumentParser(description='uiautomator2 常驻监听脚本，监听指定设备。')
    parser.add_argument('--serial', required=False, help='设备序列号（adb devices 列表中的 id），若不提供从代码 DEFAULT_SERIAL 或 adb 首个设备选择')
    parser.add_argument('--interval', type=float, default=2.0, help='设备状态轮询间隔（秒）')
    parser.add_argument('--mode', choices=['adb', 'accessibility'], default='adb', help='监听模式：adb（通过 getevent 监听触摸）或 accessibility（需要安装 AccessibilityService APK）')
    args = parser.parse_args()

    # 选择设备序列号，优先级: 命令行 > DEFAULT_SERIAL > adb devices 第一个
    serial = args.serial or DEFAULT_SERIAL

    connected = get_connected_adb_devices()
    if not serial:
        if connected:
            serial = connected[0]
            print(f'未指定 serial，使用 adb devices 中第一个设备: {serial}')
        else:
            print('未指定设备，且 adb devices 中没有设备，脚本退出')
            sys.exit(2)

    if serial not in connected:
        print(f'指定设备 {serial} 未在 adb devices 列表中，已连接设备：{connected}，脚本退出')
        sys.exit(2)

    d = connect_device(serial)
    if d is None:
        print('无法连接到设备，脚本退出')
        sys.exit(3)

    device_ref = {'device': d}
    stop_event = threading.Event()

    # 启动命令线程
    t = threading.Thread(target=command_thread_func, args=(device_ref, stop_event), daemon=True)
    t.start()

    # 根据监听模式启动触摸监听
    if args.mode == 'adb':
        touch_thread = threading.Thread(target=adb_touch_listener, args=(device_ref, stop_event), daemon=True)
        touch_thread.start()
    else:
        print('accessibility 模式尚未实现。要使用该模式，需要在设备上安装并启用一个辅助服务 APK，授权后可将点击事件直接回传到该脚本（需额外开发）。')

    try:
        # 主循环：监控设备是否仍在 adb devices 中
        while not stop_event.is_set():
            time.sleep(args.interval)
            connected = get_connected_adb_devices()
            if serial not in connected:
                print(f'设备 {serial} 从 adb 中断开，尝试重连...')
                # 尝试重连
                d = connect_device(serial, reconnect_attempts=3, reconnect_interval=2)
                if d is None:
                    print('重连失败，脚本退出')
                    stop_event.set()
                    break
                device_ref['device'] = d
            # else: 设备存在，短日志可省略或扩展为心跳

    except KeyboardInterrupt:
        print('收到 KeyboardInterrupt，退出')
        stop_event.set()


if __name__ == '__main__':
    main()
