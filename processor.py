# -- coding: utf-8 --

import requests
import os
import re
import base64
import threading
import concurrent.futures
import socket
import time
import random
import statistics
import sys
from typing import List, Dict, Tuple, Optional, Set, Union

# --- Global Constants & Variables ---

PRINT_LOCK = threading.Lock() # برای جلوگیری از تداخل در چاپ خروجی هنگام استفاده از تردها

# مسیر دایرکتوری خروجی: تنظیم شده روی "data"
OUTPUT_DIR = "data"

# لیست URLهای سابسکریپشن که کانفیگ‌ها از آن‌ها جمع‌آوری می‌شوند.
CONFIG_URLS: List[str] = [
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix",
"https://raw.githubusercontent.com/iboxz/free-v2ray-collector/refs/heads/main/main/vless",
"https://raw.githubusercontent.com/T3stAcc/V2Ray/refs/heads/main/Splitted-By-Protocol/vless.txt",
"https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/vless.txt",
"https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt",
"https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs.txt",
"https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",
"https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
"https://raw.githubusercontent.com/dream4network/telegram-configs-collector/refs/heads/main/protocols/vless",
"https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/refs/heads/main/sub/Mix/mix.txt",
"https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/refs/heads/main/config.txt",
"https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/vless.html",
"https://raw.githubusercontent.com/xyfqzy/free-nodes/refs/heads/main/nodes/vless.txt",
"https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/vless",
"https://raw.githubusercontent.com/Kolandone/v2raycollector/refs/heads/main/vless.txt",
"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt",
"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/22.txt",
"https://raw.githubusercontent.com/Awmiroosen/awmirx-v2ray/refs/heads/main/blob/main/v2-sub.txt",
"https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Vless.txt",
"https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt",
"https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix", "https://raw.githubusercontent.com/RaitonRed/ConfigsHub/refs/heads/main/Splitted-By-Protocol/vless.txt",
"https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt", "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Vless.txt", "https://raw.githubusercontent.com/Awmiroosen/awmirx-v2ray/refs/heads/main/blob/main/v2-sub.txt", "https://media.githubusercontent.com/media/gfpcom/free-proxy-list/refs/heads/main/list/vless.txt", "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/22.txt", "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt", "https://raw.githubusercontent.com/Kolandone/v2raycollector/refs/heads/main/vless.txt", "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/vless", "https://raw.githubusercontent.com/xyfqzy/free-nodes/refs/heads/main/nodes/vless.txt", "https://raw.githubusercontent.com/MAHDI-F-KHEDMAT/KHANEVADEGI/refs/heads/main/data/khanevadeh_base64.txt", "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/vless.html", "https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/refs/heads/main/config.txt", "https://raw.githubusercontent.com/crackbest/V2ray-Config/refs/heads/main/config.txt", "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/Splitted-By-Protocol/vless.txt",
"https://raw.githubusercontent.com/giromo/Xrey-collector/refs/heads/main/All_Configs_Sub.txt",
"https://raw.githubusercontent.com/dream4network/telegram-configs-collector/refs/heads/main/splitted/mixed",
"https://raw.githubusercontent.com/Matin-RK0/ConfigCollector/refs/heads/main/subscription.txt"

]

# نام فایل خروجی برای ذخیره کانفیگ‌های نهایی.
# تنظیم شده روی "KHANEVADEH_TLS_base64.txt"
OUTPUT_FILENAME: str = os.getenv("TLS_OUTPUT_FILENAME", "KHANEVADEH_TLS") + "_base64.txt"

# زمان‌بندی‌ها و تعداد تست‌ها برای ارزیابی کیفیت کانفیگ‌ها.
REQUEST_TIMEOUT: int = 15 # حداکثر زمان برای درخواست‌های HTTP
TCP_CONNECT_TIMEOUT: int = 5  # تایم‌اوت برای تست‌های کامل TCP اتصال (به میلی‌ثانیه)
NUM_TCP_TESTS: int = 11  # تعداد دفعات تست TCP برای هر کانفیگ در مرحله کامل
MIN_SUCCESSFUL_TESTS_RATIO: float = 0.7  # حداقل نسبت تست‌های موفق (70%) برای معتبر شمردن یک کانفیگ

QUICK_CHECK_TIMEOUT: int = 2  # تایم‌اوت برای تست اولیه سریع TCP (Fast Fail)

# محدودیت‌های تعداد کانفیگ‌ها در مراحل مختلف.
MAX_CONFIGS_TO_TEST: int = 100000 # حداکثر کانفیگ‌ها برای ورود به مرحله تست
FINAL_MAX_OUTPUT_CONFIGS: int = 600 # حداکثر تعداد بهترین کانفیگ‌ها که در نهایت ذخیره می‌شوند.

# الگوی Regex برای شناسایی و پارس کردن **تمام** کانفیگ‌های VLESS، بدون توجه به نوع security.
# فیلتر نهایی برای "tls" توسط SECURITY_KEYWORD انجام می‌شود.
VLESS_ANY_SECURITY_REGEX = re.compile(
    r"vless:\/\/"
    r"(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"  # UUID: شناسه‌ی منحصربه‌فرد کاربر
    r"@(?P<server>[a-zA-Z0-9.-]+)"  # Server Address: آدرس IP یا دامنه‌ی سرور
    r":(?P<port>\d+)"  # Port: پورت سرور
    r"\?security=(?P<security>[^&]+)"  # Security: هر مقداری را می‌پذیرد (Reality, TLS, و غیره).
    r"(?:&flow=(?P<flow>[^&]+))?"  # Optional Flow
    r"(?:&fp=(?P<fingerprint>[^&]+))?"  # Optional Fingerprint
    r"(?:&pbk=(?P<publicKey>[^&]+))?"  # Optional PublicKey (برای Reality)
    r"(?:&sni=(?P<sni>[^&]+))?"  # Optional SNI (Server Name Indication)
    r"(?:&sid=(?P<sessionId>[^&]+))?"  # Optional Session ID (برای Reality)
    r"(?:&type=(?P<type>[^&]+))?"  # Optional Type (مانند grpc, ws)
    r"(?:&encryption=(?P<encryption>[^&]+))?"  # Optional Encryption
    r"(?:&host=(?P<host>[^&]+))?"  # Optional Host (برای WebSocket)
    r"(?:&path=(?P<path>[^&]+))?"  # Optional Path (برای WebSocket و gRPC)
    r"(?:&serviceName=(?P<serviceName>[^&]+))?"  # Optional Service Name (برای gRPC)
    r"(?:&mode=(?P<mode>[^&]+))?"  # Optional Mode (برای gRPC)
    r"(?:&alpn=(?P<alpn>[^&]+))?"  # Optional ALPN
    r"#(?P<name>[^ ]+)"  # Name: نام کانفیگ که در انتهای لینک می‌آید
)

