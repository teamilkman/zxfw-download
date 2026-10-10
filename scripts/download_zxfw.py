#!/usr/bin/env python3
"""下载人民法院在线服务（zxfw.court.gov.cn）电子送达文书。

用法:
  download_zxfw.py --list --link "<送达短信全文或链接>"        # 只列清单
  download_zxfw.py --link "<送达短信全文或链接>" --target "<保存目录>"

参数 qdbh/sdbh/sdsin 从 --link 文本中自动提取（正则匹配，容忍短信全文混排）。
"""
import argparse
import json
import os
import re
import sys
import urllib.request

API = "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew"
PARAM_RE = re.compile(r"[?&](qdbh|sdbh|sdsin)=([0-9A-Za-z]{16,64})")
ILLEGAL_RE = re.compile(r'[\\/:*?"<>|\r\n]')


def log(msg):
    print(msg, flush=True)


def http_post_json(url, body, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_docs(params):
    resp = http_post_json(API, params)
    if resp.get("code") != 200:
        raise RuntimeError(f"接口返回异常: code={resp.get('code')} msg={resp.get('msg')}")
    docs = resp.get("data") or []
    if not docs:
        raise RuntimeError("接口返回清单为空（可能签名已失效或该送达编号下无文书）")
    return docs


def unique_in_batch(filename, used):
    if filename not in used:
        return filename
    base, ext = os.path.splitext(filename)
    n = 2
    while f"{base}_{n}{ext}" in used:
        n += 1
    return f"{base}_{n}{ext}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", required=True, help="送达短信全文或其中的链接")
    ap.add_argument("--target", help="保存目录（--list 时可省略）")
    ap.add_argument("--list", action="store_true", help="只列清单不下载")
    args = ap.parse_args()

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    params = dict(PARAM_RE.findall(args.link))
    missing = {"qdbh", "sdbh", "sdsin"} - set(params)
    if missing:
        log(f"FAIL 未能从 --link 中提取参数: {', '.join(sorted(missing))}")
        log("请确认粘贴的是含 qdbh/sdbh/sdsin 的 zxfw.court.gov.cn 送达链接")
        return 2

    try:
        docs = fetch_docs(params)
    except Exception as e:
        log(f"FAIL 获取文书清单失败: {e}")
        return 1

    courts = sorted({d.get("c_fymc", "?") for d in docs})
    log(f"送达法院: {'、'.join(courts)}　共 {len(docs)} 份文书")
    for i, d in enumerate(docs, 1):
        log(f"  {i}. {d.get('c_wsmc', '?')}  ({d.get('c_wjgs') or '?'})")

    if args.list:
        return 0

    if not args.target:
        log("FAIL 未指定 --target 保存目录")
        return 2

    os.makedirs(args.target, exist_ok=True)
    used = set()
    failed = 0
    for d in docs:
        name = ILLEGAL_RE.sub("_", str(d.get("c_wsmc", "未命名")).strip()) or "未命名"
        ext = (d.get("c_wjgs") or "pdf").strip().lstrip(".").lower() or "pdf"
        filename = unique_in_batch(f"{name}.{ext}", used)
        path = os.path.join(args.target, filename)
        try:
            content = http_get(d["wjlj"])
            ok = len(content) > 0 and (ext != "pdf" or content[:5] == b"%PDF-")
            if not ok:
                failed += 1
                log(f"FAIL {name}: 内容校验未通过（{len(content)} 字节，非有效 PDF）")
                continue
            if os.path.exists(path):
                if os.path.getsize(path) == len(content):
                    used.add(filename)
                    log(f"SKIP {filename}  已存在（同大小），跳过")
                    continue
                base, e = os.path.splitext(filename)
                n = 2
                while os.path.exists(os.path.join(args.target, f"{base}_{n}{e}")):
                    n += 1
                filename = f"{base}_{n}{e}"
                path = os.path.join(args.target, filename)
            with open(path, "wb") as f:
                f.write(content)
            used.add(filename)
            log(f"OK   {filename}  {len(content)} bytes")
        except Exception as e:
            failed += 1
            log(f"FAIL {name}: {e}")

    if failed:
        log(f"完成，但有 {failed} 份失败。直链有时效，可原样重跑一次；仍失败请重新打开原链接")
        return 1
    log(f"全部完成，已保存到: {args.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
