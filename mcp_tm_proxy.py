#!/usr/bin/env python3
"""
TM Proxy MCP Server
Unified access to TrendGPT and TM Knowledge Base via MCP protocol.

Setup:
  pip install mcp httpx

Run:
  python mcp_tm_proxy.py
"""

import httpx
import json
import os
import socket
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Load .env if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ============ CONFIG ============
# TrendGPT MCP Server
TRENDGPT_URL = "https://trendgpt.trendmicro.com/mcp"
TRENDGPT_TOKEN = os.environ.get("TRENDGPT_TOKEN", "")

# TM Knowledge MCP Server (KB, Online Help, Automation Center, etc.)
TM_KNOWLEDGE_URL = "https://knowledge-mcp-server.trendmicro.com/mcp/"
TM_KNOWLEDGE_TOKEN = os.environ.get("TM_KNOWLEDGE_TOKEN", "")

# ============ INIT ============
mcp = FastMCP("tm-proxy")

# ============ HELPERS ============

def check_vpn() -> bool:
    """Check if TM internal services are reachable"""
    try:
        socket.create_connection(("trendgpt.trendmicro.com", 443), timeout=2)
        return True
    except (socket.timeout, socket.error):
        return False


MAX_CONTENT_CHARS = 500
MAX_RESPONSE_CHARS = 4000


def truncate_content(text: str, max_len: int = MAX_CONTENT_CHARS) -> str:
    """Truncate text to max length"""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def compact_results(data: dict) -> dict:
    """Compact search results to reduce token usage"""
    if not isinstance(data, dict):
        return data

    if "result" in data:
        inner = data["result"]
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except:
                return data
        if isinstance(inner, dict) and "result" in inner:
            items = inner["result"]
            if isinstance(items, list):
                compact = []
                for item in items:
                    c = {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                    }
                    if item.get("content"):
                        c["content"] = truncate_content(item["content"])
                    if item.get("summary"):
                        c["summary"] = truncate_content(item["summary"], 200)
                    compact.append(c)
                return {"result": compact}
    return data


def call_mcp_tool(url: str, token: str, tool_name: str, arguments: dict, timeout: float = 60.0) -> dict:
    """Call a tool on remote MCP server via HTTP transport"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()

        text = response.text
        for line in text.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data:
                    result = data['result']
                    if isinstance(result, dict):
                        if 'structuredContent' in result:
                            return compact_results(result['structuredContent'])
                        if 'content' in result:
                            content = result['content']
                            if isinstance(content, list) and len(content) > 0:
                                raw = content[0].get('text', content)
                                return compact_results({"result": raw})
                    return compact_results(result)
                elif 'error' in data:
                    return {"error": data['error']}
        return {"error": "No result in response"}


# ============ TOOLS ============

@mcp.tool()
def vpn_status() -> str:
    """Check if VPN is connected to Trend Micro network"""
    connected = check_vpn()
    return json.dumps({"vpn_connected": connected})


@mcp.tool()
def ask_trendgpt(message: str, model: str = "haiku") -> str:
    """
    Ask TrendGPT about Trend Micro products (Vision One, Apex One, Deep Security, etc.)

    Args:
        message: Question about TM products
        model: haiku (fast), sonnet (balanced), opus (best)
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected. Connect to TM GlobalProtect."})
    try:
        result = call_mcp_tool(
            TRENDGPT_URL,
            TRENDGPT_TOKEN,
            "query_trendgpt",
            {"message": message, "model": model},
            timeout=120.0
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_kb(query: str, top_k: int = 3, products: list = None, format: str = "summary") -> str:
    """
    Search Trend Micro Knowledge Base articles.

    Args:
        query: Search term
        top_k: Number of results (default 3)
        products: Filter by product names (optional)
        format: content, summary, or all
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        args = {"query": query, "top_k": top_k, "format": format}
        if products:
            args["products"] = products
        result = call_mcp_tool(TM_KNOWLEDGE_URL, TM_KNOWLEDGE_TOKEN, "knowledge_articles", args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_online_help(query: str, top_k: int = 3, format: str = "summary") -> str:
    """
    Search Trend Micro Online Help documentation.

    Args:
        query: Search term
        top_k: Number of results
        format: content, summary, or all
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        result = call_mcp_tool(
            TM_KNOWLEDGE_URL,
            TM_KNOWLEDGE_TOKEN,
            "online_help",
            {"query": query, "top_k": top_k, "format": format}
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_kb_article(article_id: str) -> str:
    """
    Get full KB article by ID.

    Args:
        article_id: Article ID (format: KA-XXXXXXX)
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        result = call_mcp_tool(
            TM_KNOWLEDGE_URL,
            TM_KNOWLEDGE_TOKEN,
            "knowledge_articles",
            {"ids": [article_id], "format": "content"}
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_threat_encyclopedia(query: str, num_results: int = 5) -> str:
    """
    Search Trend Micro Threat Encyclopedia for malware, vulnerabilities.

    Args:
        query: Threat name or CVE
        num_results: Number of results
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        result = call_mcp_tool(
            TM_KNOWLEDGE_URL,
            TM_KNOWLEDGE_TOKEN,
            "threat_encyclopedia",
            {"query": query, "num_results": num_results}
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_automation_center(query: str, top_k: int = 3, products: list = None) -> str:
    """
    Search Trend Micro Automation Center for scripts and API docs.
    Supports Vision One, Deep Security, Cloud One.

    Args:
        query: Search term
        top_k: Number of results
        products: Filter by product names
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        args = {"query": query, "top_k": top_k, "format": "summary"}
        if products:
            args["products"] = products
        result = call_mcp_tool(TM_KNOWLEDGE_URL, TM_KNOWLEDGE_TOKEN, "automation_center", args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_pdf_guides(query: str, top_k: int = 3, products: list = None) -> str:
    """
    Search Trend Micro PDF guides (admin, install, documentation).

    Args:
        query: Search term
        top_k: Number of results
        products: Filter by product names
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        args = {"query": query, "top_k": top_k, "format": "summary"}
        if products:
            args["products"] = products
        result = call_mcp_tool(TM_KNOWLEDGE_URL, TM_KNOWLEDGE_TOKEN, "pdf_guides", args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_research_news(query: str, top_k: int = 5) -> str:
    """
    Search Trend Micro research and news (threats, ransomware, APTs, etc.)

    Args:
        query: Search term
        top_k: Number of results
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        result = call_mcp_tool(
            TM_KNOWLEDGE_URL,
            TM_KNOWLEDGE_TOKEN,
            "trend_micro_research_and_news_search",
            {"query": query, "top_k": top_k}
        )
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_latest_product_versions(products: list = None) -> str:
    """
    Get latest product versions from Trend Micro Download Center.

    Args:
        products: List of product names (optional)
    """
    if not check_vpn():
        return json.dumps({"error": "VPN not connected"})
    try:
        args = {}
        if products:
            args["products"] = products
        result = call_mcp_tool(TM_KNOWLEDGE_URL, TM_KNOWLEDGE_TOKEN, "latest_product_versions", args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============ RUN ============

if __name__ == "__main__":
    mcp.run()