# کلیدواژه‌های امنیتی برای فیلتر کردن کانفیگ‌ها. فقط "tls" مجاز است.
SECURITY_KEYWORD: str = "tls"

# مجموعه‌ای برای ذخیره شناسه‌های یکتا (سرور، پورت، UUID) برای جلوگیری از اضافه شدن کانفیگ‌های تکراری.
SEEN_IDENTIFIERS: Set[Tuple[str, int, str]] = set()

# --- توابع کمکی (Helper Functions) ---

def safe_print(message: str) -> None:
    """پیامی را به صورت ایمن و با استفاده از قفل (Lock) چاپ می‌کند تا از تداخل خروجی تردها جلوگیری شود."""
    with PRINT_LOCK:
        print(message)

def print_progress(iteration: int, total: int, prefix: str = '', suffix: str = '', bar_length: int = 50) -> None:
    """
    نمایش نوار پیشرفت در کنسول.
    @param iteration: تکرار فعلی (عدد صحیح)
    @param total: کل تکرارها (عدد صحیح)
    @param prefix: پیشوند متنی (رشته)
    @param suffix: پسوند متنی (رشته)
    @param bar_length: طول نوار پیشرفت (عدد صحیح)
    """
    with PRINT_LOCK:
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
        sys.stdout.flush()
        if iteration == total:
            sys.stdout.write('\n')


def is_base64_content(s: str) -> bool:
    """بررسی می‌کند که آیا یک رشته، یک محتوای معتبر Base64 است یا خیر."""
    if not isinstance(s, str) or not s:
        return False
    # این Regex بررسی می‌کند که رشته فقط شامل کاراکترهای مجاز Base64 باشد.
    if not re.fullmatch(r"^[A-Za-z0-9+/=\s]*$", s.strip()):
        return False
    try:
        # پدگذاری (Padding) لازم برای دیکد Base64 را اضافه می‌کند.
        padded_s = s.strip()
        missing_padding = len(padded_s) % 4
        if missing_padding:
            padded_s += '=' * (4 - missing_padding)
        base64.b64decode(padded_s)
        return True
    except (base64.binascii.Error, UnicodeDecodeError):
        return False

