import os
import requests
from src.utils.logger import logger

def get_current_proxy_str() -> str:
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY") or ""

def get_requests_proxies() -> dict:
    proxy_str = get_current_proxy_str()
    if proxy_str:
        return {
            "http": proxy_str,
            "https": proxy_str
        }
    return None

def apply_proxy_config(proxy_config: dict) -> None:
    enabled = proxy_config.get("enabled", False)
    protocol = proxy_config.get("protocol", "http").lower()
    host = proxy_config.get("host", "").strip()
    port = proxy_config.get("port", 7890)

    if enabled and host:
        proxy_url = f"{protocol}://{host}:{port}"
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["ALL_PROXY"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        os.environ["all_proxy"] = proxy_url
        logger.log("Network Proxy", f"[PROXY ENABLED] Global network proxy active: {proxy_url} (All HTTP/HTTPS/WebSocket requests routed via proxy)")
    else:
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            os.environ.pop(var, None)
        logger.log("Network Proxy", "[PROXY DISABLED] Global proxy disabled. Network requests routed directly.")

def test_proxy_connection(proxy_config: dict) -> tuple[bool, str]:
    protocol = proxy_config.get("protocol", "http").lower()
    host = proxy_config.get("host", "").strip()
    port = proxy_config.get("port", 7890)

    if not host:
        return False, "Please enter proxy host name (e.g. 127.0.0.1)."

    proxy_url = f"{protocol}://{host}:{port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    logger.log("Network Proxy Test", f"Testing proxy connection via [{proxy_url}] -> https://httpbin.org/ip...")

    try:
        resp = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        if resp.status_code == 200:
            origin_ip = resp.json().get("origin", "Unknown")
            logger.log("Network Proxy Test", f"Proxy connection SUCCESS. Exit IP: {origin_ip}")
            return True, f"Proxy connection succeeded!\nProxy IP: {origin_ip}"
        else:
            logger.log("Network Proxy Test", f"Proxy connection FAILED. HTTP Status: {resp.status_code}")
            return False, f"Proxy responded HTTP Status: {resp.status_code}"
    except Exception as e:
        logger.log("Network Proxy Test", f"Proxy connection EXCEPTION: {str(e)}")
        return False, f"Proxy connection failed:\n{str(e)}"

# Prevent pytest from mistaking this helper function for a test case
test_proxy_connection.__test__ = False

