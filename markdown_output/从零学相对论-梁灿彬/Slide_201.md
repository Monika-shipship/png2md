# Slide 201

§8.6 相对论在 GPS(全球定位系统)中的应用

\begin{equation}
|\Psi| = \frac{GM}{r} + \frac{1}{2} \left( \Omega r \sin\theta \right)^2 \, .
\end{equation}

有一件事情很有趣，也很有用。由于自转，地球略呈扁球状——赤道半径较大而两极半径较小，如图 8-12。把海平面的 $\Psi$ 记作 $\Psi_0$。如果地球是球体，则式(8-6-30)的 $r=R$ 为常数，而 $\theta$ 在海平面上不是常数，故 $\Psi_0$ 不是常数。然而扁球状的地球改变了这种情况。设 A、B 是海平面的两点，$\theta_A = \pi/2$ (A 在赤道面上)而 $\theta_B \neq \pi/2$ (见图 8-12)，则 $r_A > r_B$。令 $l \equiv r \sin\theta$，则 $l_A > l_B$。而式(8-6-30)的 $|\Psi|$ 是两项之和，不妨写成

\begin{equation*}
|\Psi| = \mu + \nu \, , \quad \text{其中} \ \mu \equiv \frac{GM}{r} \, , \quad \nu \equiv \frac{1}{2} (\Omega l)^2 \, .
\end{equation*}

由 $r_A > r_B$ 和 $l_A > l_B$ 可知 $\mu_A < \mu_B$，$\nu_A > \nu_B$，即 $\mu$、$\nu$ 此消彼长。有趣的是，$\mu$、$\nu$ 的消长情况竟然如此凑巧，使得在 GPS 所要求的精度内可以认为 $\Psi_A = \Psi_B$，因而可以认为 $\Psi_0$ (海平面的 $\Psi$)是常数。利用这一常数就可以给我们关心的整个时空区域定义一个新的时间坐标 $t$:

\begin{equation}
t \equiv \left(1 + \frac{\Psi_0}{c^2}\right) \hat{t} \, , \quad \text{即} \ \hat{t} = \left(1 + \frac{\Psi_0}{c^2}\right)^{-1} t \approx \left(1 - \frac{\Psi_0}{c^2}\right) t \, .
\end{equation}

(无论是否在海平面，其 $t$ 都用上式定义。)由于 $\Psi_0$ 是常数，上式无非是对时间尺度做一个常数性的伸缩，但很快就会看到这一简单的伸缩将带来巨大的好处。由式(8-6-31)得

\begin{equation}
\mathrm{d}\hat{t}^2 = \left(1 - \frac{\Psi_0}{c^2}\right)^2 \mathrm{d}t^2 = \left(1 - \frac{2\Psi_0}{c^2} + \frac{\Psi_0^2}{c^4}\right) \mathrm{d}t^2 \approx \left(1 - \frac{2\Psi_0}{c^2}\right) \mathrm{d}t^2 \, ,
\end{equation}

故式(8-6-29)右边第一项 $= -\left(1 + \frac{2\Psi}{c^2}\right) c^2 \left(1 - \frac{2\Psi_0}{c^2}\right) \mathrm{d}t^2 \approx -\left[1 + \frac{2(\Psi - \Psi_0)}{c^2}\right] c^2 \mathrm{d}t^2$，

于是史瓦西线元从表达式(8-6-29)变为在 $\{t, r, \theta, \tilde{\varphi}\}$ 系的近似表达式

\begin{equation}
\mathrm{d}s^2 = -\left[1 + \frac{2(\Psi - \Psi_0)}{c^2}\right] (c \mathrm{d}t)^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}t + 
\end{equation}
\begin{equation*}
\left(1 - \frac{2\Phi}{c^2}\right) \left( \mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2 \right) \, .
\end{equation*}

> [!NOTE] 🖼️ Figure 描述
> 三维透视地球扁球体示意图：球体赤道半径大于极半径。球心标记点，赤道处有水平虚线表示赤道圈，北半球有另一水平虚线表示纬度圈。点A位于赤道圈（$\theta_A = \pi/2$），标记"r_A"实线连接球心；点B位于北半球纬度圈，标记"r_B"实线连接球心，从B向赤道平面作垂线标记"l_B"。球心处r_B与赤道平面夹角标注"θ"。所有线条为黑色，虚线表示不可见圈，实线表示可见距离。底部标题"图8-12 地球略呈扁球状"。

> [!WARNING] 🛡️ 原文勘误
> 1. 符号修正：原文中坐标符号 $\hat{\phi}$ 应统一为 $\tilde{\varphi}$，与[P-1]页式(8-6-26)至(8-6-29)保持一致（前文使用 $\tilde{\varphi}$ 表示地球自转坐标系）
> 2. 公式编号：原文"式(8-6-30)"应明确标注在第一个方程，根据上下文推导顺序确认
> 3. 微分符号：原文"dt"应统一为正体 $\mathrm{d}t$，符合物理文献规范

<CTX>
{ "summary": "本节推导GPS时间坐标系的建立过程，通过地球扁球形修正使海平面$\Psi_0$为常数，并定义新时间坐标$t$以满足国际原子时间标准。关键步骤包括坐标变换和线元表达式转换。", "keywords": ["GPS时间坐标", "扁球地球修正", "$\Psi_0$常数性", "坐标变换", "线元表达式"] }
</CTX>