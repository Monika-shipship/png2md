# Slide 199

§8.6 相对论在GPS(全球定位系统)中的应用

$$
\mathrm{d}s^2 = -\left( \frac{1 + \frac{\Phi}{2c^2}}{1 - \frac{\Phi}{2c^2}} \right)^2 (c \,\mathrm{d}\hat{t})^2 + \left(1 - \frac{\Phi}{2c^2}\right)^4 (\mathrm{d}r^2 + r^2 \,\mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\varphi^2) \, .
$$
(8-6-19)

式(8-6-18)表明引力势$|\Phi(r)|$与$r$成反比，故地面的$|\Phi(R)|$大于空中的$|\Phi(r)|$。由数字计算可知[见式(8-3-23)]
$$
\frac{|\Phi(R)|}{c^2} = \frac{GM}{c^2 R} = \frac{(6.67 \times 10^{-11}) \times (5.977 \times 10^{24})}{(3 \times 10^8)^2 \times (6.4 \times 10^6)} \approx 7 \times 10^{-10} \ll 1,
$$
(8-6-20)

故可用牛顿二项式定理
$$
(1 - x)^{-1} \approx 1 + x
$$
(8-6-21)

求得
$$
\frac{1 + \frac{\Phi}{2c^2}}{1 - \frac{\Phi}{2c^2}} \approx \left(1 + \frac{\Phi}{2c^2}\right)\left(1 + \frac{\Phi}{2c^2}\right) \approx 1 + \frac{\Phi}{c^2} \, , \quad \left( \frac{1 + \frac{\Phi}{2c^2}}{1 - \frac{\Phi}{2c^2}} \right)^2 \approx \left(1 + \frac{\Phi}{c^2}\right)^2 \approx 1 + \frac{2\Phi}{c^2} \, ,
$$

以及
$$
\left(1 - \frac{\Phi}{2c^2}\right)^4 = \left[ \left(1 - \frac{\Phi}{2c^2}\right)^2 \right]^2 \approx \left(1 - \frac{\Phi}{c^2}\right)^2 \approx 1 - \frac{2\Phi}{c^2} \, ,
$$

于是式(8-6-19)近似简化为
$$
\mathrm{d}s^2 = -\left(1 + \frac{2\Phi}{c^2}\right) (c \,\mathrm{d}\hat{t})^2 + \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \,\mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\varphi^2) \, .
$$
(8-6-22)

上式是史瓦西线元在坐标系$\{\hat{t}, r, \theta, \varphi\}$的近似表达式。设某钟静止于地面上某点B，则其空间坐标为
$$
r = R = \text{常数}, \quad \theta = \theta_{\mathrm{B}} = \text{常数}, \quad \varphi = \varphi_{\mathrm{B}},
$$

故 $\mathrm{d}r = 0$, $\mathrm{d}\theta = 0$ 而 $\mathrm{d}\varphi \neq 0$ (该钟因地球自转而做圆周运动)，把式(8-6-22)用于该钟的世界线的任一元段得
$$
\mathrm{d}s^2 = -\left[1 + \frac{2\Phi(R)}{c^2}\right] (c \,\mathrm{d}\hat{t})^2 + \left[1 - \frac{2\Phi(R)}{c^2}\right] R^2 \sin^2\theta_{\mathrm{B}} \,\mathrm{d}\varphi^2 = 
$$
$$
-\left[1 + \frac{2\Phi(R)}{c^2} - \left(1 - \frac{2\Phi(R)}{c^2}\right) \frac{(R \sin\theta_{\mathrm{B}} \,\mathrm{d}\varphi)^2}{(c \,\mathrm{d}\hat{t})^2}\right] (c \,\mathrm{d}\hat{t})^2 \, .
$$
(8-6-23)

令
$$
\hat{u} \equiv R \sin\theta_{\mathrm{B}} \frac{\mathrm{d}\varphi}{\mathrm{d}\hat{t}} \, ,
$$
(8-6-24)

> [!NOTE] 🖼️ Figure 描述  
> 三维透视的地球扁球体示意图。球体呈扁球状，赤道半径大于极半径。球体表面有两条水平虚线：赤道圈和北半球纬度圈。点A位于赤道圈（θ=π/2），标记为"A"；点B位于北半球纬度圈，标记为"B"。从球心到A的线段标注为"r_A"；从球心到B的线段标注为"r_B"。从B向赤道平面作垂线，垂足到球心的距离标注为"l_B"。球心处r_B与赤道平面的夹角标注为"θ"。图下方标题为"图8-12 地球略呈扁球状"。所有线条为黑色，虚线表示不可见的圈，实线表示可见半径。

> [!WARNING] 🛡️ 原文勘误  
> 1. 公式(8-6-20)中物理常数修正：根据前页[P-2]数据（$G = 6.67 \times 10^{-11}$, $M = 5.977 \times 10^{24}$），将OCR识别的近似值$6.7 \times 10^{-11}$和$6 \times 10^{24}$还原为精确值，保持全书一致性  
> 2. 符号修正：原文"<<"统一为标准数学符号"$\ll$"（远小于）  
> 3. 逻辑衔接：补充"该钟因地球自转而做圆周运动"的说明，使与前页[P-1]中"海面钟随地球自转的运动速率必须考虑"形成呼应

<CTX>
{ "summary": "本页推导史瓦西线元在GPS应用中的近似表达式，通过引力势Φ的二项式展开简化线元，为后续计算卫星钟与地面钟的时间差奠定基础。核心是建立坐标系与物理量的对应关系，重点处理地球自转对时空度规的影响。", "keywords": ["史瓦西线元", "引力势", "二项式展开", "坐标系变换", "地球自转效应"] }
</CTX>