def parse_vless_config(vless_link: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    یک لینک کانفیگ VLESS را تجزیه و مؤلفه‌های آن را استخراج می‌کند.
    در صورت موفقیت، یک دیکشنری از مؤلفه‌ها را برمی‌گرداند؛ در غیر این صورت None.
    این تابع از Regex عمومی استفاده می‌کند که هر نوع security را می‌پذیرد.
    """
    # ✅ تغییر اینجا: استفاده از VLESS_ANY_SECURITY_REGEX برای پارس کردن تمام VLESSها
    match = VLESS_ANY_SECURITY_REGEX.match(vless_link)
    if not match:
        return None # اگر با الگوی Regex مطابقت نداشت (یعنی فرمت VLESS نبود)، None برمی‌گرداند.

    try:
        data = match.groupdict() # استخراج گروه‌های نام‌گذاری شده از Regex
        data['port'] = int(data['port']) # تبدیل پورت به عدد صحیح
        data['original_config'] = vless_link # نگهداری لینک اصلی
        return data
    except (ValueError, TypeError) as e:
        safe_print(f"⚠️ خطای پارس کردن لینک VLESS '{vless_link}': {e}")
        return None

# --- توابع اصلی جمع‌آوری (Core Fetching Functions) ---

def fetch_subscription_content(url: str) -> Optional[str]:
    """محتوا را از یک URL مشخص با منطق تلاش مجدد (retry) دریافت می‌کند."""
    retries = 1 # تعداد تلاش‌ها
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status() # بررسی می‌کند که آیا درخواست موفق بوده (کد وضعیت 200)
            return response.text.strip()
        except requests.RequestException:
            pass # در صورت بروز خطا، تلاش بعدی انجام می‌شود.
    return None

def process_subscription_content(content: str, source_url: str) -> List[Dict[str, Union[str, int]]]:
    """
    محتوای سابسکریپشن را پردازش می‌کند، در صورت لزوم Base64 را دیکد کرده و کانفیگ‌های یکتای VLESS را استخراج می‌کند.
    """
    if not content:
        return []

    # اگر محتوا Base64 بود، آن را دیکد می‌کند.
    if is_base64_content(content) or (re.fullmatch(r"^[A-Za-z0-9+/=\s]*$", content.strip()) and len(content) > 50):
        try:
            padded_content = content.strip()
            missing_padding = len(padded_content) % 4
            if missing_padding:
                padded_content += '=' * (4 - missing_padding)
            content = base64.b64decode(padded_content).decode('utf-8')
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            safe_print(f"⚠️ خطای دیکد Base64 برای {source_url}: {e} (محتوا: {content[:50]}...)")
            return []

    valid_configs: List[Dict[str, Union[str, int]]] = []
    for line in content.splitlines():
        line = line.strip()
        # فیلتر اولیه بر اساس شروع با "vless://" و طول کافی.
        # کلمه کلیدی SECURITY_KEYWORD اینجا در خط چک نمی‌شود تا همه انواع امنیتی بررسی شوند.
        if line.startswith("vless://") and len(line) > 50:
            parsed_data = parse_vless_config(line) # تلاش برای پارس کردن لینک

            # ✅ فیلتر نهایی: اگر پارس با موفقیت انجام شد و security آن دقیقاً "tls" بود:
            if parsed_data and parsed_data.get('security') == SECURITY_KEYWORD:
                identifier: Tuple[str, int, str] = (
                    str(parsed_data["server"]),
                    int(parsed_data["port"]),
                    str(parsed_data["uuid"])
                )

                # جلوگیری از اضافه شدن کانفیگ‌های تکراری
                if identifier not in SEEN_IDENTIFIERS:
                    SEEN_IDENTIFIERS.add(identifier)
                    valid_configs.append(parsed_data)
    return valid_configs

def gather_configurations(links: List[str]) -> List[Dict[str, Union[str, int]]]:
    """کانفیگ‌های یکتای VLESS را از لیستی از لینک‌های سابسکریپشن جمع‌آوری می‌کند."""
    safe_print("🚀 مرحله ۱/۳: در حال دریافت و پردازش کانفیگ‌ها از منابع...")
    all_configs: List[Dict[str, Union[str, int]]] = []

    total_links = len(links)
    # استفاده از ThreadPoolExecutor برای اجرای موازی درخواست‌های HTTP و پردازش
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_subscription_content, url): url for url in links}

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            url = futures[future]
            content = future.result()
            if content:
                configs = process_subscription_content(content, url)
                all_configs.extend(configs)

            print_progress(i + 1, total_links, prefix='پیشرفت دریافت و پردازش:', suffix='تکمیل شد')

    safe_print(f"\n✨ مجموع کانفیگ‌های یکتا (بر اساس سرور، پورت، UUID) جمع‌آوری شده: {len(all_configs)}")
    return all_configs

# --- توابع تست کیفیت (Quality Testing Functions) ---

def test_tcp_latency(host: str, port: int, timeout: int) -> Optional[float]:
    """یک اتصال TCP به host:port را تست کرده و در صورت موفقیت، تاخیر را بر حسب میلی‌ثانیه برمی‌گرداند."""
    start_time = time.perf_counter()
    try:
        # ایجاد اتصال سوکت TCP
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start_time) * 1000 # محاسبه تاخیر بر حسب میلی‌ثانیه
    except Exception:
        return None # در صورت خطا، None برمی‌گرداند.

def quick_tcp_check(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int]]]:
    """یک بررسی سریع TCP انجام می‌دهد. در صورت موفقیت، کانفیگ را برمی‌گرداند؛ در غیر این صورت None."""
    host = str(config.get('server', ''))
    port = int(config.get('port', 0))
    if not host or not port:
        return None

    if test_tcp_latency(host, port, QUICK_CHECK_TIMEOUT) is not None:
        return config # اگر تست سریع موفق بود، کانفیگ را برای مرحله بعد برمی‌گرداند.
    return None

def measure_quality_metrics(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    میانگین تاخیر (latency) و جیتر (jitter) را برای یک کانفیگ مشخص با انجام چندین تست TCP اندازه‌گیری می‌کند.
    داده‌های پرت (outlier) قبل از محاسبه معیارها حذف می‌شوند.
    در صورت وجود تعداد کافی از تست‌های موفق، کانفیگ را با 'latency_ms' و 'jitter_ms' برمی‌گرداند؛ در غیر این صورت None.
    """
    host = str(config.get('server', ''))
    port = int(config.get('port', 0))
    if not host or not port:
        return None

    latencies: List[float] = []
    for _ in range(NUM_TCP_TESTS):
        latency = test_tcp_latency(host, port, TCP_CONNECT_TIMEOUT)
        if latency is not None:
            latencies.append(latency)
        time.sleep(0.1 + random.random() * 0.1) # یک مکث تصادفی کوچک برای شبیه‌سازی ترافیک واقعی‌تر

    # اگر تعداد تست‌های موفق کمتر از حداقل نسبت مورد نیاز بود، None برمی‌گرداند.
    if len(latencies) < (NUM_TCP_TESTS * MIN_SUCCESSFUL_TESTS_RATIO):
        return None

    latencies.sort()
    # حذف 10% داده‌های پرت از هر طرف (بالا و پایین) برای افزایش دقت میانگین.
    num_outliers_to_remove = int(len(latencies) * 0.1)
    if len(latencies) > 2 * num_outliers_to_remove: # اطمینان از اینکه بعد از حذف، حداقل چند داده باقی بماند.
        trimmed_latencies = latencies[num_outliers_to_remove : len(latencies) - num_outliers_to_remove]
    else:
        trimmed_latencies = latencies

    if not trimmed_latencies:
        return None

    avg_latency = statistics.mean(trimmed_latencies) # محاسبه میانگین تاخیر

    jitter = 0.0
    if len(trimmed_latencies) > 1:
        # محاسبه میانگین اختلاف بین تاخیرهای متوالی برای تعیین جیتر.
        differences = [abs(trimmed_latencies[i] - trimmed_latencies[i-1]) for i in range(1, len(trimmed_latencies))]
        if differences:
            jitter = statistics.mean(differences)

    config_with_quality = config.copy()
    config_with_quality['latency_ms'] = avg_latency
    config_with_quality['jitter_ms'] = jitter
    return config_with_quality

def evaluate_and_sort_configs(configs: List[Dict[str, Union[str, int]]]) -> List[Dict[str, Union[str, int, float]]]:
    """
    کیفیت اتصال (تاخیر و جیتر) را برای زیرمجموعه‌ای از کانفیگ‌ها با استفاده از فرآیند دو مرحله‌ای (بررسی سریع و سپس ارزیابی دقیق) ارزیابی می‌کند.
    کانفیگ‌ها را بر اساس کیفیت (ابتدا جیتر، سپس تاخیر) مرتب شده برمی‌گرداند.
    """
    safe_print("\n🔍 مرحله ۲/۳: انجام تست سریع TCP (Fast Fail) برای کانفیگ‌ها...")

    configs_to_process = configs[:MAX_CONFIGS_TO_TEST] # فقط تعداد محدودی از کانفیگ‌ها را تست می‌کند.
    passed_quick_check_configs: List[Dict[str, Union[str, int]]] = []

    # تعیین حداکثر تعداد ورکرها برای اجرای موازی، بر اساس تعداد هسته‌های CPU.
    max_concurrent_workers = min(32, (os.cpu_count() or 1) * 2 + 4)

    total_quick_checks = len(configs_to_process)
    if total_quick_checks == 0:
        safe_print("\n❌ هیچ کانفیگی برای تست سریع یافت نشد.")
        return []

    quick_checked_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor:
        futures = {
            executor.submit(quick_tcp_check, cfg): cfg # ارسال هر کانفیگ برای تست سریع به یک ترد جدا
            for cfg in configs_to_process
        }

        for future in concurrent.futures.as_completed(futures): # منتظر نتایج تست‌ها می‌ماند
            result_config = future.result()

            if result_config:
                passed_quick_check_configs.append(result_config)

            quick_checked_count += 1
            print_progress(quick_checked_count, total_quick_checks, prefix='پیشرفت تست سریع:', suffix='تکمیل شد')

    safe_print(f"\n✅ {len(passed_quick_check_configs)} کانفیگ تست سریع را با موفقیت گذراندند.")
    if not passed_quick_check_configs:
        return []

    safe_print("\n🔍 مرحله ۳/۳: انجام تست کیفیت کامل (TCP Ping & Jitter) برای کانفیگ‌های سالم...")
    evaluated_configs_with_quality: List[Dict[str, Union[str, int, float]]] = []

    total_full_checks = len(passed_quick_check_configs)
    full_checked_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor:
        futures = {
            executor.submit(measure_quality_metrics, cfg): cfg # ارسال کانفیگ‌های موفق برای تست کیفیت کامل
            for cfg in passed_quick_check_configs
        }

        for future in concurrent.futures.as_completed(futures):
            result_config = future.result()

            if result_config:
                evaluated_configs_with_quality.append(result_config)

            full_checked_count += 1
            print_progress(full_checked_count, total_full_checks, prefix='پیشرفت تست کامل:', suffix='تکمیل شد')

    safe_print(f"\n✅ {len(evaluated_configs_with_quality)} کانفیگ تست کیفیت کامل را با موفقیت گذراندند.")

    # مرتب‌سازی نهایی کانفیگ‌ها: ابتدا بر اساس جیتر (کمتر بهتر است)، سپس بر اساس تاخیر (کمتر بهتر است).
    evaluated_configs_with_quality.sort(key=lambda x: (x.get('jitter_ms', float('inf')), x.get('latency_ms', float('inf'))))

    return evaluated_configs_with_quality

def save_results_base64(configs: List[Dict[str, Union[str, int, float]]]) -> None:
    """کانفیگ‌های برتر (مرتب شده بر اساس کیفیت) را در یک فایل Base64 کدگذاری شده ذخیره می‌کند."""
    if not configs:
        safe_print("\n😥 هیچ کانفیگ فعالی برای ذخیره یافت نشد.")
        return

    top_configs = configs[:FINAL_MAX_OUTPUT_CONFIGS] # انتخاب تعداد مشخصی از بهترین کانفیگ‌ها

    final_configs_list: List[str] = []
    for i, cfg in enumerate(top_configs, start=1):
        original_link = str(cfg.get('original_config', ''))
        # حذف هرگونه کامنت (مثلاً #نام_کانفیگ) از لینک اصلی
        config_without_comment = re.sub(r'#.*$', '', original_link).strip()
        # اضافه کردن یک شماره منحصر به فرد به عنوان نام به انتهای هر کانفیگ
        numbered_config = f"{config_without_comment}#{i}"
        final_configs_list.append(numbered_config)

    subscription_text: str = "\n".join(final_configs_list) # ترکیب تمام کانفیگ‌ها به یک رشته بزرگ

    # انکد کردن کل متن سابسکریپشن به Base64 و حذف کاراکترهای پدگذاری '='
    base64_sub: str = base64.b64encode(subscription_text.encode('utf-8')).decode('utf-8').replace('=', '')

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True) # ایجاد دایرکتوری خروجی اگر وجود نداشته باشد.
    except OSError as e:
        safe_print(f"❌ خطا در ایجاد دایرکتوری خروجی {OUTPUT_DIR}: {e}")
        return

    output_path: str = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME) # مسیر کامل فایل خروجی

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(base64_sub) # نوشتن محتوای Base64 در فایل
        safe_print(f"\n🎉 {len(top_configs)} کانفیگ با شماره‌گذاری یکتا در قالب سابسکریپشن Base64 ذخیره شد: {output_path}")

        safe_print(f"🏆 5 کانفیگ برتر (فقط برای نمایش در لاگ):")
        # چاپ اطلاعات 5 کانفیگ برتر در کنسول برای اطلاع‌رسانی
        for i, cfg in enumerate(top_configs[:5], start=1):
            server = cfg.get('server', 'N/A')
            port = cfg.get('port', 'N/A')
            latency = cfg.get('latency_ms', float('inf'))
            jitter = cfg.get('jitter_ms', float('inf'))
            safe_print(
                f"  {i}. {server}:{port} - "
                f"تاخیر: {latency:.2f}ms, "
                f"جیتر: {jitter:.2f}ms"
            )
    except IOError as e:
        safe_print(f"❌ خطا در ذخیره فایل به {output_path}: {e}")

