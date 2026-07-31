import os
import socket
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
        no_proxy_str = "localhost,127.0.0.1,::1"
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["ALL_PROXY"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        os.environ["all_proxy"] = proxy_url
        os.environ["NO_PROXY"] = no_proxy_str
        os.environ["no_proxy"] = no_proxy_str
        logger.log("Network Proxy", f"[PROXY ENABLED] Global network proxy active: {proxy_url} (All external HTTP/HTTPS/WebSocket requests routed via proxy)")
    else:
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "NO_PROXY", "no_proxy"]:
            os.environ.pop(var, None)
        logger.log("Network Proxy", "[PROXY DISABLED] Global proxy disabled. Network requests routed directly.")


def test_proxy_connection(proxy_config: dict) -> tuple[bool, str]:
    protocol = proxy_config.get("protocol", "http").lower()
    host = proxy_config.get("host", "").strip()
    port = proxy_config.get("port", 7890)

    if not host:
        return False, "请输入代理服务器主机地址 (例如 127.0.0.1)。"

    # Step 1: 本地 Socket TCP 端口握手验证 (零网络依赖，秒级验证代理软件本身是否存活)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        if result != 0:
            logger.log("Network Proxy Test", f"Proxy TCP socket port check FAILED at {host}:{port}")
            return False, f"代理服务器未启动或无法连接：\n端口 {host}:{port} 拒绝连接 (Error Code: {result})\n请确认 Clash / v2ray 代理软件是否正常开启。"
    except Exception as e:
        logger.log("Network Proxy Test", f"Proxy TCP socket exception: {e}")
        return False, f"无法连接代理服务器端口 {host}:{port}：\n{str(e)}"

    # Step 2: 代理端口存活，发起公网出口 IP 连通性测试
    proxy_url = f"{protocol}://{host}:{port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    test_endpoints = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
        "https://www.cloudflare.com/cdn-cgi/trace"
    ]

    logger.log("Network Proxy Test", f"Proxy port {host}:{port} is ALIVE. Testing internet exit connection via [{proxy_url}]...")

    for endpoint in test_endpoints:
        try:
            resp = requests.get(endpoint, proxies=proxies, timeout=3)
            if resp.status_code == 200:
                ip_info = None
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        ip_info = data.get("ip") or data.get("origin")
                except Exception:
                    pass

                if not ip_info and "ip=" in resp.text:
                    for line in resp.text.splitlines():
                        if line.startswith("ip="):
                            ip_info = line.split("=")[1]
                            break

                ip_info = ip_info or "Connected"

                logger.log("Network Proxy Test", f"Proxy connection SUCCESS via {endpoint}. Exit IP: {ip_info}")
                return True, f"代理服务连通成功！\n代理节点: {proxy_url}\n公网出口 IP: {ip_info}"
        except Exception as e:
            logger.log("Network Proxy Test", f"Endpoint {endpoint} test failed: {e}")

    # 如果 TCP 握手成功但外网目标没响应，依旧说明代理端口已连通
    logger.log("Network Proxy Test", f"Proxy TCP port {host}:{port} is open, but external target timed out.")
    return True, f"代理服务器连通成功！\n代理节点: {proxy_url}\n(提示: 代理端口响应正常，公网出口测试超时)"

# Prevent pytest from mistaking this helper function for a test case
test_proxy_connection.__test__ = False
