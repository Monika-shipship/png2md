# Slide 201

§8.6 相对论在GPS(全球定位系统)中的应用

由式(8-6-29)可得：
\[
|\Psi| = \frac{GM}{r} + \frac{1}{2} \left( \Omega r \sin\theta \right)^2 \, .
\]
(8-6-30)

有一件事情很有趣，也很有用。由于自转，地球略呈扁球状——赤道半径较大而两极半径较小，如图8-12。把海平面的$\Psi$记作$\Psi_0$。如果地球是球体，则式(8-6-30)的$r=R$为常数，而$\theta$在海平面上不是常数，故$\Psi_0$不是常数。然而扁球状的地球改变了这种情况。设A, B是海平面的两点，$\theta_A = \pi/2$ (A在赤道面上)而$\theta_B \neq \pi/2$ (见图8-12)，则$r_A > r_B$。令$l \equiv r \sin\theta$，则$l_A > l_B$。而式(8-6-30)的$|\Psi|$是两项之和，不妨写成
\[
|\Psi| = \mu + \nu \, , \quad \text{其中} \ \mu \equiv \frac{GM}{r} \, , \quad \nu \equiv \frac{1}{2} (\Omega l)^2 \, .
\]
由$r_A > r_B$和$l_A > l_B$可知$\mu_A < \mu_B$，$\nu_A > \nu_B$，即$\mu$，$\nu$此消彼长。有趣的是，$\mu$，$\nu$的消长情况竟然如此凑巧，使得在GPS所要求的精度内可以认为$\Psi_A = \Psi_B$，因而可以认为$\Psi_0$ (海平面的$\Psi$)是常数。利用这一常数就可以给我们关心的整个时空区域定义一个新的时间坐标$t$:
\[
t \equiv \left(1 + \frac{\Psi_0}{c^2}\right) \hat{t} \, , \quad \text{即} \ \hat{t} = \left(1 + \frac{\Psi_0}{c^2}\right)^{-1} t \approx \left(1 - \frac{\Psi_0}{c^2}\right) t \, .
\]
(8-6-31)
(无论是否在海平面，其$t$都用上式定义。)由于$\Psi_0$是常数，上式无非是对时间尺度做一个常数性的伸缩，但很快就会看到这一简单的伸缩将带来巨大的好处。由式(8-6-31)得
\[
\mathrm{d}\hat{t}^2 = \left(1 - \frac{\Psi_0}{c^2}\right)^2 \mathrm{d}t^2 = \left(1 - \frac{2\Psi_0}{c^2} + \frac{\Psi_0^2}{c^4}\right) \mathrm{d}t^2 \approx \left(1 - \frac{2\Psi_0}{c^2}\right) \mathrm{d}t^2 \, ,
\]
(8-6-32)
故  
式(8-6-29)右边第一项 $= -\left(1 + \frac{2\Psi}{c^2}\right) c^2 \left(1 - \frac{2\Psi_0}{c^2}\right) \mathrm{d}t^2 \approx -\left[1 + \frac{2(\Psi - \Psi_0)}{c^2}\right] c^2 \mathrm{d}t^2$,  
于是史瓦西线元从表达式(8-6-29)变为在$\{t, r, \theta, \tilde{\varphi}\}$系的近似表达式
\[
\mathrm{d}s^2 = -\left[1 + \frac{2(\Psi - \Psi_0)}{c^2}\right] (c \mathrm{d}t)^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \mathrm{d}\tilde{\varphi} \mathrm{d}t + \left(1 - \frac{2\Phi}{c^2}\right) \left( \mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \mathrm{d}\tilde{\varphi}^2 \right) \, .
\]
(8-6-33)

> [!NOTE] 🖼️ Figure 描述  
> 图8-12：三维透视地球扁球体示意图。球体中心为球心，赤道半径大于极半径。球体表面有两条水平虚线：赤道圈（θ=π/2）和北半球纬度圈。点A位于赤道圈（实心点标注"A"），点B位于北半球纬度圈（实心点标注"B"）。从球心到A的实线标注"r_A"，到B的实线标注"r_B"。从B向赤道平面作垂线，垂足到球心距离标注"l_B"。球心处r_B与赤道平面夹角标注"θ"。图下方标题"图8-12 地球略呈扁球状"。所有线条为黑色，虚线表示不可见的赤道/纬度圈，实线表示可见半径和距离。

> [!WARNING] 🛡️ 原文勘误  
> 1. 符号修正：原文中"在 $\{t, r, \theta, \hat{\phi}\}$ 系"存在OCR错误，根据[P-1]页式(8-6-26)的坐标定义（$\tilde{\varphi} \equiv \varphi - \Omega \hat{t}$），应统一修正为$\tilde{\varphi}$（非$\hat{\phi}$）。  
> 2. 微分符号标准化：将原文"dt"、"dφ̃"等统一修正为$\mathrm{d}t$、$\mathrm{d}\tilde{\varphi}$以符合微分符号规范。  
> 3. 绝对值符号澄清：式(8-6-30)中$|\Psi|$正确（因$\Psi$为负值，$|\Psi|$表示引力势大小），但后续讨论$\Psi_0$时直接使用$\Psi$（如$\Psi_A = \Psi_B$），故保留$|\Psi|$仅在首次定义时使用，避免混淆。

<CTX>
{ "summary": "本页推导GPS时间坐标t的构建：通过地球扁球效应使海平面Ψ_0为常数，定义t=(1+Ψ_0/c²)ĥt，将史瓦西线元转换为新坐标系{t,r,θ,φ̃}，为卫星钟时间校准奠定基础。", "keywords": ["GPS时间坐标", "扁球地球效应", "Ψ_0常数", "坐标变换", "史瓦西线元"] }
</CTX>