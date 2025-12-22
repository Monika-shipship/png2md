# Slide 202

再次考虑静止在海平面B点的钟，它在新坐标系$\{t, r, \theta, \tilde{\varphi}\}$的坐标自动满足$r$, $\theta$, $\tilde{\varphi}=$常数（因它随地球自转而动），故$\mathrm{d}r=0$, $\mathrm{d}\theta=0$, $\mathrm{d}\tilde{\varphi}=0$。把式(8-6-33)用于其世界线的任一元段得  
$$\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[ 1 + \frac{2(\Psi_B - \Psi_0)}{c^2} \right]^{1/2} \mathrm{d}t \approx \left[ 1 + \frac{\Psi_B - \Psi_0}{c^2} \right] \mathrm{d}t = \mathrm{d}t.$$  
(8-6-34)  
（末步是因为B点在海平面保证$\Psi_B = \Psi_0$。）上式说明，海平面上静止钟在$\{t, r, \theta, \tilde{\varphi}\}$系的坐标时间$\mathrm{d}t$等于其固有时间$\mathrm{d}\tau$，而$\mathrm{d}\tau$正是国际时间标准，可见新定义的坐标时间$t$的重大优点：海平面上静止钟的$t$就是国际标准时。文献中称此$t$为GPS时间。  

进一步，为了找出任一个钟（特别是卫星钟）的坐标时间(GPS时间)$\mathrm{d}t$与该钟固有时间$\mathrm{d}\tau$的关系，可以利用式(8-6-31)和式(8-6-32)把史瓦西线元在$\{\hat{t}, r, \theta, \varphi\}$系的表达式(8-6-22)变换为在$\{t, r, \theta, \varphi\}$系的如下近似形式：  
$$\mathrm{d}s^2 = -\left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} \right] (c\,\mathrm{d}t)^2 + \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2).$$  
(8-6-35)  

也可改写为  
$$\mathrm{d}s^2 = -\left[ \left(1 + \frac{2(\Phi - \Psi_0)}{c^2}\right) - \left(1 - \frac{2\Phi}{c^2}\right) \frac{\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2}{(c\,\mathrm{d}t)^2} \right] (c\,\mathrm{d}t)^2.$$  
(8-6-36)  

令  
$$u \equiv \frac{ \sqrt{ \mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2 } }{ \mathrm{d}t }.$$  
(8-6-37)  

则$u$是所论钟在$\{t, r, \theta, \varphi\}$系的坐标速率。注意到式(8-6-20)，式(8-6-36)方括号内第二大项可近似为  
$$-\left(1 - \frac{2\Phi}{c^2}\right) \frac{\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2 \theta \,\mathrm{d}\varphi^2}{(c\,\mathrm{d}t)^2} \approx -\frac{u^2}{c^2},$$  

于是式(8-6-36)近似成为  
$$\mathrm{d}s^2 = -\left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} - \frac{u^2}{c^2} \right] (c\,\mathrm{d}t)^2,$$  
(8-6-38)  

因而  
$$\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[ 1 + \frac{2(\Phi - \Psi_0)}{c^2} - \frac{u^2}{c^2} \right]^{1/2} \mathrm{d}t \approx \left( 1 + \frac{\Phi - \Psi_0}{c^2} - \frac{u^2}{2c^2} \right) \mathrm{d}t.$$  
(8-6-39)  

也可反表为  

> [!NOTE] 🖼️ Figure 描述  
> 三维透视的地球扁球体示意图，中心为球心。球体赤道半径大于极半径，呈扁球状。表面有两条水平虚线：赤道圈和北半球纬度圈。点A（赤道圈，实心点）标注$r_A$，点B（纬度圈，实心点）标注$r_B$。球心到A的水平实线标$r_A$，到B的倾斜实线标$r_B$；B向赤道平面的垂线标$l_B$。球心处$r_B$与赤道平面的夹角弧线标$\theta$。标题：图8-12 地球略呈扁球状。线条全黑，无填充，虚线表不可见圈，实线表可见半径。

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号修正**：Target中"$\phĩ$"应统一为$\tilde{\varphi}$（与P-1中$\hat{\phi}$符号体系一致，tilde phi在LaTeX中为`\tilde{\varphi}`）。  
> 2. **公式逻辑**：式(8-6-36)末句"注意到式(8-6-20)"在上下文中无直接引用，但P-2中(8-6-20)定义$u$为坐标速率，此处保留以维持推导连贯性。  
> 3. **OCR错误**：Target中"$\Psi_B = \Psi_0$"误识别为"Ψ_B = Ψ_0"，修正为$\Psi_B = \Psi_0$以匹配P-1的符号规范。

<CTX>
{ "summary": "本页核心论证GPS时间$t$的物理意义：通过坐标变换使海平面静止钟的$\mathrm{d}t$等于固有时间$\mathrm{d}\\tau$，推导出任意钟的GPS时间与固有时间的微分关系(8-6-39)，为卫星钟修正奠定基础。关键点包括$\\Psi_0$常数性的应用及坐标速率$u$的引入。", "keywords": ["GPS时间", "固有时间", "坐标变换", "$\\Psi_0$常数性", "坐标速率"] }
</CTX>