import os
import json
import xml.etree.ElementTree as ET
import urllib.parse
import requests
from datetime import datetime
from src.utils.logger import logger
from src.utils.proxy import get_current_proxy_str, get_requests_proxies

class WebDAVSync:
    def __init__(self, webdav_config: dict) -> None:
        self.config = webdav_config
        self.enabled = self.config.get("enabled", False)

        provider = self.config.get("provider", "jianguoyun")
        provider_cfg = self.config.get(provider, {})

        self.server_url = (provider_cfg.get("server_url") or self.config.get("server_url", "https://dav.jianguoyun.com/dav/")).strip()
        self.username = provider_cfg.get("username") or self.config.get("username", "")
        self.password = provider_cfg.get("password") or self.config.get("password", "")

        raw_dir = (provider_cfg.get("remote_dir") or self.config.get("remote_dir", "/VoiceInput")).strip("/")
        self.remote_dir = f"/{raw_dir}" if raw_dir else "/VoiceInput"
        self.remote_main_file = f"{self.remote_dir}/config.json"
        self.max_backups = int(provider_cfg.get("max_backups") or self.config.get("max_backups", 5))

    def _get_auth(self):
        return (self.username, self.password) if self.username else None

    def _get_proxies(self):
        return get_requests_proxies()

    def _get_url_for_path(self, rel_path: str) -> str:
        """精准拼装 WebDAV 服务器 URL，自动去重与标准化层级。"""
        if not self.server_url:
            return ""
        
        parsed_server = urllib.parse.urlsplit(self.server_url)
        base_path = parsed_server.path.rstrip('/')
        clean_rel = rel_path.strip('/')

        base_parts = [p for p in base_path.split('/') if p]
        rel_parts = [p for p in clean_rel.split('/') if p]

        # 智能层级去重 (如 server_url 已包含 VoiceInput)
        if base_parts and rel_parts and base_parts[-1].lower() == rel_parts[0].lower():
            merged_parts = base_parts + rel_parts[1:]
        else:
            merged_parts = base_parts + rel_parts

        full_path = "/" + "/".join(merged_parts)
        new_split = urllib.parse.SplitResult(
            scheme=parsed_server.scheme,
            netloc=parsed_server.netloc,
            path=full_path,
            query="",
            fragment=""
        )
        return urllib.parse.urlunsplit(new_split)

    def ensure_remote_dir(self) -> None:
        if not self.remote_dir or self.remote_dir == "/":
            return

        parts = self.remote_dir.strip("/").split("/")
        curr = ""
        for p in parts:
            if not p:
                continue
            curr += f"/{p}"
            url = self._get_url_for_path(curr) + "/"
            try:
                requests.request("MKCOL", url, auth=self._get_auth(), proxies=self._get_proxies(), timeout=5)
            except Exception:
                pass

    def upload_config(self, local_config_path: str, save_history: bool = True) -> tuple[bool, str]:
        if not os.path.exists(local_config_path):
            logger.log("WebDAV", f"Upload failed: Local config file not found ({local_config_path})")
            return False, "Local config file not found."

        if not self.server_url or not self.username:
            logger.log("WebDAV", "Upload failed: Server URL or Username not configured.")
            return False, "Please configure WebDAV Server URL and Username."

        try:
            self.ensure_remote_dir()
            with open(local_config_path, "r", encoding="utf-8") as f:
                content = f.read()

            main_url = self._get_url_for_path(self.remote_main_file)
            resp = requests.put(main_url, data=content.encode("utf-8"), auth=self._get_auth(), proxies=self._get_proxies(), timeout=8)

            if resp.status_code in [200, 201, 204]:
                logger.log("WebDAV", f"Successfully uploaded main config to {main_url}")
                if save_history:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    history_name = f"config_{ts}.json"
                    hist_url = self._get_url_for_path(f"{self.remote_dir}/{history_name}")
                    try:
                        requests.put(hist_url, data=content.encode("utf-8"), auth=self._get_auth(), proxies=self._get_proxies(), timeout=8)
                        logger.log("WebDAV", f"Uploaded timestamped backup: {history_name}")
                        self._cleanup_old_backups()
                    except Exception as hist_err:
                        logger.log("WebDAV", f"History backup upload warning: {hist_err}")

                return True, "Config successfully uploaded to WebDAV!"
            else:
                logger.log("WebDAV", f"Upload failed HTTP Status: {resp.status_code}")
                return False, f"WebDAV upload failed (HTTP Status: {resp.status_code})"
        except Exception as e:
            logger.log("WebDAV", f"Upload exception: {str(e)}")
            return False, f"WebDAV upload exception:\n{str(e)}"

    def download_config(self, local_config_path: str, remote_filename: str = None) -> tuple[bool, str]:
        if not self.server_url or not self.username:
            logger.log("WebDAV", "Download failed: Server URL or Username not configured.")
            return False, "Please configure WebDAV Server URL and Username."

        try:
            target_rel = f"{self.remote_dir}/{remote_filename}" if remote_filename else self.remote_main_file
            url = self._get_url_for_path(target_rel)
            
            resp = requests.get(url, auth=self._get_auth(), proxies=self._get_proxies(), timeout=8)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    logger.log("WebDAV", f"Download failed: {url} is not valid JSON")
                    return False, "Downloaded WebDAV file is not valid JSON."

                os.makedirs(os.path.dirname(os.path.abspath(local_config_path)), exist_ok=True)
                with open(local_config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                logger.log("WebDAV", f"Successfully downloaded config from {url}")
                return True, "Config successfully downloaded and applied locally!"
            elif resp.status_code == 404:
                logger.log("WebDAV", f"Remote file not found: {url}")
                return False, f"Remote config file not found on WebDAV server ({url}). Please upload your config first."
            else:
                logger.log("WebDAV", f"Download failed HTTP Status: {resp.status_code}")
                return False, f"WebDAV download failed (HTTP Status: {resp.status_code})"
        except Exception as e:
            logger.log("WebDAV", f"Download exception: {str(e)}")
            return False, f"WebDAV download exception:\n{str(e)}"

    def list_backups(self) -> tuple[bool, list[dict], str]:
        if not self.server_url or not self.username:
            return False, [], "Please configure WebDAV Server URL and Username."

        url = self._get_url_for_path(self.remote_dir)
        if not url.endswith("/"):
            url += "/"
            
        headers = {"Depth": "1"}

        try:
            resp = requests.request("PROPFIND", url, headers=headers, auth=self._get_auth(), proxies=self._get_proxies(), timeout=8)
            if resp.status_code in [200, 207]:
                backups = []
                try:
                    tree = ET.fromstring(resp.content)
                    for response in tree.findall("{DAV:}response"):
                        href_elem = response.find("{DAV:}href")
                        if href_elem is not None and href_elem.text:
                            href = href_elem.text.strip()
                            name = os.path.basename(href.rstrip("/"))
                            if name and name.endswith(".json"):
                                getlastmodified = ""
                                prop_elem = response.find(".//{DAV:}getlastmodified")
                                if prop_elem is not None and prop_elem.text:
                                    getlastmodified = prop_elem.text.strip()

                                backups.append({
                                    "filename": name,
                                    "href": href,
                                    "modified": getlastmodified
                                })
                except Exception as xml_err:
                    print(f"[WebDAV] XML parse warning: {xml_err}")

                backups.sort(key=lambda x: x["filename"], reverse=True)
                return True, backups, "Backups retrieved successfully."
            else:
                return False, [], f"WebDAV list failed (HTTP Status: {resp.status_code})"
        except Exception as e:
            return False, [], f"WebDAV list exception:\n{str(e)}"

    def _cleanup_old_backups(self) -> None:
        ok, backups, _ = self.list_backups()
        if not ok or not backups:
            return

        history_files = [b for b in backups if b["filename"].startswith("config_") and b["filename"] != "config.json"]

        if len(history_files) > self.max_backups:
            to_delete = history_files[self.max_backups:]
            for old_file in to_delete:
                fname = old_file["filename"]
                del_url = self._get_url_for_path(f"{self.remote_dir}/{fname}")
                try:
                    res = requests.delete(del_url, auth=self._get_auth(), proxies=self._get_proxies(), timeout=5)
                    logger.log("WebDAV", f"Auto-deleted old backup '{fname}' (HTTP Status: {res.status_code})")
                except Exception as del_err:
                    logger.log("WebDAV", f"Exception deleting old backup '{fname}': {del_err}")