# --- نقطه ورود اصلی برنامه (Main Entry Point) ---

def main() -> None:
    """تابع اصلی برای هماهنگی فرآیند جمع‌آوری، تست و ذخیره کانفیگ‌های VLESS TLS."""
    start_time = time.time() # شروع زمان‌سنجی کلی اجرا

    # مرحله ۱: جمع‌آوری کانفیگ‌ها
    all_unique_configs = gather_configurations(CONFIG_URLS)

    # مرحله ۲ و ۳: ارزیابی و مرتب‌سازی کانفیگ‌ها
    evaluated_and_sorted_configs = evaluate_and_sort_configs(all_unique_configs)

    # مرحله ۴: ذخیره نتایج
    if evaluated_and_sorted_configs:
        save_results_base64(evaluated_and_sorted_configs)
    else:
        safe_print("\n🚫 هیچ کانفیگ فعالی برای ارزیابی و ذخیره یافت نشد.")

    elapsed = time.time() - start_time # محاسبه زمان کل اجرا
    safe_print(f"\n⏱️ کل زمان اجرا: {elapsed:.2f} ثانیه")

if __name__ == "__main__":
    main() # اجرای تابع اصلی در زمان اجرای اسکریپت
# -- coding: utf-8 --

import requests
import os
import re
import base64
import threading
import concurrent.futures
import socket
import time
import random
import statistics
import sys
from typing import List, Dict, Tuple, Optional, Set, Union

