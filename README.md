# global-stepper-b2b-plan
海布里电气（SEAWERY）混合 / 闭环步进电机出海（北美 / 欧洲 / 中东 / 东南亚）B2B 年度营销计划，单文件 HTML：`public/index.html`。
由 `../global-servo-plan`（MOTIONX 伺服版，2026-11-16）改写，2026-11-20。

重新生成：
```
python3 -I build/prep.py <research目录> ../global-servo-plan/build/data.json build/data.json   # 图表与搜索排名数据
cat build/tpl_*.html > build/template.html && python3 -I build/build.py <research目录> build/data.json build/template.html public/index.html
```
引用写法 `[[轮次:编号]]`：US-R1 / US-R2 / NA / EUME / SEA（伺服口径）、US-R3（美国步进）、GL-R3（四区域步进 Trends）、X（`build/sources_extra.json`：Census HS6、公司目录、美国 v3 计划）。
