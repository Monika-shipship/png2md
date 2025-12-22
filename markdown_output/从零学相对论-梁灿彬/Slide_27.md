# Slide 27

§2.2 闵氏几何

闵氏空间(Minkowski space)。今后统一用符号 $\mathrm{d}s^2$ 代表线元（但元段长则仍记作 $\mathrm{d}l$），所以欧氏线元 $\mathrm{d}l^2 = \mathrm{d}y^2 + \mathrm{d}x^2$ 将改记作 $\mathrm{d}s^2 = \mathrm{d}y^2 + \mathrm{d}x^2$。

以上只是为陈述方便而讨论 2 维情况，不难将讨论推广到维数更高的空间。读者都熟悉 3 维欧氏空间，其线元在直角坐标系的表达式为
$$\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2, \tag{2-1-11}$$
如果改用球坐标系 $\{r,\theta,\varphi\}$，利用该系与直角系的熟知关系：
$$x = r\sin\theta\cos\varphi, \quad y = r\sin\theta\sin\varphi, \quad z = r\cos\theta, \tag{2-1-12}$$
由微分运算容易求得欧氏线元 $\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2$ 在球坐标系的表达式：
$$\mathrm{d}s^2 = \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \,\mathrm{d}\varphi^2). \tag{2-1-13}$$
我们再次强调，坐标变换改变的只是线元的表达式而不是线元本身。就是说，式(2-1-13)与(2-1-11)虽然形式不同，但实质一样，都代表 3 维欧氏线元，可表为连等式：
$$\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 = \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \,\mathrm{d}\varphi^2).$$
如果改用第三种坐标系（例如柱坐标系或者更复杂的坐标系），欧氏线元 $\mathrm{d}s^2$ 的表达式还会取其他更为复杂的形式。欧氏线元只在直角坐标系才有最简单的表达式 $\mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2$。想象地再补上第 4 维，把第 4 个直角坐标记作 $w$，便可写出 4 维欧氏线元在直角系的表达式：
$$\mathrm{d}s^2 = \mathrm{d}w^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2, \tag{2-1-14}$$
与 4 维闵氏线元
$$\mathrm{d}s^2 = -\mathrm{d}t^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 \tag{2-1-15}$$
相对应（但请特别注意右边第一项的负号）。

类似地，如果在闵氏时空中选取惯性坐标系以外的坐标系，闵氏线元的表达式也要改变。例如，若选 4 维球坐标系 $\{t,r,\theta,\varphi\}$，其中 $r,\theta,\varphi$ 仍由式(2-1-12)定义，则闵氏线元的表达式改为
$$\mathrm{d}s^2 = -\mathrm{d}t^2 + \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \,\mathrm{d}\varphi^2). \tag{2-1-16}$$
若选更复杂的坐标系，闵氏线元的表达式将更为复杂。当且仅当选用惯性坐标系时，闵氏线元才有最简单的表达式 $-\mathrm{d}t^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2$。

为方便起见，仍先讨论 2 维情况。把 $\mathrm{d}s^2 \equiv -\mathrm{d}t^2 + \mathrm{d}x^2$ 看作线元似乎意味着曲线的长度应定义为 $\mathrm{d}s$ 的积分，但 $\mathrm{d}t^2$ 前的负号却带来一个微妙之处，因为它导致 $\mathrm{d}s^2$ 正负不定。图 2-2 示出了三类曲线。曲线 $L_1$ 的任一元段都有 $\mathrm{d}s^2 > 0$，故元段长 $\mathrm{d}l$ 可自然定义为 $\mathrm{d}l \equiv \sqrt{\mathrm{d}s^2}$，曲线 $L_1$ 介于 $a_1$ 和 $b_1$ 点之间的一段的线长

> [!NOTE] 🖼️ Figure 2-2
> 二维闵氏时空坐标系图，水平轴为 $x$ 轴（箭头向右），垂直轴为 $t$ 轴（注释说明应为 $ct$ 轴，箭头向上）。图中包含三条曲线：
> 1. **曲线 $L_1$**：平缓上凸曲线（开口向下），位于右下部分，标有两点 $a_1$ 和 $b_1$；
> 2. **曲线 $L_2$**：较陡峭上凸曲线（开口向下），位于左上部分，更靠近 $t$ 轴，标有两点 $a_2$ 和 $b_2$；
> 3. **曲线 $L_3$**：通过原点的直线（斜率为正），位于 $L_1$ 和 $L_2$ 之间；
> 三条曲线相互交叉：$L_3$ 与 $L_1$ 在 $a_1$ 点附近相交，$L_3$ 与 $L_2$ 在 $b_2$ 点附近相交。所有曲线从第三象限延伸至第一象限。

> [!WARNING] 🛡️ 原文勘误
> 1. 修正微分符号：统一将 $ds^2$、$dx^2$ 等改为 $\mathrm{d}s^2$、$\mathrm{d}x^2$ 等，与前文[P-1]中一致（前文使用 $\mathrm{d}t$、$\mathrm{d}x$ 等符号）。
> 2. 修正开头衔接：将"space)。"与前文[P-1]衔接为"闵氏空间(Minkowski space)。"，还原完整表述。
> 3. 修正公式(2-1-13)和(2-1-16)中的标点：将句号移至公式标签外，符合数学排版规范。
> 4. 修正重复标题：删除多余的"§2.2 闵氏几何"标题（OCR重复识别所致）。
> 5. 修正间距：在 $\sin^2\theta \,\mathrm{d}\varphi^2$ 中添加适当空格，提高可读性。

<CTX>
{ "summary": "本节介绍闵氏几何的基本概念，重点阐述线元在不同坐标系下的表达式不变性，并对比欧氏几何与闵氏几何的差异。核心内容包括3维和4维欧氏线元、闵氏线元在各种坐标系中的表达形式，以及线元决定几何的基本原理。", "keywords": ["闵氏几何", "线元", "坐标变换", "不变量", "时空间隔"] }
</CTX>