# --- Global Constants & Variables ---

PRINT_LOCK = threading.Lock() # برای جلوگیری از تداخل در چاپ خروجی هنگام استفاده از تردها

# مسیر دایرکتوری خروجی: تنظیم شده روی "data"
OUTPUT_DIR = "data"

# لیست URLهای سابسکریپشن که کانفیگ‌ها از آن‌ها جمع‌آوری می‌شوند.
CONFIG_URLS: List[str] = [
    "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/refs/heads/main/sub/protocols/vless.txt",
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt",
    "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Vless.txt",
    "https://www.v2nodes.com/subscriptions/country/all/?key=F225BC16D80D287",
    "https://raw.githubusercontent.com/Awmiroosen/awmirx-v2ray/refs/heads/main/blob/main/v2-sub.txt",
    "https://raw.githubusercontent.com/gfpcom/free-proxy-list/refs/heads/main/list/vless.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/22.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt",
    "https://raw.githubusercontent.com/MRT-project/v2ray-configs/refs/heads/main/AllConfigsSub.txt",
    "https://raw.githubusercontent.com/Kolandone/v2raycollector/refs/heads/main/vless.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/vless",
    "https://raw.githubusercontent.com/xyfqzy/free-nodes/refs/heads/main/nodes/vless.txt",
    "https://raw.githubusercontent.com/MAHDI-F-KHEDMAT/KHANEVADEGI/refs/heads/main/data/khanevadeh_base64.txt",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/vless.html",
    "https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/refs/heads/main/config.txt",
]

# نام فایل خروجی برای ذخیره کانفیگ‌های نهایی.
# تنظیم شده روی "KHANEVADEH_TLS_base64.txt"
OUTPUT_FILENAME: str = os.getenv("TLS_OUTPUT_FILENAME", "KHANEVADEH_TLS") + "_base64.txt"

# زمان‌بندی‌ها و تعداد تست‌ها برای ارزیابی کیفیت کانفیگ‌ها.
REQUEST_TIMEOUT: int = 15 # حداکثر زمان برای درخواست‌های HTTP
TCP_CONNECT_TIMEOUT: int = 5  # تایم‌اوت برای تست‌های کامل TCP اتصال (به میلی‌ثانیه)
NUM_TCP_TESTS: int = 11  # تعداد دفعات تست TCP برای هر کانفیگ در مرحله کامل
MIN_SUCCESSFUL_TESTS_RATIO: float = 0.7  # حداقل نسبت تست‌های موفق (70%) برای معتبر شمردن یک کانفیگ

QUICK_CHECK_TIMEOUT: int = 2  # تایم‌اوت برای تست اولیه سریع TCP (Fast Fail)

# محدودیت‌های تعداد کانفیگ‌ها در مراحل مختلف.
MAX_CONFIGS_TO_TEST: int = 100000 # حداکثر کانفیگ‌ها برای ورود به مرحله تست
FINAL_MAX_OUTPUT_CONFIGS: int = 600 # حداکثر تعداد بهترین کانفیگ‌ها که در نهایت ذخیره می‌شوند.

# الگوی Regex برای شناسایی و پارس کردن **تمام** کانفیگ‌های VLESS، بدون توجه به نوع security.
# فیلتر نهایی برای "tls" توسط SECURITY_KEYWORD انجام می‌شود.
VLESS_ANY_SECURITY_REGEX = re.compile(
    r"vless:\/\/"
    r"(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"  # UUID: شناسه‌ی منحصربه‌فرد کاربر
    r"@(?P<server>[a-zA-Z0-9.-]+)"  # Server Address: آدرس IP یا دامنه‌ی سرور
    r":(?P<port>\d+)"  # Port: پورت سرور
    r"\?security=(?P<security>[^&]+)"  # Security: هر مقداری را می‌پذیرد (Reality, TLS, و غیره).
    r"(?:&flow=(?P<flow>[^&]+))?"  # Optional Flow
    r"(?:&fp=(?P<fingerprint>[^&]+))?"  # Optional Fingerprint
    r"(?:&pbk=(?P<publicKey>[^&]+))?"  # Optional PublicKey (برای Reality)
    r"(?:&sni=(?P<sni>[^&]+))?"  # Optional SNI (Server Name Indication)
    r"(?:&sid=(?P<sessionId>[^&]+))?"  # Optional Session ID (برای Reality)
    r"(?:&type=(?P<type>[^&]+))?"  # Optional Type (مانند grpc, ws)
    r"(?:&encryption=(?P<encryption>[^&]+))?"  # Optional Encryption
    r"(?:&host=(?P<host>[^&]+))?"  # Optional Host (برای WebSocket)
    r"(?:&path=(?P<path>[^&]+))?"  # Optional Path (برای WebSocket و gRPC)
    r"(?:&serviceName=(?P<serviceName>[^&]+))?"  # Optional Service Name (برای gRPC)
    r"(?:&mode=(?P<mode>[^&]+))?"  # Optional Mode (برای gRPC)
    r"(?:&alpn=(?P<alpn>[^&]+))?"  # Optional ALPN
    r"#(?P<name>[^ ]+)"  # Name: نام کانفیگ که در انتهای لینک می‌آید
)

