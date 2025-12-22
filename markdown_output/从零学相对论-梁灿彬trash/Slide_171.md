# Slide 171

§ 8.1 史瓦西真空解 159  

由式 (8-1-1) 可知，静态观者世界线上 $\mathrm{d}r = \mathrm{d}\theta = \mathrm{d}\varphi = 0$，代入史瓦西线元得  
\[
\mathrm{d}s^2 = -\left(1 - \frac{2M}{r}\right) \mathrm{d}t^2,
\tag{8-1-8}
\]  
沿线段 $\mu_{\mathrm{A}}$ 和 $\mu_{\mathrm{B}}$ 积分给出（第一步用到式 (3-2-1)）  
\[
\Delta \tau_{\mathrm{A}} = \int_{\text{沿}\mu_{\mathrm{A}}} \sqrt{-\mathrm{d}s^2} = \left(1 - \frac{2M}{r_{\mathrm{A}}}\right)^{1/2} \Delta t_{\mathrm{A}},
\tag{8-1-9a}
\]  
\[
\Delta \tau_{\mathrm{B}} = \int_{\text{沿}\mu_{\mathrm{B}}} \sqrt{-\mathrm{d}s^2} = \left(1 - \frac{2M}{r_{\mathrm{B}}}\right)^{1/2} \Delta t_{\mathrm{B}}.
\tag{8-1-9b}
\]  
注意到 $\Delta t_{\mathrm{A}} = \Delta t_{\mathrm{B}}$ 及 $r_{\mathrm{A}} \neq r_{\mathrm{B}}$，便知  
\[
\Delta \tau_{\mathrm{A}} = \left(1 - \frac{2M}{r_{\mathrm{A}}}\right)^{1/2} \left(1 - \frac{2M}{r_{\mathrm{B}}}\right)^{-1/2} \Delta \tau_{\mathrm{B}} \neq \Delta \tau_{\mathrm{B}}.
\tag{8-1-10}
\]  
可见线段 $\mu_{\mathrm{A}}$ 和 $\mu_{\mathrm{B}}$ 经历的固有时间并不相同。在闵氏时空中，“等 $t$ 面”就是“同时面”，但现在看到这两个词汇对史瓦西时空有不同含义：等 $t$ 面上各点的坐标时 $t$ 相同而固有时 $\tau$ 一般不同。如果仍称之为“同时面”，只能理解为坐标时间相同的面。  

既然现在提到固有时和坐标时，我们想借此机会谈一谈相对论中的时间概念。最有物理意义的时间就是观者的固有时 $\tau$，它是观者携带的标准钟的读数，也是其生物钟的读数，是其感受到的实在时间。除固有时 $\tau$ 外，$\tau$ 的任一常增函数也可在一定程度上解释为该观者的时间。例如，设 $p$ 是史瓦西时空外的一点，$G$ 是世界线经过 $p$ 的观者。一方面，作为 $G$ 世界线的点，$p$ 有固有时 $\tau_p$；另一方面，作为时空点，$p$ 有坐标时 $t_p$（史瓦西坐标系 $\{t,r,\theta,\varphi\}$ 的 $t$ 坐标值），于是对 $G$ 线有函数 $t(\tau)$。图 8-3 示明这是常增函数，故坐标时 $t$ 在一定程度上代表 $G$ 的时间，称为**坐标时间**（coordinate time）。为表述方便，可想象观者 $G$ 除标准钟外还携带**坐标钟**（coordinate clock），其读数恰等于该点坐标时 $t$。  

下面讨论史瓦西坐标的取值范围。角度坐标范围为  
\[
0 \leqslant \theta < \pi, \quad 0 \leqslant \varphi < 2\pi.
\]  
时间坐标 $t$ 的取值范围达最大，即 $-\infty < t < \infty$，因静态性意味着“永恒不变”。径向坐标 $r$ 的范围虽无上限，但有下限 $r > 2M$（理由见后文）。

> [!NOTE] 🖼️ Figure 8-3  
> 二维坐标图：横轴 $r$（$0 \to \infty$），标有 $r=2M$ 垂直虚线；纵轴 $t$（$0 \to \infty$）。曲线 $G$ 代表观者世界线，从右下向左上延伸并穿过 $r=2M$。曲线上标两点：$p_1$（下方），$p_2$（上方，$p_2$ 在 $p_1$ 右上方）。$p_1$ 处有向上张开的未来光锥（锥顶 $p_1$，沿 $t$ 增加方向）。$p_1$ 和 $p_2$ 分别引出水平实线（等 $t$ 线）。世界线标 "G" 及 "$\tau$ 增" 箭头（$p_1 \to p_2$）。  
> *说明*：因 $p_1$ 未来光锥朝上张开，$p_2$ 在 $p_1$ 未来（$\tau_2 > \tau_1$）；由等 $t$ 线知 $t_2 > t_1$，故 $t(\tau)$ 是常增函数。

> [!WARNING] 🛡️ 原文勘误  
> 1. "永恒不"（原文截断）→ 修正为 **"永恒不变"**（据 [N+1] 页首句 "变" 补全，符合物理语境）  
> 2. "0 \leqslant \theta < \pi, ; 0 \leqslant \varphi < 2\pi" → 修正为 **"0 \leqslant \theta < \pi, \quad 0 \leqslant \varphi < 2\pi"**（删除多余分号，规范间距）  
> 3. "坐标时 $t_p$（史瓦西坐标系 $\{t,r,\theta,\varphi\}$ 的第 0 坐标 $t$ 在 $p$ 点的值）" → 简化为 **"$t$ 坐标值"**（避免冗余，保持学术简洁性）

<CTX>
{ "summary": "本页核心讨论史瓦西时空中固有时间与坐标时间的差异：通过静态观者世界线段的积分证明等 $t$ 面上固有时 $\tau$ 不相等（公式 8-1-10），阐明坐标钟与标准钟的区别，并明确史瓦西坐标范围（尤其 $r>2M$ 的物理约束）", "keywords": ["固有时间", "坐标时间", "静态观者", "史瓦西半径", "时间概念"] }
</CTX>