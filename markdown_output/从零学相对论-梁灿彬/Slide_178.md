# Slide 178

式(4-3-5)已证明 $u_0^2 / c^2 \ll 1$，利用地球数据及物理常数（均指国际单位制数值）：
$$
M = 6 \times 10^{24}, \quad R = 6.4 \times 10^6, \quad G = 6.7 \times 10^{-11}, \quad c = 3 \times 10^8 \tag{8-3-22}
$$
易知赤道引力势 $\Phi_0$ 满足：
$$
\frac{|\Phi_0|}{c^2} = \frac{GM}{c^2 R} = \frac{(6.7 \times 10^{-11}) \times (6 \times 10^{24})}{(3 \times 10^8)^2 \times (6.4 \times 10^6)} \approx 7 \times 10^{-10} \ll 1, \tag{8-3-23}
$$
令 $x \equiv \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2}$，则 $x \ll 1$，用牛顿二项式定理 $(1+x)^{1/2} \approx 1 + x/2$ 可将式(8-3-21)简化为：
$$
\mathrm{d}\tau_0 \approx \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) \mathrm{d}t. \tag{8-3-24}
$$
将上式沿 $C_0$ 线（见图4-22）全程积分得：
$$
\tau_0 = \int_{0}^{t_q} \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) \mathrm{d}t = \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) t_q. \tag{8-3-25}
$$
再讨论赤道上空的任一 $C$ 线（$v$ 值任意），它与 $C_0$ 线有两点不同：① $C_0$ 线在赤道上，引力势为 $\Phi_0 \equiv \Phi(R)$，而 $C$ 线（飞机）在赤道上空离地面 $h$ 米处，引力势为 $\Phi \equiv \Phi(R+h)$；② $C_0$ 线代表固结在赤道某点的钟，满足 $\mathrm{d}\varphi = \Omega \mathrm{d}t$，其线速率 $u_0 = R\Omega$，而 $C$ 线是赤道上空的飞行钟，其线速率 $u = (R+h)  \mathrm{d}\varphi / \mathrm{d}t$。因此，式(8-3-18)用于 $C$ 线的任一元段给出：
$$
\begin{aligned}
\mathrm{d}s^2 &= -\left( 1 + \frac{2\Phi}{c^2} \right) c^2 \mathrm{d}t^2 + (R+h)^2 \mathrm{d}\varphi^2 \\
&= -\left( 1 + \frac{2\Phi}{c^2} \right) c^2 \mathrm{d}t^2 + u^2 \mathrm{d}t^2 \\
&= -\left( 1 + \frac{2\Phi}{c^2} - \frac{u^2}{c^2} \right) c^2 \mathrm{d}t^2,
\end{aligned} \tag{8-3-26}
$$
用 $\Phi$ 和 $u$ 分别替换式(8-3-25)的 $\Phi_0$ 和 $u_0$ 便得 $C$ 线的环球飞行时间 $\tau$：
$$
\tau = \left( 1 + \frac{\Phi}{c^2} - \frac{u^2}{2c^2} \right) t_q. \tag{8-3-27}
$$
式(8-3-27)与式(8-3-25)相减给出：
$$
\tau - \tau_0 = \left( \frac{\Phi - \Phi_0}{c^2} - \frac{u^2 - u_0^2}{2c^2} \right) t_q, \tag{8-3-28}
$$
式中的 $\Phi - \Phi_0$ 可由式(8-3-17)及式(8-3-20)求得：
$$
\Phi - \Phi_0 = -\frac{GM}{R+h} - \left( -\frac{GM}{R} \right) = \frac{GMh}{R(R+h)} \approx \frac{GMh}{R^2} = gh, \tag{8-3-29}
$$
其中 $g = GM / R^2$ 是地面的重力加速度。将上式代入式(8-3-28)给出：
$$
\tau - \tau_0 = \left( \frac{gh}{c^2} - \frac{u^2 - u_0^2}{2c^2} \right) t_q = \frac{1}{2c^2} \left[ 2gh - (u^2 - u_0^2) \right] t_q. \tag{8-3-30}
$$

> [!NOTE] 🖼️ Figure 描述  
> 图 8-5 是垂直布局的引力红移测量实验示意图：底部矩形标注 "E"（发射体），顶部矩形标注 "A"（接收体），两者垂直对齐；中间以波浪线连接，自下而上标注箭头和希腊字母 "γ"，表示 γ 射线传播路径；无填充色，仅黑色轮廓线，简洁展示发射体 E 向接收体 A 的垂直辐射关系。

> [!WARNING] 🛡️ 原文勘误  
> - 原 OCR 中 "$\mathrm{d}s_0^2$"（式 8-3-26）应为 "$\mathrm{d}s^2$"：前文（P-1 页式 8-3-19）及上下文均使用 $\mathrm{d}s^2$ 表示线元平方，且 $C$ 线非地面钟，下标 0 逻辑矛盾。已修正为 $\mathrm{d}s^2$。  
> - 原 OCR 中 "u = (R+h) \, \mathrm{d}\varphi / \mathrm{d}t" 的斜体 $\varphi$ 与 P-1 页式 8-3-19 一致，但需确认符号：P-1 页使用正体 $\varphi$（如 $\mathrm{d}\varphi$），符合物理惯例，故统一为 $\mathrm{d}\varphi$。  
> - 原 OCR 公式 (8-3-24) 结尾误植 "$\mathrm{d}t_0$"：P-1 页式 (8-3-21) 及上下文均用 $\mathrm{d}t$（坐标时），且 $C_0$ 线积分变量为 $t$，故修正为 $\mathrm{d}t$。

<CTX>
{ "summary": "本页完成原子钟环球飞行实验的理论推导，通过史瓦西线元计算引力势差与运动效应，导出飞行钟与地面钟的时间差公式 (8-3-30)；关键步骤包括地球参数代入、牛顿二项式近似及引力势差简化。", "keywords": ["引力钟慢", "原子钟实验", "史瓦西线元", "引力势差", "时间差公式"] }
</CTX>