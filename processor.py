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
import sys # برای چاپ نوار پیشرفت
from typing import List, Dict, Tuple, Optional, Set, Union 

# --- Global Constants & Variables ---

PRINT_LOCK = threading.Lock() 

# مسیر دایرکتوری خروجی: تنظیم شده روی "data"
OUTPUT_DIR = "data" 

# لیست URLهای سابسکریپشن
# اگر GitHub Pages را فعال کرده‌اید، می‌توانید لینک خود را اینجا اضافه کنید.
# مثال: "https://YOUR-USERNAME.github.io/KHANEVADEGI/data/khanevadeh_base64.txt"
CONFIG_URLS: List[str] = [
    "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/refs/heads/main/sub/protocols/vless.txt",
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt",
    "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Vless.txt",
    "https://www.v2nodes.com/subscriptions/country/all/?key=F225BC16D80D287",
    "https://raw.githubusercontent.com/T3stAcc/V2Ray/refs/heads/main/AllConfigsSub.txt", # این لینک به دلیل 404 یا مشکلات پارس شدن حذف یا کامنت شده است.
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

# نام فایل خروجی برای ذخیره کانفیگ‌های نهایی: تنظیم شده روی "khanevadeh_base64.txt"
OUTPUT_FILENAME: str = os.getenv("REALITY_OUTPUT_FILENAME", "khanevadeh") + "_base64.txt"

# زمان‌بندی‌ها و تعداد تست‌ها
REQUEST_TIMEOUT: int = 15 
TCP_CONNECT_TIMEOUT: int = 5 # تایم‌اوت برای تست‌های کامل TCP
NUM_TCP_TESTS: int = 11 # تعداد دفعات تست TCP برای مرحله کامل
MIN_SUCCESSFUL_TESTS_RATIO: float = 0.7 # حداقل درصد تست‌های موفق برای مرحله کامل

QUICK_CHECK_TIMEOUT: int = 2 # تایم‌اوت برای تست اولیه سریع (Fast Fail)

# محدودیت‌های تعداد کانفیگ‌ها
MAX_CONFIGS_TO_TEST: int = 100000 
FINAL_MAX_OUTPUT_CONFIGS: int = 600 

# الگوهای Regex برای شناسایی و پارس کردن کانفیگ‌ها
VLESS_REALITY_PATTERN: re.Pattern = re.compile(r'(vless://[^\s]+)', re.IGNORECASE)
SECURITY_KEYWORD: str = 'security=tls'  


# ✅ تغییر اول: نوع داده شناسه یکتا اصلاح شد تا فقط شامل سرور، پورت و uuid باشد
SEEN_IDENTIFIERS: Set[Tuple[str, int, str]] = set()

# --- توابع کمکی (Helper Functions) ---

def safe_print(message: str) -> None:
    """Prints a message safely using a lock to prevent mixed output from threads."""
    with threading.Lock(): 
        print(message)

def print_progress(iteration: int, total: int, prefix: str = '', suffix: str = '', bar_length: int = 50) -> None:
    """
    Call in a loop to create a progress bar in the console.
    @param iteration: current iteration (int)
    @param total: total iterations (int)
    @param prefix: string prefix (str)
    @param suffix: string suffix (str)
    @param bar_length: character length of bar (int)
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
    """Checks if a string is a valid base64 encoded string."""
    if not isinstance(s, str) or not s:
        return False
    if not re.fullmatch(r"^[A-Za-z0-9+/=\s]+$", s.strip()):
        return False
    try:
        base64.b64decode(s)
        return True
    except (base64.binascii.Error, UnicodeDecodeError):
        return False

# --- توابع اصلی جمع‌آوری (Core Fetching Functions) ---

def fetch_subscription_content(url: str) -> Optional[str]:
    """Fetches content from a given URL with retry logic."""
    retries = 1 
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status() 
            return response.text.strip()
        except requests.RequestException as e:
            pass # هیچ پیامی چاپ نمی‌شود، فقط خطا نادیده گرفته می‌شود.
    return None

def process_subscription_content(content: str, source_url: str) -> List[Dict[str, Union[str, int]]]:
    """Processes subscription content, decoding base64 if necessary and extracting unique VLESS configs."""
    if not content:
        return []
    
    if is_base64_content(content):
        try:
            content = base64.b64decode(content).decode('utf-8')
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            safe_print(f"⚠️ خطای دیکد Base64 برای {source_url}: {e}") 
            return []
    
    valid_configs: List[Dict[str, Union[str, int]]] = []
    for line in content.splitlines():
        line = line.strip()
        if SECURITY_KEYWORD in line and line.startswith("vless://"):
            parsed_data = parse_vless_config(line)
            
            if parsed_data:
                # ✅ تغییر دوم: شناسه یکتا برای هماهنگی با v2rayNG اصلاح شد
                identifier: Tuple[str, int, str] = (
                    parsed_data["server"], 
                    parsed_data["port"], 
                    parsed_data["uuid"]
                )
                
                if identifier not in SEEN_IDENTIFIERS:
                    SEEN_IDENTIFIERS.add(identifier)
                    valid_configs.append(parsed_data) 
    return valid_configs

def gather_configurations(links: List[str]) -> List[Dict[str, Union[str, int]]]:
    """Gathers unique VLESS configurations from a list of subscription links."""
    safe_print("🚀 مرحله ۱/۳: در حال دریافت و پردازش کانفیگ‌ها از منابع...")
    all_configs: List[Dict[str, Union[str, int]]] = []
    
    total_links = len(links)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_subscription_content, url): url for url in links}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            url = futures[future]
            content = future.result()
            if content:
                configs = process_subscription_content(content, url)
                all_configs.extend(configs)
            
            # اینجا فقط یک نوار پیشرفت کلی برای این مرحله نمایش داده می شود
            print_progress(i + 1, total_links, prefix='پیشرفت دریافت و پردازش:', suffix='تکمیل شد')
    
    safe_print(f"\n✨ مجموع کانفیگ‌های یکتا (بر اساس منطق v2rayNG) جمع‌آوری شده: {len(all_configs)}")
    return all_configs

# --- توابع تست کیفیت (Quality Testing Functions) ---

def test_tcp_latency(host: str, port: int, timeout: int) -> Optional[float]:
    """Tests a TCP connection to host:port and returns latency in ms if successful."""
    start_time = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start_time) * 1000 
    except Exception: 
        return None

def quick_tcp_check(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int]]]:
    """Performs a single, quick TCP check. Returns the config if successful, None otherwise."""
    host = str(config['server'])
    port = int(config['port'])
    if test_tcp_latency(host, port, QUICK_CHECK_TIMEOUT) is not None:
        return config
    return None

def measure_quality_metrics(config: Dict[str, Union[str, int]]) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    Measures average latency and jitter for a given config with multiple TCP tests.
    Performs outlier removal before calculating metrics.
    Returns config with 'latency_ms' and 'jitter_ms' if enough successful tests, otherwise None.
    """
    host = str(config['server'])
    port = int(config['port'])

    latencies: List[float] = []
    for _ in range(NUM_TCP_TESTS):
        latency = test_tcp_latency(host, port, TCP_CONNECT_TIMEOUT)
        if latency is not None:
            latencies.append(latency)
        time.sleep(0.1 + random.random() * 0.1) 

    if len(latencies) < (NUM_TCP_TESTS * MIN_SUCCESSFUL_TESTS_RATIO):
        return None 

    latencies.sort()
    num_outliers_to_remove = min(2, len(latencies) // 3) 
    
    if len(latencies) > 2 * num_outliers_to_remove: 
        trimmed_latencies = latencies[num_outliers_to_remove : len(latencies) - num_outliers_to_remove]
    else:
        trimmed_latencies = latencies 

    if not trimmed_latencies: 
        return None

    avg_latency = statistics.mean(trimmed_latencies) 
    
    jitter = 0.0
    if len(trimmed_latencies) > 1:
        differences = [abs(trimmed_latencies[i] - trimmed_latencies[i-1]) for i in range(1, len(trimmed_latencies))]
        if differences:
            jitter = statistics.mean(differences) 
        
    config_with_quality = config.copy()
    config_with_quality['latency_ms'] = avg_latency
    config_with_quality['jitter_ms'] = jitter
    return config_with_quality

def evaluate_and_sort_configs(configs: List[Dict[str, Union[str, int]]]) -> List[Dict[str, Union[str, int, float]]]:
    """
    Evaluates connection quality (latency and jitter) for a subset of configurations
    using a two-stage process (quick check then detailed evaluation).
    Returns them sorted by quality (Jitter primary, Latency secondary).
    """
    safe_print("\n🔍 مرحله ۲/۳: انجام تست سریع TCP (Fast Fail) برای کانفیگ‌ها...")
    
    configs_to_process = configs[:MAX_CONFIGS_TO_TEST]
    passed_quick_check_configs: List[Dict[str, Union[str, int]]] = []
    
    max_concurrent_workers = min(32, os.cpu_count() + 4 if os.cpu_count() else 4)

    # --- مرحله ۱: تست سریع ---
    total_quick_checks = len(configs_to_process)
    quick_checked_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor: 
        futures = {
            executor.submit(quick_tcp_check, cfg): cfg 
            for cfg in configs_to_process
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
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

    # --- مرحله ۲: تست کامل ---
    total_full_checks = len(passed_quick_check_configs)
    full_checked_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor: 
        futures = {
            executor.submit(measure_quality_metrics, cfg): cfg 
            for cfg in passed_quick_check_configs
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result_config = future.result()
            
            if result_config:
                evaluated_configs_with_quality.append(result_config)

            full_checked_count += 1
            print_progress(full_checked_count, total_full_checks, prefix='پیشرفت تست کامل:', suffix='تکمیل شد')
    
    safe_print(f"\n✅ {len(evaluated_configs_with_quality)} کانفیگ تست کیفیت کامل را با موفقیت گذراندند.")

    evaluated_configs_with_quality.sort(key=lambda x: (x['jitter_ms'], x['latency_ms']))
    
    return evaluated_configs_with_quality

def save_results_base64(configs: List[Dict[str, Union[str, int, float]]]) -> None:
    """Saves the top configurations (sorted by quality) into a base64 encoded file."""
    if not configs:
        safe_print("\n😥 هیچ کانفیگ فعالی برای ذخیره یافت نشد.")
        return
    
    top_configs = configs[:FINAL_MAX_OUTPUT_CONFIGS]
    
    final_configs_list: List[str] = []
    for i, cfg in enumerate(top_configs, start=1):
        config_without_comment = re.sub(r'#.*$', '', str(cfg['original_config'])).strip()
        
        # اضافه کردن تنها یک شماره یکتا به عنوان نام کانفیگ
        numbered_config = f"{config_without_comment}#{i}"
        
        final_configs_list.append(numbered_config)
    
    subscription_text: str = "\n".join(final_configs_list)
    
    base64_sub: str = base64.b64encode(subscription_text.encode('utf-8')).decode('utf-8').replace('=', '')
    
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except OSError as e:
        safe_print(f"❌ خطا در ایجاد دایرکتوری خروجی {OUTPUT_DIR}: {e}")
        return
    
    output_path: str = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(base64_sub)
        safe_print(f"\n🎉 {len(top_configs)} کانفیگ با شماره‌گذاری یکتا در قالب سابسکریپشن Base64 ذخیره شد: {output_path}")
        
        safe_print(f"🏆 5 کانفیگ برتر (فقط برای نمایش در لاگ):")
        for i, cfg in enumerate(top_configs[:5], start=1):
            safe_print(
                f"  {i}. {cfg['server']}:{cfg['port']} - "
                f"تاخیر: {cfg['latency_ms']:.2f}ms, "
                f"جیتر: {cfg['jitter_ms']:.2f}ms"
            )
    except IOError as e:
        safe_print(f"❌ خطا در ذخیره فایل به {output_path}: {e}")

# --- نقطه ورود اصلی برنامه (Main Entry Point) ---

def main() -> None:
    """Main function to orchestrate fetching, testing, and saving VLESS Reality configurations."""
    start_time = time.time()
    
    all_unique_configs = gather_configurations(CONFIG_URLS)
    
    evaluated_and_sorted_configs = evaluate_and_sort_configs(all_unique_configs)
    
    if evaluated_and_sorted_configs:
        save_results_base64(evaluated_and_sorted_configs) 
    else:
        safe_print("\n🚫 هیچ کانفیگ فعالی برای ارزیابی و ذخیره یافت نشد.")
    
    elapsed = time.time() - start_time
    safe_print(f"\n⏱️ کل زمان اجرا: {elapsed:.2f} ثانیه")

if __name__ == "__main__":
    main()
