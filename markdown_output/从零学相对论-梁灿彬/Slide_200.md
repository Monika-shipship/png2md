# Slide 200

因 $\mathrm{d}\varphi/\mathrm{d}\hat{t}$ 是该钟随地球自转而做圆周运动的角速率，故 $\hat{u}$ 就是它的线速率。把式(8-6-24)代入式(8-6-23)得
$$\mathrm{d}s^2 = -\left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2} + \frac{2\Phi(R)}{c^2} \cdot \frac{\hat{u}^2}{c^2}\right] (c\,\mathrm{d}\hat{t})^2 \approx -\left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2}\right] (c\,\mathrm{d}\hat{t})^2,$$
于是该钟世界线任一元段的固有时间为
$$\mathrm{d}\tau = \sqrt{\frac{-\mathrm{d}s^2}{c^2}} = \left[1 + \frac{2\Phi(R)}{c^2} - \frac{\hat{u}^2}{c^2}\right]^{1/2} \mathrm{d}\hat{t} \approx \left[1 + \frac{\Phi(R)}{c^2} - \frac{\hat{u}^2}{2c^2}\right] \mathrm{d}\hat{t} \neq \mathrm{d}\hat{t}.$$
(8-6-25)  
[其中第一步用到式(3-2-2')，末步再次用到 $(1+x)^{1/2} \approx 1+x/2$。] 地球上的时间标准是由海平面上的静止原子钟的固有时间定义的，这称为国际原子时间（International Atomic Time），而式(8-6-25)表明海平面上静止钟的坐标时间 $\mathrm{d}\hat{t}$ 不等于其固有时间 $\mathrm{d}\tau$，可见坐标时间 $\hat{t}$ 不符合国际时间标准。假定 GPS 用户从4个卫星信号求解而得自己收信的时刻竟然是坐标时间 $\hat{t}$，那就与国际时间对不上号，用 $\hat{t}$ 值的计算结果将使用户受骗上当。为了解决这一问题，有必要再做一次坐标变换，使新坐标包含地球自转的信息。为此，可以保持 $\hat{t}$, $r$, $\theta$ 不变而把 $\varphi$ 变为新坐标 $\tilde{\varphi}$，定义为
$$\tilde{\varphi} \equiv \varphi - \Omega \hat{t}, \quad (\Omega \text{ 是地球自转角速率})$$
(8-6-26)  
于是线元(8-6-22)在新坐标系 $\{\hat{t}, r, \theta, \tilde{\varphi}\}$ 中取如下形式：
$$\mathrm{d}s^2 = -\left[\left(1 + \frac{2\Phi}{c^2}\right) - \left(1 - \frac{2\Phi}{c^2}\right)\left(\frac{\Omega r \sin\theta}{c}\right)^2\right] (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t}$$
$$+ \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2) \approx$$
$$-\left[1 + \frac{2\Phi}{c^2} - \left(\frac{\Omega r \sin\theta}{c}\right)^2\right] (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t}$$
$$+ \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2).$$
(8-6-27)  
令
$$\Psi \equiv \Phi - \frac{1}{2} (\Omega r \sin\theta)^2,$$
(8-6-28)  
则
$$\mathrm{d}s^2 = -\left(1 + \frac{2\Psi}{c^2}\right) (c\,\mathrm{d}\hat{t})^2 + 2\left(1 - \frac{2\Phi}{c^2}\right) \Omega r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}\,\mathrm{d}\hat{t}$$
$$+ \left(1 - \frac{2\Phi}{c^2}\right) (\mathrm{d}r^2 + r^2 \mathrm{d}\theta^2 + r^2 \sin^2\theta \,\mathrm{d}\tilde{\varphi}^2).$$
(8-6-29)  
这是史瓦西线元在坐标系 $\{\hat{t}, r, \theta, \tilde{\varphi}\}$ 的近似表达式，其中的 $\Psi$ 由式(8-6-28)定义，由此式得

> [!NOTE] 🖼️ Figure 描述  
> 图8-12 地球略呈扁球状示意图。球体呈三维透视，赤道半径大于极半径。表面有两条水平虚线：赤道圈和北半球纬度圈。点A位于赤道圈（θ=π/2），实心点标注"A"；点B位于北半球纬度圈，实心点标注"B"。从球心到A的水平实线标"r_A"，到B的倾斜实线标"r_B"。从B向赤道平面作垂线，垂足到球心的距离标"l_B"。球心处r_B与赤道平面的夹角标"θ"。图下方标题为"图8-12 地球略呈扁球状"。所有线条为黑色，虚线表示不可见圈，实线表示可见半径和距离。

<CTX>
{ "summary": "本页推导GPS时间系统中坐标时间与固有时间的关系，通过坐标变换引入地球自转效应，定义新引力势Ψ以满足国际原子时间标准。核心是式(8-6-25)至(8-6-29)的线元变换过程。", "keywords": ["GPS时间系统", "坐标变换", "引力势Ψ", "国际原子时间", "固有时间"] }
</CTX>