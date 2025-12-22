# Slide 199

§8.6 相对论在GPS(全球定位系统)中的应用

式(8-6-18)表明引力势$|\Phi(r)|$与$r$成反比，故地面的$|\Phi(R)|$大于空中的$|\Phi(r)|$。由数字计算可知[见式(8-3-23)]
$$
\frac{|\Phi(R)|}{c^2} = \frac{GM}{c^2 R} = \frac{(6.7 \times 10^{-11}) \times (6 \times 10^{24})}{(3 \times 10^8)^2 \times (6.4 \times 10^6)} \approx 7 \times 10^{-10} \ll 1,
$$
(8-6-20)

故可用牛顿二项式定理
$$
(1 - x)^{-1} \approx 1 + x
$$
(8-6-21)

求得
$$
\frac{1 + \frac{\Phi}{2c^2}}{1 - \frac{\Phi}{2c^2}} \approx \left(1 + \frac{\Phi}{2c^2}\right)\left(1 + \frac{\Phi}{2c^2}\right) \approx 1 + \frac{\Phi}{c^2}, \quad \left( \frac{1 + \frac{\Phi}{2c^2}}{1 - \frac{\Phi}{2c^2}} \right)^2 \approx \left(1 + \frac{\Phi}{c^2}\right)^2 \approx 1 + \frac{2\Phi}{c^2},
$$

以及
$$
\left(1 - \frac{\Phi}{2c^2}\right)^4 = \left[ \left(1 - \frac{\Phi}{2c^2}\right)^2 \right]^2 \approx \left(1 - \frac{\Phi}{c^2}\right)^2 \approx 1 - \frac{2\Phi}{c^2},
$$

于是式(8-6-19)近似简化为
$$
\mathrm{d}s^2 = -\left(1 + \frac{2\Phi}{c^2}\right) (c \mathrm{d}\hat{t})^2 + \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \mathrm{d}\varphi^2).
$$
(8-6-22)

上式是史瓦西线元在坐标系$\{\hat{t}, r, \theta, \varphi\}$的近似表达式。设某钟静止于地面上某点B，则其空间坐标为
$$
r = R = \text{常数}, \quad \theta = \theta_{\mathrm{B}} = \text{常数}, \quad \varphi = \varphi_{\mathrm{B}},
$$

故 $\mathrm{d}r = 0$, $\mathrm{d}\theta = 0$ 而 $\mathrm{d}\varphi \neq 0$ (该钟因地球自转而做圆周运动)，把式(8-6-22)用于该钟的世界线的任一元段得
$$
\mathrm{d}s^2 = -\left[1 + \frac{2\Phi(R)}{c^2}\right] (c \mathrm{d}\hat{t})^2 + \left[1 - \frac{2\Phi(R)}{c^2}\right] R^2 \sin^2\theta_{\mathrm{B}} \mathrm{d}\varphi^2 = -\left[1 + \frac{2\Phi(R)}{c^2} - \left(1 - \frac{2\Phi(R)}{c^2}\right) \frac{(R \sin\theta_{\mathrm{B}} \mathrm{d}\varphi)^2}{(c \mathrm{d}\hat{t})^2}\right] (c \mathrm{d}\hat{t})^2.
$$
(8-6-23)

令
$$
\hat{u} \equiv R \sin\theta_{\mathrm{B}} \frac{\mathrm{d}\varphi}{\mathrm{d}\hat{t}},
$$
(8-6-24)

> [!NOTE] 🖼️ Figure 描述  
> 图8-12：地球扁球体示意图。球体中心为地心，赤道半径大于极半径。表面有两条水平虚线：赤道圈（水平虚线）和北半球纬度圈（水平虚线）。点A（赤道处）和点B（北半球）用实心点标记并标注字母。从地心到A的实线标注为$r_A$，到B的实线标注为$r_B$。从B向赤道平面作垂线，垂足到地心的水平距离标注为$l_B$。$r_B$与赤道平面的夹角标注为$\theta$。图下方标题为“图8-12 地球略呈扁球状”。所有线条为黑色，无填充色；虚线表示不可见的参考圈，实线表示可见的几何关系。

> [!WARNING] 🛡️ 原文勘误  
> 1. OCR将"≈"误识别为"="：原句"≈ 7 × 10^{-10} << 1"中"<<"应为"\ll"（远小于符号），已修正为"\ll"。  
> 2. 符号不一致：[P-1]页(8-6-24)定义速度为$\hat{u}$，但[Target]页OCR误写为$\nu$（希腊字母nu），根据上下文"线速率"及[N+1]页验证，应统一为拉丁字母$\hat{u}$（带帽u）。  
> 3. 公式(8-6-23)末尾括号缺失：OCR漏印右括号，根据数学结构补充完整。  
> 4. 文本重复：[P-1]页末句"则"与[Target]页开头"式(8-6-18)表明..."存在语义衔接，但OCR导致轻微冗余；已优化表述确保逻辑流（删除冗余"则"字）。

<CTX>
{ "summary": "本页推导GPS相对论修正的时空度规简化过程，通过牛顿二项式展开将史瓦西线元转化为近似平直形式，并引入地球自转效应分析海面钟的固有时间偏差。核心是建立引力势Φ与坐标变换的关联，为后续总效应计算奠定基础。", "keywords": ["史瓦西线元", "引力势", "坐标变换", "固有时间", "地球扁率"] }
</CTX>