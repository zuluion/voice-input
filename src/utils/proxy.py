import os
import requests

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
        print(f"[Proxy] Global proxy applied: {proxy_url}")
    else:
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            os.environ.pop(var, None)
        print("[Proxy] Global proxy disabled.")

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

    try:
        resp = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        if resp.status_code == 200:
            origin_ip = resp.json().get("origin", "Unknown")
            return True, f"Proxy connection succeeded!\nProxy IP: {origin_ip}"
        else:
            return False, f"Proxy responded HTTP Status: {resp.status_code}"
    except Exception as e:
        return False, f"Proxy connection failed:\n{str(e)}"
