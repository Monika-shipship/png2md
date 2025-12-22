# Slide 202

再次考虑静止在海平面 B 点的钟，它在新坐标系 $\{t, r, \theta, \tilde{\varphi}\}$ 的坐标自动满足 $r$, $\theta$, $\tilde{\varphi} =$ 常数（因它随地球自转而动），故 $\mathrm{d}r = 0$, $\mathrm{d}\theta = 0$, $\mathrm{d}\tilde{\varphi} = 0$。把式 (8-6-33) 用于其世界线的任一元段得
$$
\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[ 1 + \frac{2(\Psi_B - \Psi_0)}{c^2} \right]^{1/2} \mathrm{d}t \approx \left[ 1 + \frac{\Psi_B - \Psi_0}{c^2} \right] \mathrm{d}t = \mathrm{d}t.
$$
(8-6-34)  
（末步是因为 B 点在海平面保证 $\Psi_B = \Psi_0$。）上式说明，海平面上静止钟在 $\{t, r, \theta, \tilde{\varphi}\}$ 系的坐标时间 $\mathrm{d}t$ 等于其固有时间 $\mathrm{d}\tau$，而 $\mathrm{d}\tau$ 正是国际时间标准，可见新定义的坐标时间 $t$ 的重大优点：海平面上静止钟的 $t$ 就是国际标准时。文献中称此 $t$ 为 GPS 时间。

进一步，为了找出任一个钟（特别是卫星钟）的坐标时间 (GPS 时间) $\mathrm{d}t$ 与该钟固有时间 $\mathrm{d}\tau$ 的关系，可以利用式 (8-6-31) 和式 (8-6-32) 把史瓦西线元在 $\{\hat{t}, r, \theta, \varphi\}$ 系的表达式 (8-6-22) 变换为在 $\{t, r, \theta, \varphi\}$ 系的如下近似形式：
$$
\mathrm{d}s^2 = -\left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} \right] (c\,\mathrm{d}t)^2 + \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2).
$$
(8-6-35)  
也可改写为
$$
\mathrm{d}s^2 = -\left[ \left(1 + \frac{2(\Phi - \Psi_0)}{c^2}\right) - \left(1 - \frac{2\Phi}{c^2}\right) \frac{\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2}{(c\,\mathrm{d}t)^2} \right] (c\,\mathrm{d}t)^2.
$$
(8-6-36)  
令
$$
u \equiv \frac{ \sqrt{ \mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2 } }{ \mathrm{d}t }.
$$
(8-6-37)  
则 $u$ 是所论钟在 $\{t, r, \theta, \varphi\}$ 系的坐标速率。注意到式 (8-6-20)，便有  
式 (8-6-36) 方括号内第二大项 $\equiv -\left(1 - \frac{2\Phi}{c^2}\right) \frac{\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2}{(c\,\mathrm{d}t)^2} \approx -\frac{u^2}{c^2}$,  
于是式 (8-6-36) 近似成为
$$
\mathrm{d}s^2 = -\left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} - \frac{u^2}{c^2} \right] (c\,\mathrm{d}t)^2,
$$
(8-6-38)  
因而
$$
\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} - \frac{u^2}{c^2} \right]^{1/2} \mathrm{d}t \approx \left( 1 + \frac{\Phi - \Psi_0}{c^2} - \frac{u^2}{2c^2} \right) \mathrm{d}t.
$$
(8-6-39)  
也可反表为

> [!NOTE] 🖼️ Figure 描述  
> 图 8-12 地球略呈扁球状：三维透视示意图，球体赤道半径大于极半径。点 A 位于赤道面（$\theta_A = \pi/2$），点 B 位于北半球纬度圈；$r_A > r_B$，$l \equiv r \sin\theta$ 满足 $l_A > l_B$。从球心到 A 的线段标 $r_A$，到 B 的线段标 $r_B$；B 到赤道平面的垂足距离标 $l_B$；$r_B$ 与赤道平面夹角标 $\theta$。虚线表示赤道圈和纬度圈，实线表示可见半径和距离。

> [!WARNING] 🛡️ 原文勘误  
> 1. 坐标系符号修正：原文中 "$\{t, r, \theta, \varphi\}$" 应统一为 "$\{t, r, \theta, \tilde{\varphi}\}$"（参考 [P-1] 式 (8-6-26) 和 [N+1] 式 (8-6-40)），因 $\tilde{\varphi}$ 是包含地球自转的新坐标。  
> 2. 公式 (8-6-35) 修正：原文 "$\left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + \cdots \mathrm{d}\varphi^2)$" 中 $\varphi$ 应为 $\tilde{\varphi}$，与坐标系定义一致（[P-1] 式 (8-6-29) 明确使用 $\tilde{\varphi}$）。  
> 3. 术语统一：原文 "φ̃" 在 LaTeX 中应规范为 "\tilde{\varphi}"（[P-1] 和 [P-2] 均使用此符号）。

<CTX>
{ "summary": "本页推导 GPS 时间标准：通过坐标变换使海平面静止钟的坐标时间等于固有时间，定义 GPS 时间；建立卫星钟坐标时间与固有时间的微分关系，为后续修正计算奠定基础。", "keywords": ["GPS时间", "坐标变换", "固有时间", "坐标速率", "史瓦西线元"] }
</CTX>