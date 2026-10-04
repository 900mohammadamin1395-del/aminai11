# -*- coding: utf-8 -*-

import os


def get_safe_proxies():
    """
    Some local proxy tools (common with VPN/anti-filtering setups) expose
    their proxy address with an "https://" scheme in the environment
    variables, even though the proxy itself only speaks plain HTTP for
    the CONNECT tunnel. That mismatch makes urllib3 try to negotiate TLS
    with the proxy itself, which can fail outright or — worse — just
    hang until the OS-level TCP timeout kicks in (which can take a
    couple of minutes). Rewriting the scheme to "http://" before handing
    it to requests fixes this without touching system settings.

    Returns a proxies dict for requests, or None if no proxy is set
    (letting requests fall back to its normal behaviour).
    """

    proxy_url = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )

    if not proxy_url:
        return None

    if proxy_url.startswith("https://"):
        proxy_url = "http://" + proxy_url[len("https://"):]

    return {"http": proxy_url, "https": proxy_url}
