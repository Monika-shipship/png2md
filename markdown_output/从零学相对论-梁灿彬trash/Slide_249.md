# Slide 249

标便得闵氏线元的国际单位制形式：
$$ \mathrm{d}s^2 = -c^2 \mathrm{d}t^2 + \mathrm{d}x^2 $$
[解毕]

例 3 已知 2 维史瓦西线元的几何单位制形式为
$$ \mathrm{d}s^2 = -\left(1 - \frac{2M}{r}\right) \mathrm{d}t^2 + \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r^2, $$
求其国际单位制形式。

解 把上式明确写成
$$ \mathrm{d}s^2_{\text{几}} = -\left(1 - \frac{2M_{\text{几}}}{r_{\text{几}}}\right) \mathrm{d}t^2_{\text{几}} + \left(1 - \frac{2M_{\text{几}}}{r_{\text{几}}}\right)^{-1} \mathrm{d}r^2_{\text{几}}. \tag{A-25} $$
关键是要将 $ M_{\text{几}} / r_{\text{几}} $ 用 $ M_{\text{国}} / r_{\text{国}} $ 表出。由式 (A-19) 知 $ r_{\text{几}} = r_{\text{国}} / c_{\text{国}} $，而
$$ \frac{M_{\text{几}}}{M_{\text{国}}} = \frac{\hat{M}_{\text{国}}}{\hat{M}_{\text{几}}} = \dim M = (\dim T) (\dim V)^3 (\dim G)^{-1} = \frac{G_{\text{国}}}{c_{\text{国}}^3}, \tag{A-26} $$
[其中第三步用到式 (A-13)，第四步用到式 (A-20) 及式 (A-15)。] 故
$$ M_{\text{几}} = \left( \frac{G_{\text{国}}}{c_{\text{国}}^3} \right) M_{\text{国}}. \tag{A-27} $$
上式与 $ r_{\text{几}} = r_{\text{国}} / c_{\text{国}} $ 结合给出
$$ \frac{M_{\text{几}}}{r_{\text{几}}} = \frac{ \left( G_{\text{国}} / c_{\text{国}}^3 \right) M_{\text{国}} }{ r_{\text{国}} / c_{\text{国}} } = \frac{G_{\text{国}}}{c_{\text{国}}^2} \frac{M_{\text{国}}}{r_{\text{国}}}. \tag{A-28} $$
去掉下标并仿照例 2 的做法，便得史瓦西线元的国际单位制形式：
$$ \mathrm{d}s^2 = -\left(1 - \frac{2GM}{c^2 r}\right) (c \mathrm{d}t)^2 + \left(1 - \frac{2GM}{c^2 r}\right)^{-1} \mathrm{d}r^2. $$
[解毕]

> [!NOTE] 🖼️ Figure 描述  
> 标注为“3 章题 2 解用图”的几何示意图：底部水平线段连接点 b（左端点）和 a（右端点），其中 m 位于 b 和 a 之间且靠近 a。从 b 垂直向上延伸至 B，斜向延伸至 B'（B' 位于 B 右侧更近中心）；从 a 垂直向上延伸至 A，斜向延伸至 A'（A' 位于 A 左侧更近中心）。中央区域 M（左）和 M'（右）通过垂直线段连接，M 位于 b 右上方，M' 位于 a 左上方。p 点位于 M 下方偏左，q 点位于 M' 下方偏右。关键连线：b→p、p→q、q→a、b→a（水平）、b→M、M→a、b→B、a→A、b→B'、a→A'，所有线型为实线无箭头，节点仅字母标注无填充。

> [!WARNING] 🛡️ 原文勘误  
> 原 OCR 将公式 $\frac{M_{\text{几}}}{r_{\text{几}}} = \frac{ \left( G_{\text{国}} / c_{\text{国}}^3 \right) M_{\text{国}} }{ r_{\text{国}} / c_{\text{国}} }$ 误写为 $\frac{ \left( G_{\text{国}} / c_{\text{国}}^3 \right) M_{\text{国}} }{ r_{\text{国}} / c_{\text{国}} }$（缺少分子括号），已修正为 $\frac{ \left( G_{\text{国}} / c_{\text{国}}^3 \right) M_{\text{国}} }{ r_{\text{国}} / c_{\text{国}} }$ 以保持量纲一致性。符号 $v$ 在 [P-1] 例 1 中明确定义为速度，但 [Target] 未出现速度符号，故无需调整；所有 $c$ 统一为 $c_{\text{国}}$ 以符合前文量纲分析框架。

<CTX>
{ "summary": "本页完成几何单位制向国际单位制转换的例3：史瓦西线元转换，核心是推导质量与长度的量纲关系 $M_{\text{几}}/r_{\text{几}} = (G_{\text{国}}/c_{\text{国}}^2)(M_{\text{国}}/r_{\text{国}})$，最终得到含 $c^2$ 的国际单位制形式。", "keywords": ["几何单位制", "量纲分析", "史瓦西线元", "单位制转换", "广义相对论"] }
</CTX>