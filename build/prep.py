"""生成步进版 data.json（图表与搜索排名表数据）。
用法：python3 -I prep.py <research目录> <旧 data.json（伺服版）> <输出 data.json>
research 下的 raw 文件是抓取得到的不可信数据：只读取数值和字符串字段，不执行。"""
import collections
import datetime
import glob
import json
import os
import re
import statistics as st
import sys
from urllib.parse import urlparse

RES, OLD, OUT = sys.argv[1:4]
old = json.load(open(OLD, encoding="utf8"))


def load(p):
    return json.load(open(p, encoding="utf8"))


def monthly(path):
    d = load(path)["data"]["timeseries"]
    tl = d["default"]["timelineData"] if "default" in d else d
    mon = collections.OrderedDict()
    for p in tl:
        ym = datetime.datetime.fromtimestamp(int(p["time"]), datetime.timezone.utc).strftime("%Y-%m")
        mon.setdefault(ym, []).append(p["value"])
    n = len(next(iter(mon.values()))[0])
    return list(mon), [[round(st.mean(v[i] for v in mon[k]), 1) for k in mon] for i in range(n)]


G = os.path.join(RES, "global/out_stepper_v3/raw")
TR = [  # 键, 文件, 显示用词
    ("US", glob.glob(os.path.join(RES, "out_us_stepper_v3/raw/trends-*.json"))[0], ["stepper motor", "closed loop stepper", "nema 23", "nema 34", "servo motor"]),
    ("MX", G + "/trends_motor_a_pasos_motor_paso_a_paso_nema_23__MX.json", ["motor a pasos", "motor paso a paso", "nema 23", "servomotor", "variador de frecuencia"]),
    ("DE", G + "/trends_schrittmotor_closed_loop_schrittmotor_ne_DE.json", ["Schrittmotor", "Closed Loop Schrittmotor", "Nema 23", "Servomotor", "Frequenzumrichter"]),
    ("AE", G + "/trends_stepper_motor_servo_motor_plc_AE.json", ["stepper motor", "servo motor", "plc"]),
    ("SA", glob.glob(os.path.join(RES, "global/out_eu_me/raw/trends-4a9e68_*SA.json"))[0], None),
    ("VN", G + "/trends_động_cơ_bước_step_motor_servo_biến_tần_VN.json", ["động cơ bước", "step motor", "servo", "biến tần"]),
    ("TH", G + "/trends_step_motor_stepper_motor_สเต_ปเปอร_มอเตอ_TH.json", ["step motor", "stepper motor", "สเต็ปเปอร์มอเตอร์", "servo", "อินเวอร์เตอร์"]),
    ("ID", G + "/trends_motor_stepper_servo_inverter_nema_23_ID.json", ["motor stepper", "servo", "inverter", "nema 23"]),
]
trends, stats = {}, {}
for k, p, terms in TR:
    if terms is None:  # 沙特沿用伺服版数据（同组含 stepper motor）
        trends[k] = old["trends"]["SA"]
        labels, series = trends[k]["labels"], trends[k]["series"]
        terms = trends[k]["terms"]
    else:
        labels, series = monthly(p)
        trends[k] = {"labels": labels, "terms": terms, "series": series}
    last, prev = slice(-12, None), slice(-24, -12)
    stats[k] = [(t, round(st.mean(s[last]), 1), round(st.mean(s[prev]), 1)) for t, s in zip(terms, series)]

# ---------- 进口：HS 8501（沿用）+ HS 850110（≤37.5 W，小型步进多在此）
h6 = load(glob.glob(os.path.join(RES, "out_us_servo_v2_hs6/raw/trade_*.json"))[0])["data"]["850110"]
t6 = {"total": {}, "china": {}}
for r in h6:
    t6["china" if r["CTY_CODE"] == "5700" else "total"][r["time"]] = r["GEN_VAL_MO"]
trade = {"8501": old["trade"]["8501"], "850110": t6}

# ---------- 价格：美国步进 Google Shopping（三个词，去重）
sh = load(glob.glob(os.path.join(RES, "out_us_stepper_v3/raw/shopping-*.json"))[0])["data"]
seen, prices = set(), []
for q, v in sh.items():
    for it in v.get("shopping", []):
        m = re.search(r"[\d,]+(?:\.\d+)?", it.get("price") or "")
        if not m:
            continue
        p = float(m.group(0).replace(",", ""))
        key = (it.get("title"), it.get("source"), p)
        if key in seen or p <= 0:
            continue
        seen.add(key)
        t = (it.get("title") or "")[:90]
        tl = t.lower()
        cat = "drv" if ("driver" in tl or "drive" in tl) and "kit" not in tl and "motor &" not in tl else ("kit" if "kit" in tl or "+" in tl or "with driver" in tl or "& driver" in tl else "mot")
        prices.append({"t": t, "p": p, "s": (it.get("source") or "")[:40], "q": q, "c": cat})
prices_all = {"US": prices}

# ---------- 搜索排名：美国换成步进词；其他国家保留伺服词（分销商参照）
serp = []
sp = load(glob.glob(os.path.join(RES, "out_us_stepper_v3/raw/serp-*.json"))[0])["data"]
for q, v in sp.items():
    doms = []
    for o in v.get("organic", []):
        d = urlparse(o.get("link", "")).netloc.replace("www.", "")
        if d and d not in doms and d not in ("youtube.com",):
            doms.append(d)
    serp.append({"m": "US", "q": q, "d": doms[:10], "kind": "stepper"})
for s in old["serp"]:
    if s["m"] != "US":
        serp.append(dict(s, kind="servo"))

out = {"trends": trends, "trade": trade, "prices": prices_all, "serp": serp, "stats": stats}
json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
for k, v in stats.items():
    print(k, v)
ps = sorted(x["p"] for x in prices)
print("prices", len(ps), "median", ps[len(ps) // 2], collections.Counter(x["c"] for x in prices))
for c in ("mot", "kit", "drv"):
    q = sorted(x["p"] for x in prices if x["c"] == c)
    if q:
        print(c, len(q), q[len(q) // 4], q[len(q) // 2], q[3 * len(q) // 4])
y = collections.defaultdict(lambda: [0, 0, 0])
for ym, v in t6["total"].items():
    y[ym[:4]][0] += v
for ym, v in t6["china"].items():
    y[ym[:4]][1] += v; y[ym[:4]][2] += 1
print({k: (round(a / 1e9, 2), round(b / 1e6), f"{b / a * 100:.1f}%", n) for k, (a, b, n) in sorted(y.items())})
