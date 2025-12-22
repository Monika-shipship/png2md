# Slide 162

在史瓦西时空中，引力钟慢效应是广义相对论的核心预测之一。设 $G_1$ 和 $G_2$ 是两个静态观者，具有相同的 $\theta$ 和 $\varphi$ 坐标，径向坐标分别为 $r_1$ 和 $r_2$（其中 $r_2 < r_1$，即 $G_2$ 更靠近引力源中心）。采用约定的比钟方式：$G_1$ 在事件 $p_1$（固有时 $\tau_1$）用左眼观测 $G_2$ 的钟读数为 $\tau_2$，同时用右眼观测自身钟读数为 $\tau_1$；经过固有时 $\Delta\tau_1 = \tau_1' - \tau_1 > 0$ 后，$G_1$ 在 $p_1'$ 处再次观测，$G_2$ 的钟读数为 $\tau_2'$，定义 $\Delta\tau_2 = \tau_2' - \tau_2$。通过比较 $\Delta\tau_1$ 与 $\Delta\tau_2$，可判定钟的表观走时率。

由于 $G_1$ 的世界线上 $r, \theta, \varphi$ 为常数，其线元为：
$$
\mathrm{d}s^2|_{G_1} = -\left(1 - \frac{2M}{r_1}\right)\mathrm{d}t^2 + \left(1 - \frac{2M}{r_1}\right)^{-1}\mathrm{d}r^2 + r_1^2(\mathrm{d}\theta^2 + \sin^2\theta\,\mathrm{d}\varphi^2) = -\left(1 - \frac{2M}{r_1}\right)\mathrm{d}t^2 \quad (8\text{-}3\text{-}1)
$$
从 $p_1$ 积分到 $p_1'$ 得：
$$
\Delta\tau_1 = \int_{p_1}^{p_1'} \sqrt{-\mathrm{d}s^2|_{G_1}} = \int_{t_1}^{t_1'} \sqrt{1 - \frac{2M}{r_1}}\,\mathrm{d}t = \sqrt{1 - \frac{2M}{r_1}}\,\Delta t_1, \quad (8\text{-}3\text{-}2)
$$
其中 $\Delta t_1 \equiv t_1' - t_1$。类似地，对 $G_2$ 有：
$$
\Delta\tau_2 = \sqrt{1 - \frac{2M}{r_2}}\,\Delta t_2, \quad (8\text{-}3\text{-}3)
$$
其中 $\Delta t_2 \equiv t_2' - t_2$。联立得：
$$
\frac{\Delta\tau_1}{\Delta\tau_2} = \sqrt{\frac{1 - 2M/r_1}{1 - 2M/r_2}} \cdot \frac{\Delta t_1}{\Delta t_2} \quad (8\text{-}3\text{-}4)
$$
为证明 $\Delta t_1 / \Delta t_2 = 1$，考虑图 8-4 中的光子世界线 $\gamma$（径向类光测地线）。$\gamma$ 上 $\theta$ 和 $\varphi$ 为常数，线元满足：
$$
\mathrm{d}s^2|_{\gamma} = -\left(1 - \frac{2M}{r}\right)\mathrm{d}t^2 + \left(1 - \frac{2M}{r}\right)^{-1}\mathrm{d}r^2 \quad (8\text{-}3\text{-}5)
$$
由类光性 $\mathrm{d}s^2|_{\gamma} = 0$ 得：
$$
\mathrm{d}t = \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r \quad (8\text{-}3\text{-}6)
$$
沿 $\gamma$ 从 $p_2$ 到 $p_1$ 积分：
$$
t_1 - t_2 = \int_{r_2}^{r_1} \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r \quad (8\text{-}3\text{-}7)
$$
对另一光子世界线 $\gamma'$ 有类似结果：
$$
t_1' - t_2' = \int_{r_2}^{r_1} \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r \quad (8\text{-}3\text{-}8)
$$
对比式 (8-3-7) 与 (8-3-8) 得 $t_1' - t_2' = t_1 - t_2$，即 $\Delta t_1 = \Delta t_2$，故 $\Delta t_1 / \Delta t_2 = 1$。代入式 (8-3-4)：
$$
\frac{\Delta\tau_1}{\Delta\tau_2} = \sqrt{\frac{1 - 2M/r_1}{1 - 2M/r_2}} > 1 \quad (\text{因 } r_2 < r_1), \quad (8\text{-}3\text{-}9)
$$
即 $\Delta\tau_1 > \Delta\tau_2$，表明 $G_1$ 认为 $G_2$ 的钟更慢。由于 $G_1$ 和 $G_2$ 均为静态观者（无相对运动），此钟慢效应纯粹源于引力场，故称**引力钟慢效应**（或引力时间延缓）。该结论对任意静态时空均成立，仅式 (8-3-9) 需相应调整。

> [!NOTE] 🖼️ Figure 描述  
> 图 8-4 展示二维 $(r,t)$ 坐标系（横轴 $r$，纵轴 $t$）：  
> - 两条竖直实线：$G_1$ 位于 $r = r_1$（右侧），$G_2$ 位于 $r = r_2 < r_1$（左侧）  
> - $G_1$ 线上点：$p_1(t_1)$、$p_1'(t_1')$，竖直距离标为 $\Delta\tau_1$  
> - $G_2$ 线上点：$p_2(t_2)$、$p_2'(t_2')$，竖直距离标为 $\Delta\tau_2$  
> - 水平虚线：连接 $p_1/p_1'$ 到 $t$ 轴（标 $t_1/t_1'$），连接 $p_2/p_2'$ 到 $t$ 轴（标 $t_2/t_2'$）  
> - 光子世界线：$\gamma$（从 $p_2$ 到 $p_1$）和 $\gamma'$（从 $p_2'$ 到 $p_1'$）为上凸曲线，表征径向类光传播  
> - 所有元素以黑色绘制，坐标轴和虚线为细实线，$\gamma/\gamma'$ 为粗实线  

> [!WARNING] 🛡️ 原文勘误  
> 1. OCR 中 "$G_1$ 和 $G_2$ 的标准钟（仍记作 $G_1$ 和 $G_2$）" 逻辑冗余，修正为 "他们的标准钟" 以避免混淆（$G_1, G_2$ 作为观者标识已足够）  
> 2. 公式 (8-3-1) 中 "$r_1^2(\mathrm{d}\theta^2 + \sin^2\theta\mathrm{d}\varphi^2)$" 漏写逗号，补为 "$\sin^2\theta\,\mathrm{d}\varphi^2$" 以符合微分形式规范  
> 3. "G₁线上r,θ,φ为常数" 修正为 "$G_1$ 线上 $r, \theta, \varphi$ 为常数"，确保符号斜体一致性  

<CTX>
{ "summary": "本页推导史瓦西时空中引力钟慢效应的核心公式 (8-3-9)，证明引力场强处（$r$ 小）的钟走得更慢，且效应纯源于引力（静态观者无相对运动）。", "keywords": ["引力钟慢效应", "静态观者", "类光测地线", "固有时", "史瓦西度规"] }
</CTX>