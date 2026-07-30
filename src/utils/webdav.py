import os
import json
import xml.etree.ElementTree as ET
import requests
from datetime import datetime

class WebDAVSync:
    def __init__(self, webdav_config: dict) -> None:
        self.config = webdav_config
        self.enabled = self.config.get("enabled", False)
        self.server_url = self.config.get("server_url", "https://dav.jianguoyun.com/dav/").rstrip("/")
        self.username = self.config.get("username", "")
        self.password = self.config.get("password", "")
        self.remote_path = self.config.get("remote_path", "/VoiceInput/config.json").lstrip("/")

    def _get_auth(self):
        return (self.username, self.password) if self.username else None

    def _get_full_url(self, path: str = "") -> str:
        rel = path.lstrip("/") if path else self.remote_path
        return f"{self.server_url}/{rel}"

    def ensure_remote_dir(self) -> None:
        dir_path = os.path.dirname(self.remote_path)
        if not dir_path or dir_path == "/":
            return

        parts = dir_path.split("/")
        curr = ""
        for p in parts:
            if not p:
                continue
            curr += f"/{p}"
            url = f"{self.server_url}{curr}"
            try:
                requests.request("MKCOL", url, auth=self._get_auth(), timeout=5)
            except Exception:
                pass

    def upload_config(self, local_config_path: str, save_history: bool = True) -> tuple[bool, str]:
        if not os.path.exists(local_config_path):
            return False, "Local config file not found."

        if not self.server_url or not self.username:
            return False, "Please configure WebDAV Server URL and Username."

        try:
            self.ensure_remote_dir()
            with open(local_config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Upload main config.json
            url = self._get_full_url()
            resp = requests.put(url, data=content.encode("utf-8"), auth=self._get_auth(), timeout=8)

            if resp.status_code in [200, 201, 204]:
                # Optionally upload timestamped history backup (e.g. config_20260730_100000.json)
                if save_history:
                    dir_path = os.path.dirname(self.remote_path)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    history_name = f"config_backup_{ts}.json"
                    hist_rel = f"{dir_path}/{history_name}" if dir_path else history_name
                    hist_url = f"{self.server_url}/{hist_rel.lstrip('/')}"
                    try:
                        requests.put(hist_url, data=content.encode("utf-8"), auth=self._get_auth(), timeout=8)
                    except Exception:
                        pass
                return True, "Config successfully uploaded to WebDAV!"
            else:
                return False, f"WebDAV upload failed (HTTP Status: {resp.status_code})"
        except Exception as e:
            return False, f"WebDAV upload exception:\n{str(e)}"

    def download_config(self, local_config_path: str, remote_filename: str = None) -> tuple[bool, str]:
        if not self.server_url or not self.username:
            return False, "Please configure WebDAV Server URL and Username."

        try:
            if remote_filename:
                dir_path = os.path.dirname(self.remote_path)
                rel = f"{dir_path}/{remote_filename}" if dir_path else remote_filename
                url = f"{self.server_url}/{rel.lstrip('/')}"
            else:
                url = self._get_full_url()

            resp = requests.get(url, auth=self._get_auth(), timeout=8)
            if resp.status_code == 200:
                # Validate JSON format
                try:
                    data = resp.json()
                except Exception:
                    return False, "Downloaded WebDAV file is not valid JSON."

                os.makedirs(os.path.dirname(local_config_path), exist_ok=True)
                with open(local_config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                return True, "Config successfully downloaded and applied locally!"
            elif resp.status_code == 404:
                return False, f"Remote config file not found on WebDAV server ({url})."
            else:
                return False, f"WebDAV download failed (HTTP Status: {resp.status_code})"
        except Exception as e:
            return False, f"WebDAV download exception:\n{str(e)}"

    def list_backups(self) -> tuple[bool, list[dict], str]:
        if not self.server_url or not self.username:
            return False, [], "Please configure WebDAV Server URL and Username."

        dir_path = os.path.dirname(self.remote_path)
        url = f"{self.server_url}/{dir_path.lstrip('/')}" if dir_path else self.server_url

        headers = {"Depth": "1"}
        try:
            resp = requests.request("PROPFIND", url, headers=headers, auth=self._get_auth(), timeout=8)
            if resp.status_code in [200, 207]:
                backups = []
                try:
                    tree = ET.fromstring(resp.content)
                    for response in tree.findall("{DAV:}response"):
                        href_elem = response.find("{DAV:}href")
                        if href_elem is not None and href_elem.text:
                            href = href_elem.text.strip()
                            name = os.path.basename(href.rstrip("/"))
                            if name and (name.endswith(".json") or name == "config.json"):
                                # Get modified time if available
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
