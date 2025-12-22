# Slide 214

z  
↑  
|  
|         Q₂  
|        /  
|       /  
|      Q₁  
|     /  
|    /  
|   /  
|  /  
| /  
O------------------→ r  
   r₁  r₂  

图9-2 待求曲线的Q₁Q₂段的欧氏线长应等于$\mathrm{d}l|_{P_1P_2}$  

L线的内禀弯曲情况。再以$z$轴为对称轴将曲线旋转一周便扫出一个曲面，其外部弯曲情况就反映赤道面$\mathcal{P}$的内禀弯曲情况。这样得到的曲面叫做静态球对称恒星的嵌入图。刚才所谈的是嵌入图的绘制原则，下面介绍绘制方法。  

设欧氏空间中$z$-$r$面上待求曲线的函数表达式为$z(r)$，则由式(9-1-8)可知该曲线的任一元段有  
\[
\mathrm{d}s^2(\text{欧}) = \left[ \frac{\mathrm{d}z(r)}{\mathrm{d}r} \mathrm{d}r \right]^2 + \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2 = \left[ \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 \right] \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2,
\]  
(9-1-9)  
将上式与式(9-1-6)对比可知，为使$Q_1Q_2$段的欧氏线长等于$\mathrm{d}l|_{P_1P_2}$，只需  
\[
\left[ \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 \right] \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2 = \left[ 1 - \frac{2m(r)}{r} \right]^{-1} \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2,
\]  
(9-1-10)  
为此又只需  
\[
\left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 + 1 = \left[ 1 - \frac{2m(r)}{r} \right]^{-1}, \quad \text{即} \quad \left( \frac{\mathrm{d}z}{\mathrm{d}r} \right)^2 = \frac{2m(r)}{r - 2m(r)},
\]  
(9-1-11)  
因而  
\[
\frac{\mathrm{d}z(r)}{\mathrm{d}r} = \sqrt{\frac{2m(r)}{r - 2m(r)}}.
\]  
(9-1-12)  
约定$z(0)=0$，则  
\[
z(r) = \int_0^r \sqrt{\frac{2m(r')}{r' - 2m(r')}} \mathrm{d}r', \quad (\text{对 } 0 < r < \infty).
\]  
(9-1-13)  
因为$r \geq R$时$m(r)=M$[见式(9-1-4)]，所以对$r \geq R$有  
\[
z(r) = \int_0^R \sqrt{\frac{2m(r)}{r - 2m(r)}} \mathrm{d}r + \int_R^r \sqrt{\frac{2M}{r' - 2M}} \mathrm{d}r' = 
\]

> [!NOTE] 🖼️ Figure 描述  
> 该图是二维坐标系中$z$-$r$平面上的几何关系示意图。坐标系原点$O$位于左下角，$z$轴垂直向上标注"z"，$r$轴水平向右标注"r"。图中有一条从原点$O$出发向右上方延伸的平滑实线曲线，初始段较陡峭，随$r$增大逐渐平缓。曲线上标有两点：左侧点$Q_1$和右侧点$Q_2$。从$Q_1$、$Q_2$分别向下引垂直虚线，与$r$轴相交于$r_1$、$r_2$（$r_1 < r_2$）。所有关键点（$O$、$Q_1$、$Q_2$、$r_1$、$r_2$）均为实心圆点并标注文字标签。坐标轴和曲线为黑色实线，垂线为黑色虚线。图形用于说明欧氏线长$\mathrm{d}s(\text{欧})$与内禀距离$\mathrm{d}l|_{P_1P_2}$的等价关系。

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号修正**：原文"dl|_{p₁p₂}"应为"dl|_{P₁P₂}"，根据[P-1]页式(9-1-7)和图9-1标注，邻点应使用大写字母$P_1$、$P_2$（见[P-1]页"设$L$是...$P_1,P_2$是$L$上任意两个邻点"）。  
> 2. **逻辑补全**：原文"赤道面S"应为"赤道面$\mathcal{P}$"，根据[P-1]页图9-1标注和数学符号一致性（$\mathcal{P}$代表赤道面）。  
> 3. **公式修正**：原文"z(r) = \int_0^r \sqrt{\frac{2m(r')}{r' - 2m(r')}} \mathrm{d}r', \quad (\text{对 } 0 < r < \infty)。"末尾句号应移至括号外，符合数学公式排版规范（见[N+1]页式(9-1-14)的排版方式）。  
> 4. **OCR错误**：原文"r' - 2M"在积分上限处应为"r' - 2M"（见[N+1]页式(9-1-14)），但当前页公式未完成，保留原始结构。

<CTX>
{ "summary": "本页推导静态球对称恒星嵌入图的数学表达式，通过欧氏空间曲线z(r)的积分公式(9-1-13)建立内禀弯曲与外在嵌入的映射关系，为后续计算r≥R区域的显式解做准备。", "keywords": ["嵌入图", "z(r)积分", "内禀弯曲", "欧氏空间", "史瓦西几何"] }
</CTX>