# کلیدواژه‌های امنیتی برای فیلتر کردن کانفیگ‌ها. فقط "tls" مجاز است.
SECURITY_KEYWORD: str = "tls"

# مجموعه‌ای برای ذخیره شناسه‌های یکتا (سرور، پورت، UUID) برای جلوگیری از اضافه شدن کانفیگ‌های تکراری.
SEEN_IDENTIFIERS: Set[Tuple[str, int, str]] = set()

# --- توابع کمکی (Helper Functions) ---

def safe_print(message: str) -> None:
    """پیامی را به صورت ایمن و با استفاده از قفل (Lock) چاپ می‌کند تا از تداخل خروجی تردها جلوگیری شود."""
    with PRINT_LOCK:
        print(message)

def print_progress(iteration: int, total: int, prefix: str = '', suffix: str = '', bar_length: int = 50) -> None:
    """
    نمایش نوار پیشرفت در کنسول.
    @param iteration: تکرار فعلی (عدد صحیح)
    @param total: کل تکرارها (عدد صحیح)
    @param prefix: پیشوند متنی (رشته)
    @param suffix: پسوند متنی (رشته)
    @param bar_length: طول نوار پیشرفت (عدد صحیح)
    """
    with PRINT_LOCK:
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
        sys.stdout.flush()
        if iteration == total:
            sys.stdout.write('\n')


def is_base64_content(s: str) -> bool:
    """بررسی می‌کند که آیا یک رشته، یک محتوای معتبر Base64 است یا خیر."""
    if not isinstance(s, str) or not s:
        return False
    # این Regex بررسی می‌کند که رشته فقط شامل کاراکترهای مجاز Base64 باشد.
    if not re.fullmatch(r"^[A-Za-z0-9+/=\s]*$", s.strip()):
        return False
    try:
        # پدگذاری (Padding) لازم برای دیکد Base64 را اضافه می‌کند.
        padded_s = s.strip()
        missing_padding = len(padded_s) % 4
        if missing_padding:
            padded_s += '=' * (4 - missing_padding)
        base64.b64decode(padded_s)
        return True
    except (base64.binascii.Error, UnicodeDecodeError):
        return False

