# Slide 203

§8.6 相对论在 GPS(全球定位系统)中的应用

从式(8-6-39)可反解出坐标时间微分与固有时间微分的关系：

$$
\mathrm{d}t = \left(1 + \frac{\Phi - \Psi_0}{c^2} - \frac{u^2}{2c^2}\right)^{-1} \mathrm{d}\tau \approx \left(1 - \frac{\Phi - \Psi_0}{c^2} + \frac{u^2}{2c^2}\right) \mathrm{d}\tau \quad (8-6-39')
$$

这就是任一钟的 GPS 时间 $t$ 与固有时间 $\tau$ 的微分关系。将此式用于卫星钟，以 $\mu$ 代表卫星钟世界线上我们关心的一段。由于卫星高度 $r_{\text{卫}}$ 及速率 $u_{\text{卫}}$ 近似为常数，沿 $\mu$ 段积分得：

$$
\int_{\mu} \mathrm{d}t = \int_{\mu} \mathrm{d}\tau_{\text{卫}} - \left( \frac{\Phi_{\text{卫}} - \Psi_0}{c^2} - \frac{u_{\text{卫}}^2}{2c^2} \right) \int_{\mu} \mathrm{d}\tau_{\text{卫}} \quad (8-6-40)
$$

令 $\Delta t \equiv \int_{\mu} \mathrm{d}t$，$\Delta \tau_{\text{卫}} \equiv \int_{\mu} \mathrm{d}\tau_{\text{卫}}$，$(\Delta t)_{\text{修}} \equiv - \left( \frac{\Phi_{\text{卫}} - \Psi_0}{c^2} - \frac{u_{\text{卫}}^2}{2c^2} \right) \Delta \tau_{\text{卫}}$，则：

$$
\Delta t = \Delta \tau_{\text{卫}} + (\Delta t)_{\text{修}} \quad (8-6-42)
$$

卫星经历的 GPS 时间 $\Delta t$ 之所以不等于其固有时间 $\Delta \tau_{\text{卫}}$，正是因为上式右边多了修正项 $(\Delta t)_{\text{修}}$。现在可以明确指出：传播延迟方程(8-6-2)中的 $t$ 和 $t_i$ 均为 $\{t, r, \theta, \varphi\}$ 系的坐标时（即 GPS 时）。因此，从卫星钟读出固有时间 $\Delta \tau_{\text{卫}}$ 后，必须先加上 $(\Delta t)_{\text{修}}$ 以转换为 GPS 时间 $\Delta t$，再发出信号。信号应包含发信时的 GPS 时刻 $t_i$ 以及卫星在此时的空间坐标 $r_i, \theta_i, \varphi_i$ 等内容，以便用户求解传播延迟方程(8-6-2)，最终确定自身的时空坐标 $t, r, \theta, \varphi$，实现定时定位功能。此处的 $t$ 即用户收信时的 GPS 时刻，与国际标准时间完全一致。

为将式(8-6-41)的 $(\Delta t)_{\text{修}}$ 与选读前的两个相对论效应（效应1和效应2）进行对比，需先明确相关物理量。由式(8-6-18)有：

$$
\frac{\Phi_{\text{卫}}}{c^2} = - \frac{GM}{c^2} \frac{1}{r_{\text{卫}}} \quad (8-6-43)
$$

常数 $\Psi_0$ 可通过赤道点 A 计算。结合式(8-6-28)和式(8-6-18)得：

$$
\frac{\Psi_0}{c^2} = \frac{\Psi|_A}{c^2} = \frac{\Phi|_A}{c^2} - \frac{(\Omega R \sin \theta_A)^2}{2c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{(\Omega R)^2}{2c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{u_{\text{赤}}^2}{2c^2} \quad (8-6-44)
$$

其中 $R_{\text{赤}}$ 为赤道半径，$u_{\text{赤}}$ 是海平面赤道处静止钟随地球自转的线速率（注意：此处 $u$ 统一使用拉丁字母表示速度，与 P-1 页式(8-6-37)定义一致，避免与 P-2 页势能项 $\nu$ 混淆）。将式(8-6-43)和(8-6-44)代入式(8-6-41)得：

$$
(\Delta t)_{\text{修}} = \left[ \frac{GM}{c^2} \left( \frac{1}{r_{\text{卫}}} - \frac{1}{R_{\text{赤}}} \right) + \frac{u_{\text{卫}}^2 - u_{\text{赤}}^2}{2c^2} \right] \Delta \tau_{\text{卫}} \quad (8-6-45)
$$

设 $\Delta \tau_{\text{赤}}$ 为赤道钟在坐标时间 $\Delta t$ 内经历的固有时间。定量计算表明 $\Delta \tau_{\text{赤}}$ 与 $\Delta \tau_{\text{卫}}$ 的相对差异量级为 $10^{-10}$，因此式(8-6-45)可进一步简化为：

> [!NOTE] 🖼️ Figure 8-12: 地球略呈扁球状  
> 图位于页面右侧，三维透视地球扁球体示意图。球体占据主要区域，中心标有球心点。赤道半径明显大于极半径，呈现扁球状特征。球体表面有两条水平虚线：赤道位置的虚线表示赤道圈，北半球虚线表示某纬度圈。点A（实心点，标注"A"）位于赤道圈上；点B（实心点，标注"B"）位于北半球纬度圈上。从球心到A的水平实线标注"$r_A$"，到B的倾斜实线标注"$r_B$"。从B向赤道平面作垂线，垂足到球心的水平实线标注"$l_B$"。球心处$r_B$与赤道平面的夹角用弧线标注"$\theta$"。图下方标题为"图8-12 地球略呈扁球状"。所有线条为黑色，无填充色；虚线表示不可见轮廓，实线表示可见半径和距离。

> [!WARNING] 🛡️ 原文勘误  
> 原文式(8-6-44)中 "$- \frac{(\Omega R)^2}{2c^2}$" 应为 "$- \frac{(\Omega R_{\text{赤}})^2}{2c^2}$"（下标缺失）。根据图8-12描述及物理一致性，$R$ 应明确为赤道半径 $R_{\text{赤}}$，否则与后文 $R_{\text{赤}}$ 定义矛盾。修正后：  
> $\frac{\Psi_0}{c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{(\Omega R_{\text{赤}})^2}{2c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{u_{\text{赤}}^2}{2c^2}$

<CTX>
{ "summary": "本页推导GPS时间与固有时间的转换关系，建立卫星钟修正项(Δt)ₘ的显式表达式，并揭示其与广义相对论效应（引力势差）和狭义相对论效应（运动速率差）的定量关联。关键创新在于利用地球扁球特性使Ψ₀为常数，实现两种效应的代数叠加。", "keywords": ["GPS时间", "固有时间", "相对论修正", "扁球地球", "引力钟慢"] }
</CTX>