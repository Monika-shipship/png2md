# Slide 200

因 $\mathrm{d}\varphi/\mathrm{d}\hat{t}$ 是钟随地球自转的角速率，故 $\hat{u}$ 即为其线速率。将式(8-6-24)代入式(8-6-23)得：
$$\mathrm{d}s^2 = -\left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2} + \frac{2\Phi(R)}{c^2} \cdot \frac{\hat{u}^2}{c^2}\right] (c\,\mathrm{d}\hat{t})^2 \approx -\left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2}\right] (c\,\mathrm{d}\hat{t})^2,$$
该钟世界线元段的固有时间为：
$$\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2}\right]^{1/2} \mathrm{d}\hat{t} \approx \left[1 + \frac{\Phi(R)}{c^2} - \frac{\hat{u}^2}{2c^2}\right] \mathrm{d}\hat{t} \neq \mathrm{d}\hat{t}.$$
(8-6-25)  
[注：第一步应用式(3-2-2')，末步利用 $(1+x)^{1/2} \approx 1+x/2$ 近似。]  

地球时间标准由海平面静止原子钟的固有时间定义（国际原子时间），而式(8-6-25)表明海平面静止钟的坐标时间 $\mathrm{d}\hat{t}$ 不等于其固有时间 $\mathrm{d}\tau$，故坐标时间 $\hat{t}$ 不符合国际标准。若GPS用户将卫星信号解算的时刻视为坐标时间 $\hat{t}$，将导致时间系统错位。为解决此问题，需进行坐标变换以纳入地球自转效应。保持 $\hat{t}$, $r$, $\theta$ 不变，将 $\varphi$ 变换为新坐标 $\tilde{\varphi}$：
$$\tilde{\varphi} \equiv \varphi - \Omega \hat{t}, \quad (\Omega \text{ 为地球自转角速率})$$
(8-6-26)  
线元(8-6-22)在新坐标系 $\{\hat{t}, r, \theta, \tilde{\varphi}\}$ 中的表达式为：
$$\mathrm{d}s^2 = -\left[\left(1 + \frac{2\Phi}{c^2}\right) - \left(1 - \frac{2\Phi}{c^2}\right)\left(\frac{\Omega r \sin\theta}{c}\right)^2\right] (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t}$$
$$+ \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2) \approx -\left[1 + \frac{2\Phi}{c^2} - \left(\frac{\Omega r \sin\theta}{c}\right)^2\right] (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t}$$
$$+ \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2).$$
(8-6-27)  
定义新势函数：
$$\Psi \equiv \Phi - \frac{1}{2} (\Omega r \sin\theta)^2,$$
(8-6-28)  
则线元简化为：
$$\mathrm{d}s^2 = -\left(1 + \frac{2\Psi}{c^2}\right) (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t} + \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2).$$
(8-6-29)  
此即史瓦西线元在 $\{\hat{t}, r, \theta, \tilde{\varphi}\}$ 系的近似表达式，其中 $\Psi$ 由式(8-6-28)定义。

> [!NOTE] 🖼️ Figure 8-12 描述  
> 三维透视地球扁球体示意图：球体赤道半径大于极半径，表面有两条水平虚线（赤道圈和北半球纬度圈）。点A（赤道）和点B（北半球）以实心点标记；从球心到A的水平实线标 $r_A$，到B的倾斜实线标 $r_B$；B向赤道平面的垂线标 $l_B$；$r_B$ 与赤道平面夹角标 $\theta$。标题“图8-12 地球略呈扁球状”，全图黑线无填充。

> [!WARNING] 🛡️ 原文勘误  
> 1. 公式(8-6-25)末尾符号：原文为 `≠ \mathrm{d}\hat{t}。` 修正为 `≠ \mathrm{d}\hat{t}.`（句号应为英文标点）  
> 2. 符号一致性：[P-1] 页式(8-6-24)定义 $\hat{u} \equiv R \sin\theta_{\mathrm{B}} \frac{\mathrm{d}\varphi}{\mathrm{d}\hat{t}}$，[Target] 页保持 $\hat{u}$ 而非 $\nu$（避免与后文 $\nu \equiv \frac{1}{2} (\Omega l)^2$ 混淆）  
> 3. 逻辑衔接：补充"线元(8-6-22)"明确引用来源（见[P-1]页末公式）

<CTX>
{ "summary": "本页推导海平面钟的固有时间与坐标时间关系，指出坐标时间$\hat{t}$不符合国际原子时间标准，进而引入含地球自转的坐标变换$\tilde{\varphi} = \varphi - \Omega \hat{t}$，导出新坐标系下史瓦西线元的简化表达式，并定义有效势$\Psi$。", "keywords": ["坐标时间", "固有时间", "地球自转", "势函数$\Psi$", "GPS时间系统"] }
</CTX>