def parse_vless_config(vless_link: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    یک لینک کانفیگ VLESS را تجزیه و مؤلفه‌های آن را استخراج می‌کند.
    در صورت موفقیت، یک دیکشنری از مؤلفه‌ها را برمی‌گرداند؛ در غیر این صورت None.
    این تابع از Regex عمومی استفاده می‌کند که هر نوع security را می‌پذیرد.
    """
    # ✅ تغییر اینجا: استفاده از VLESS_ANY_SECURITY_REGEX برای پارس کردن تمام VLESSها
    match = VLESS_ANY_SECURITY_REGEX.match(vless_link)
    if not match:
        return None # اگر با الگوی Regex مطابقت نداشت (یعنی فرمت VLESS نبود)، None برمی‌گرداند.

    try:
        data = match.groupdict() # استخراج گروه‌های نام‌گذاری شده از Regex
        data['port'] = int(data['port']) # تبدیل پورت به عدد صحیح
        data['original_config'] = vless_link # نگهداری لینک اصلی
        return data
    except (ValueError, TypeError) as e:
        safe_print(f"⚠️ خطای پارس کردن لینک VLESS '{vless_link}': {e}")
        return None

# --- توابع اصلی جمع‌آوری (Core Fetching Functions) ---

def fetch_subscription_content(url: str) -> Optional[str]:
    """محتوا را از یک URL مشخص با منطق تلاش مجدد (retry) دریافت می‌کند."""
    retries = 1 # تعداد تلاش‌ها
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status() # بررسی می‌کند که آیا درخواست موفق بوده (کد وضعیت 200)
            return response.text.strip()
        except requests.RequestException:
            pass # در صورت بروز خطا، تلاش بعدی انجام می‌شود.
    return None

def process_subscription_content(content: str, source_url: str) -> List[Dict[str, Union[str, int]]]:
    """
    محتوای سابسکریپشن را پردازش می‌کند، در صورت لزوم Base64 را دیکد کرده و کانفیگ‌های یکتای VLESS را استخراج می‌کند.
    """
    if not content:
        return []

    # اگر محتوا Base64 بود، آن را دیکد می‌کند.
    if is_base64_content(content) or (re.fullmatch(r"^[A-Za-z0-9+/=\s]*$", content.strip()) and len(content) > 50):
        try:
            padded_content = content.strip()
            missing_padding = len(padded_content) % 4
            if missing_padding:
                padded_content += '=' * (4 - missing_padding)
            content = base64.b64decode(padded_content).decode('utf-8')
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            safe_print(f"⚠️ خطای دیکد Base64 برای {source_url}: {e} (محتوا: {content[:50]}...)")
            return []

    valid_configs: List[Dict[str, Union[str, int]]] = []
    for line in content.splitlines():
        line = line.strip()
        # فیلتر اولیه بر اساس شروع با "vless://" و طول کافی.
        # کلمه کلیدی SECURITY_KEYWORD اینجا در خط چک نمی‌شود تا همه انواع امنیتی بررسی شوند.
        if line.startswith("vless://") and len(line) > 50:
            parsed_data = parse_vless_config(line) # تلاش برای پارس کردن لینک

            # ✅ فیلتر نهایی: اگر پارس با موفقیت انجام شد و security آن دقیقاً "tls" بود:
            if parsed_data and parsed_data.get('security') == SECURITY_KEYWORD:
                identifier: Tuple[str, int, str] = (
                    str(parsed_data["server"]),
                    int(parsed_data["port"]),
                    str(parsed_data["uuid"])
                )

                # جلوگیری از اضافه شدن کانفیگ‌های تکراری
                if identifier not in SEEN_IDENTIFIERS:
                    SEEN_IDENTIFIERS.add(identifier)
                    valid_configs.append(parsed_data)
    return valid_configs

def gather_configurations(links: List[str]) -> List[Dict[str, Union[str, int]]]:
    """کانفیگ‌های یکتای VLESS را از لیستی از لینک‌های سابسکریپشن جمع‌آوری می‌کند."""
    safe_print("🚀 مرحله ۱/۳: در حال دریافت و پردازش کانفیگ‌ها از منابع...")
    all_configs: List[Dict[str, Union[str, int]]] = []

    total_links = len(links)
    # استفاده از ThreadPoolExecutor برای اجرای موازی درخواست‌های HTTP و پردازش
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_subscription_content, url): url for url in links}

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            url = futures[future]
            content = future.result()
            if content:
                configs = process_subscription_content(content, url)
                all_configs.extend(configs)

            print_progress(i + 1, total_links, prefix='پیشرفت دریافت و پردازش:', suffix='تکمیل شد')

    safe_print(f"\n✨ مجموع کانفیگ‌های یکتا (بر اساس سرور، پورت، UUID) جمع‌آوری شده: {len(all_configs)}")
    return all_configs

# --- توابع تست کیفیت (Quality Testing Functions) ---

def test_tcp_latency(host: str, port: int, timeout: int) -> Optional[float]:
    """یک اتصال TCP به host:port را تست کرده و در صورت موفقیت، تاخیر را بر حسب میلی‌ثانیه برمی‌گرداند."""
    start_time = time.perf_counter()
    try:
        # ایجاد اتصال سوکت TCP
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start_time) * 1000 # محاسبه تاخیر بر حسب میلی‌ثانیه
    except Exception:
        return None # در صورت خطا، None برمی‌گرداند.

def quick_tcp_check(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int]]]:
    """یک بررسی سریع TCP انجام می‌دهد. در صورت موفقیت، کانفیگ را برمی‌گرداند؛ در غیر این صورت None."""
    host = str(config.get('server', ''))
    port = int(config.get('port', 0))
    if not host or not port:
        return None

    if test_tcp_latency(host, port, QUICK_CHECK_TIMEOUT) is not None:
        return config # اگر تست سریع موفق بود، کانفیگ را برای مرحله بعد برمی‌گرداند.
    return None

def measure_quality_metrics(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    میانگین تاخیر (latency) و جیتر (jitter) را برای یک کانفیگ مشخص با انجام چندین تست TCP اندازه‌گیری می‌کند.
    داده‌های پرت (outlier) قبل از محاسبه معیارها حذف می‌شوند.
    در صورت وجود تعداد کافی از تست‌های موفق، کانفیگ را با 'latency_ms' و 'jitter_ms' برمی‌گرداند؛ در غیر این صورت None.
    """
    host = str(config.get('server', ''))
    port = int(config.get('port', 0))
    if not host or not port:
        return None

    latencies: List[float] = []
    for _ in range(NUM_TCP_TESTS):
        latency = test_tcp_latency(host, port, TCP_CONNECT_TIMEOUT)
        if latency is not None:
            latencies.append(latency)
        time.sleep(0.1 + random.random() * 0.1) # یک مکث تصادفی کوچک برای شبیه‌سازی ترافیک واقعی‌تر

    # اگر تعداد تست‌های موفق کمتر از حداقل نسبت مورد نیاز بود، None برمی‌گرداند.
    if len(latencies) < (NUM_TCP_TESTS * MIN_SUCCESSFUL_TESTS_RATIO):
        return None

    latencies.sort()
    # حذف 10% داده‌های پرت از هر طرف (بالا و پایین) برای افزایش دقت میانگین.
    num_outliers_to_remove = int(len(latencies) * 0.1)
    if len(latencies) > 2 * num_outliers_to_remove: # اطمینان از اینکه بعد از حذف، حداقل چند داده باقی بماند.
        trimmed_latencies = latencies[num_outliers_to_remove : len(latencies) - num_outliers_to_remove]
    else:
        trimmed_latencies = latencies

    if not trimmed_latencies:
        return None

    avg_latency = statistics.mean(trimmed_latencies) # محاسبه میانگین تاخیر

    jitter = 0.0
    if len(trimmed_latencies) > 1:
        # محاسبه میانگین اختلاف بین تاخیرهای متوالی برای تعیین جیتر.
        differences = [abs(trimmed_latencies[i] - trimmed_latencies[i-1]) for i in range(1, len(trimmed_latencies))]
        if differences:
            jitter = statistics.mean(differences)

    config_with_quality = config.copy()
    config_with_quality['latency_ms'] = avg_latency
    config_with_quality['jitter_ms'] = jitter
    return config_with_quality

def evaluate_and_sort_configs(configs: List[Dict[str, Union[str, int]]]) -> List[Dict[str, Union[str, int, float]]]:
    """
    کیفیت اتصال (تاخیر و جیتر) را برای زیرمجموعه‌ای از کانفیگ‌ها با استفاده از فرآیند دو مرحله‌ای (بررسی سریع و سپس ارزیابی دقیق) ارزیابی می‌کند.
    کانفیگ‌ها را بر اساس کیفیت (ابتدا جیتر، سپس تاخیر) مرتب شده برمی‌گرداند.
    """
    safe_print("\n🔍 مرحله ۲/۳: انجام تست سریع TCP (Fast Fail) برای کانفیگ‌ها...")

    configs_to_process = configs[:MAX_CONFIGS_TO_TEST] # فقط تعداد محدودی از کانفیگ‌ها را تست می‌کند.
    passed_quick_check_configs: List[Dict[str, Union[str, int]]] = []

    # تعیین حداکثر تعداد ورکرها برای اجرای موازی، بر اساس تعداد هسته‌های CPU.
    max_concurrent_workers = min(32, (os.cpu_count() or 1) * 2 + 4)

    total_quick_checks = len(configs_to_process)
    if total_quick_checks == 0:
        safe_print("\n❌ هیچ کانفیگی برای تست سریع یافت نشد.")
        return []

    quick_checked_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor:
        futures = {
            executor.submit(quick_tcp_check, cfg): cfg # ارسال هر کانفیگ برای تست سریع به یک ترد جدا
            for cfg in configs_to_process
        }

        for future in concurrent.futures.as_completed(futures): # منتظر نتایج تست‌ها می‌ماند
            result_config = future.result()

            if result_config:
                passed_quick_check_configs.append(result_config)

            quick_checked_count += 1
            print_progress(quick_checked_count, total_quick_checks, prefix='پیشرفت تست سریع:', suffix='تکمیل شد')

    safe_print(f"\n✅ {len(passed_quick_check_configs)} کانفیگ تست سریع را با موفقیت گذراندند.")
    if not passed_quick_check_configs:
        return []

    safe_print("\n🔍 مرحله ۳/۳: انجام تست کیفیت کامل (TCP Ping & Jitter) برای کانفیگ‌های سالم...")
    evaluated_configs_with_quality: List[Dict[str, Union[str, int, float]]] = []

    total_full_checks = len(passed_quick_check_configs)
    full_checked_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor:
        futures = {
            executor.submit(measure_quality_metrics, cfg): cfg # ارسال کانفیگ‌های موفق برای تست کیفیت کامل
            for cfg in passed_quick_check_configs
        }

        for future in concurrent.futures.as_completed(futures):
            result_config = future.result()

            if result_config:
                evaluated_configs_with_quality.append(result_config)

            full_checked_count += 1
            print_progress(full_checked_count, total_full_checks, prefix='پیشرفت تست کامل:', suffix='تکمیل شد')

    safe_print(f"\n✅ {len(evaluated_configs_with_quality)} کانفیگ تست کیفیت کامل را با موفقیت گذراندند.")

    # مرتب‌سازی نهایی کانفیگ‌ها: ابتدا بر اساس جیتر (کمتر بهتر است)، سپس بر اساس تاخیر (کمتر بهتر است).
    evaluated_configs_with_quality.sort(key=lambda x: (x.get('jitter_ms', float('inf')), x.get('latency_ms', float('inf'))))

    return evaluated_configs_with_quality

def save_results_base64(configs: List[Dict[str, Union[str, int, float]]]) -> None:
    """کانفیگ‌های برتر (مرتب شده بر اساس کیفیت) را در یک فایل Base64 کدگذاری شده ذخیره می‌کند."""
    if not configs:
        safe_print("\n😥 هیچ کانفیگ فعالی برای ذخیره یافت نشد.")
        return

    top_configs = configs[:FINAL_MAX_OUTPUT_CONFIGS] # انتخاب تعداد مشخصی از بهترین کانفیگ‌ها

    final_configs_list: List[str] = []
    for i, cfg in enumerate(top_configs, start=1):
        original_link = str(cfg.get('original_config', ''))
        # حذف هرگونه کامنت (مثلاً #نام_کانفیگ) از لینک اصلی
        config_without_comment = re.sub(r'#.*$', '', original_link).strip()
        # اضافه کردن یک شماره منحصر به فرد به عنوان نام به انتهای هر کانفیگ
        numbered_config = f"{config_without_comment}#{i}"
        final_configs_list.append(numbered_config)

    subscription_text: str = "\n".join(final_configs_list) # ترکیب تمام کانفیگ‌ها به یک رشته بزرگ

    # انکد کردن کل متن سابسکریپشن به Base64 و حذف کاراکترهای پدگذاری '='
    base64_sub: str = base64.b64encode(subscription_text.encode('utf-8')).decode('utf-8').replace('=', '')

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True) # ایجاد دایرکتوری خروجی اگر وجود نداشته باشد.
    except OSError as e:
        safe_print(f"❌ خطا در ایجاد دایرکتوری خروجی {OUTPUT_DIR}: {e}")
        return

    output_path: str = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME) # مسیر کامل فایل خروجی

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(base64_sub) # نوشتن محتوای Base64 در فایل
        safe_print(f"\n🎉 {len(top_configs)} کانفیگ با شماره‌گذاری یکتا در قالب سابسکریپشن Base64 ذخیره شد: {output_path}")

        safe_print(f"🏆 5 کانفیگ برتر (فقط برای نمایش در لاگ):")
        # چاپ اطلاعات 5 کانفیگ برتر در کنسول برای اطلاع‌رسانی
        for i, cfg in enumerate(top_configs[:5], start=1):
            server = cfg.get('server', 'N/A')
            port = cfg.get('port', 'N/A')
            latency = cfg.get('latency_ms', float('inf'))
            jitter = cfg.get('jitter_ms', float('inf'))
            safe_print(
                f"  {i}. {server}:{port} - "
                f"تاخیر: {latency:.2f}ms, "
                f"جیتر: {jitter:.2f}ms"
            )
    except IOError as e:
        safe_print(f"❌ خطا در ذخیره فایل به {output_path}: {e}")

# --- نقطه ورود اصلی برنامه (Main Entry Point) ---

def main() -> None:
    """تابع اصلی برای هماهنگی فرآیند جمع‌آوری، تست و ذخیره کانفیگ‌های VLESS TLS."""
    start_time = time.time() # شروع زمان‌سنجی کلی اجرا

    # مرحله ۱: جمع‌آوری کانفیگ‌ها
    all_unique_configs = gather_configurations(CONFIG_URLS)

    # مرحله ۲ و ۳: ارزیابی و مرتب‌سازی کانفیگ‌ها
    evaluated_and_sorted_configs = evaluate_and_sort_configs(all_unique_configs)

    # مرحله ۴: ذخیره نتایج
    if evaluated_and_sorted_configs:
        save_results_base64(evaluated_and_sorted_configs)
    else:
        safe_print("\n🚫 هیچ کانفیگ فعالی برای ارزیابی و ذخیره یافت نشد.")

    elapsed = time.time() - start_time # محاسبه زمان کل اجرا
    safe_print(f"\n⏱️ کل زمان اجرا: {elapsed:.2f} ثانیه")

if __name__ == "__main__":
    main() # اجرای تابع اصلی در زمان اجرای اسکریپت
