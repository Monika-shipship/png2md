# Slide 226

L线的内禀弯曲情况。再以$z$轴为对称轴将曲线旋转一周便扫出一个曲面，其外部弯曲情况就反映赤道面$\mathcal{P}$的内禀弯曲情况。这样得到的曲面叫做静态球对称恒星的嵌入图。刚才所谈的是嵌入图的绘制原则，下面介绍绘制方法。

设欧氏空间中$z$-$r$面上待求曲线的函数表达式为$z(r)$，则由式(9-1-8)可知该曲线的任一元段有
$$
\mathrm{d}s^2(\text{欧}) = \left[ \frac{\mathrm{d}z(r)}{\mathrm{d}r} \mathrm{d}r \right]^2 + \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2 = \left[ \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 \right] \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2,
$$
(9-1-9)

将上式与式(9-1-6)对比可知，为使$Q_1Q_2$段的欧氏线长等于$\mathrm{d}l|_{P_1P_2}$，只需
$$
\left[ \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 \right] \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2 = \left[ 1 - \frac{2m(r)}{r} \right]^{-1} \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2,
$$
(9-1-10)

为此又只需
$$
\left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 = \left[ 1 - \frac{2m(r)}{r} \right]^{-1}, \quad \text{即} \quad \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 = \frac{2m(r)}{r - 2m(r)},
$$
(9-1-11)

因而
$$
\frac{\mathrm{d}z(r)}{\mathrm{d}r} = \sqrt{\frac{2m(r)}{r - 2m(r)}}.
$$
(9-1-12)

约定$z(0)=0$，则
$$
z(r) = \int_0^r \sqrt{\frac{2m(r')}{r' - 2m(r')}} \mathrm{d}r', \quad (\text{对 } 0 < r < \infty).
$$
(9-1-13)

因为$r \geq R$时$m(r)=M$[见式(9-1-4)]，所以对$r \geq R$有
$$
z(r) = \int_0^R \sqrt{\frac{2m(r)}{r - 2m(r)}} \mathrm{d}r + \int_R^r \sqrt{\frac{2M}{r' - 2M}} \mathrm{d}r' =
$$

> [!NOTE] 🖼️ Figure 9-2
> 该图是二维$z$-$r$坐标系中的函数曲线图。坐标系原点$O$位于左下角，$z$轴垂直向上，$r$轴水平向右。图中有一条从原点$O$出发向右上方延伸的平滑实线曲线，初始较陡峭，随后逐渐平缓。曲线上标记两点：左侧的$Q_1$和右侧的$Q_2$。从$Q_1$和$Q_2$分别向下引垂直虚线，与$r$轴相交于$r_1$和$r_2$（$r_1 < r_2$）。所有关键点（$O$、$Q_1$、$Q_2$、$r_1$、$r_2$）均为黑色实心圆点并标注标签。坐标轴和曲线为黑色实线，垂线为黑色虚线，用于说明欧氏线长$\mathrm{d}l|_{P_1P_2}$的计算原理。

> [!WARNING] 🛡️ 原文勘误
> 1. 原文"赤道面S"应为"赤道面$\mathcal{P}$"（根据[P-1]页图9-1标注及上下文一致性，$\mathcal{P}$是赤道面符号）。
> 2. 原文"dl|_{p₁p₂}"中下标应为$P_1P_2$（大写，与[P-1]页式(9-1-7)和图9-1标注一致）。
> 3. 原文"r' - 2M"在积分式中应保持$r'$作为哑变量（已修正为$r'$）。

<CTX>
{ "summary": "本页详细推导静态球对称恒星嵌入图的数学表达式，通过欧氏空间中z(r)曲线的构建，将弯曲空间几何可视化。核心是建立z(r)的微分方程并求解积分表达式。", "keywords": ["嵌入图", "z(r)函数", "微分方程", "欧氏空间", "空间弯曲"] }
</CTX>