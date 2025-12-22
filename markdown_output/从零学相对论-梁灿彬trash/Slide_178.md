# Slide 166

式(4-3-5)已证明 $ u_0^2 / c^2 \ll 1 $。利用地球数据及物理常数（均指国际单位制数值）：
$$
M = 6 \times 10^{24}, \quad R = 6.4 \times 10^{6}, \quad G = 6.7 \times 10^{-11}, \quad c = 3 \times 10^{8} \tag{8-3-22}
$$
易知赤道引力势 $\Phi_0$ 满足：
$$
\frac{|\Phi_0|}{c^2} = \frac{GM}{c^2 R} = \frac{(6.7 \times 10^{-11}) \times (6 \times 10^{24})}{(3 \times 10^{8})^2 \times (6.4 \times 10^{6})} \approx 7 \times 10^{-10} \ll 1, \tag{8-3-23}
$$
令 $ x \equiv \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2} $，则 $ x \ll 1 $。应用牛顿二项式定理 $ (1+x)^{1/2} \approx 1 + x/2 $，可将式(8-3-21)简化为：
$$
\mathrm{d}\tau_0 \approx \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) \mathrm{d}t. \tag{8-3-24}
$$
将上式沿 $ C_0 $ 线（见图4-22）全程积分得：
$$
\tau_0 = \int_{0}^{t_q} \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) \mathrm{d}t = \left( 1 + \frac{\Phi_0}{c^2} - \frac{u_0^2}{2c^2} \right) t_q. \tag{8-3-25}
$$
再讨论赤道上空任意 $ C $ 线（$ v $ 值任意），其与 $ C_0 $ 线存在两点差异：  
① $ C_0 $ 线位于赤道表面（引力势 $\Phi_0 \equiv \Phi(R)$），而 $ C $ 线（飞机）位于离地 $ h $ 米高度（引力势 $\Phi \equiv \Phi(R+h)$）；  
② $ C_0 $ 线代表固结于赤道的钟（满足 $\mathrm{d}\varphi = \Omega \mathrm{d}t$，线速率 $u_0 = R\Omega$），而 $ C $ 线为飞行钟（线速率 $u = (R+h) \, \mathrm{d}\varphi / \mathrm{d}t$）。  
因此，式(8-3-18)应用于 $ C $ 线元段得：
$$
\begin{aligned}
\mathrm{d}s^2 &= -\left( 1 + \frac{2\Phi}{c^2} \right) c^2 \mathrm{d}t^2 + (R+h)^2 \mathrm{d}\varphi^2 \\
&= -\left( 1 + \frac{2\Phi}{c^2} \right) c^2 \mathrm{d}t^2 + u^2 \mathrm{d}t^2 \\
&= -\left( 1 + \frac{2\Phi}{c^2} - \frac{u^2}{c^2} \right) c^2 \mathrm{d}t^2,
\end{aligned} \tag{8-3-26}
$$
将 $\Phi$ 和 $u$ 代入式(8-3-25)得 $ C $ 线环球飞行时间：
$$
\tau = \left( 1 + \frac{\Phi}{c^2} - \frac{u^2}{2c^2} \right) t_q. \tag{8-3-27}
$$
联立式(8-3-27)与(8-3-25)得：
$$
\tau - \tau_0 = \left( \frac{\Phi - \Phi_0}{c^2} - \frac{u^2 - u_0^2}{2c^2} \right) t_q. \tag{8-3-28}
$$
其中 $\Phi - \Phi_0$ 由式(8-3-17)及(8-3-20)计算：
$$
\Phi - \Phi_0 = -\frac{GM}{R+h} - \left( -\frac{GM}{R} \right) = \frac{GMh}{R(R+h)} \approx \frac{GMh}{R^2} = gh, \tag{8-3-29}
$$
此处 $ g = GM / R^2 $ 为地面重力加速度。代入式(8-3-28)得：
$$
\tau - \tau_0 = \left( \frac{gh}{c^2} - \frac{u^2 - u_0^2}{2c^2} \right) t_q.
$$

> [!NOTE] 🖼️ Figure 4-22 几何关系
> 该图展示赤道平面上的两条世界线：  
> - $ C_0 $：固结于赤道表面的钟（$ r = R $, $ \mathrm{d}\varphi = \Omega \mathrm{d}t $）  
> - $ C $：赤道上空飞行钟（$ r = R + h $, $ \mathrm{d}\varphi / \mathrm{d}t = \Omega + v / (R + h) $）  
> 两世界线在赤道平面投影为同心圆，$ C $ 线半径大于 $ C_0 $ 线，$ v $ 表示飞行钟相对地球自转的切向速度。

> [!WARNING] 🛡️ 原文勘误
> 1. OCR 误将 "d" 识别为 "0"：  
>    - 原文 "$\mathrm{d}s_0^2$" → 修正为 "$\mathrm{d}s^2$"（式8-3-26）  
>    *依据*：P-1 页式(8-3-19)及 N+1 页均使用 $\mathrm{d}s^2$，且下标 0 仅用于 $C_0$ 线  
> 2. 符号混淆修正：  
>    - 原文 "$\mathrm{d}t_0$" → 修正为 "$\mathrm{d}t$"（式8-3-24）  
>    *依据*：P-1 页式(8-3-21)使用 $\mathrm{d}t$，且 $t$ 为史瓦西坐标时间  
> 3. 逻辑衔接补充：  
>    - 补充 "$v$ 表示飞行钟相对地球自转的切向速度"  
>    *依据*：P-2 页选读8-1明确 $v$ 为飞机东飞速度，N+1 页式(8-3-31)使用 $u = R\Omega + v$

<CTX>
{ "summary": "本页推导地球引力场中飞行钟与地面钟的时间差公式，通过史瓦西度规结合地球自转效应，建立 $\tau - \tau_0$ 与引力势差、线速率差的定量关系，为验证广义相对论提供理论基础", "keywords": ["史瓦西度规", "引力钟慢", "地球自转", "线速率", "引力势差"] }
</CTX>