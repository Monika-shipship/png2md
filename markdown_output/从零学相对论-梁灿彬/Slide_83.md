# Slide 83

§4.3 双子效应（佯谬）  

$$\mathrm{d}s^2 = -c^2 \mathrm{d}t^2 + R^2 \mathrm{d}\varphi^2 \quad (4\text{-}3\text{-}10)$$  

因 $\mathrm{d}\varphi/\mathrm{d}t$ 是飞机的角速率，故飞机的线速率 $u = R \mathrm{d}\varphi/\mathrm{d}t$，代入上式得  
$$\mathrm{d}s^2 = -c^2 \mathrm{d}t^2 + u^2 \mathrm{d}t^2 = -\left(1 - \frac{u^2}{c^2}\right) c^2 \mathrm{d}t^2 \quad (4\text{-}3\text{-}11)$$  

上式无非是用 $u$ 代替式 $(4\text{-}3\text{-}3)$ 中的 $u_0$，所以，把 $C_0$ 线的环球时间表达式 $(4\text{-}3\text{-}7)$ 的 $u_0$ 改为 $u$ 便得 $C$ 线的环球时间（记作 $\tau$）：  
$$\tau = \left[1 - \frac{(u/c)^2}{2}\right] \hat{\tau} = \left[1 - \frac{(R\Omega + v)^2}{2c^2}\right] \hat{\tau} \quad (4\text{-}3\text{-}12)$$  
当 $v=0$ 时还原为  
$$\tau_0 = \left[1 - \frac{(R^2\Omega^2)}{2c^2}\right] \hat{\tau} = \left[1 - \frac{(u_0/c)^2}{2}\right] \hat{\tau} \quad (4\text{-}3\text{-}7')$$  
两式相减给出  
$$\tau - \tau_0 = -\frac{(2R\Omega v + v^2)}{2c^2} \hat{\tau} \quad (4\text{-}3\text{-}13)$$  
上式除以式 $(4\text{-}3\text{-}7')$ 得  
$$\frac{\tau - \tau_0}{\tau_0} = \frac{ - (2R\Omega v + v^2) / 2c^2 }{ 1 - (R^2\Omega^2 / 2c^2) } \quad (4\text{-}3\text{-}14)$$  
上式右边分母  
$$1 - (R^2\Omega^2 / 2c^2) = 1 - (u_0 / c)^2 / 2 \approx 1 - 10^{-12} \approx 1,$$  
[其中第二步用到式 $(4\text{-}3\text{-}5)$。] 所以式 $(4\text{-}3\text{-}14)$ 可简化为  
$$(\tau - \tau_0) / \tau_0 \approx - (2R\Omega v + v^2) / 2c^2,$$  
于是  
$$\tau - \tau_0 = - (2R\Omega v + v^2) \tau_0 / 2c^2 \quad (4\text{-}3\text{-}15)$$  
可见，当 $v>0$（东飞）时 $\tau < \tau_0$，即环球时间比地面惯性参考钟经历的时间短（“丢失时间”）；当 $v<0$（西飞）而且 $|v| \approx R\Omega$ 时 $\tau > \tau_0$，即环球时间比地面钟的时间长（“赢得时间”）。  

除了地球有自转外，地球引力场也会带来可观测的影响。飞机与地面的高度差造成引力势差，根据广义相对论，其影响体现为一个附加项，式 $(4\text{-}3\text{-}15)$ 要改为  
$$\tau - \tau_0 = \left[2gh - (2R\Omega v + v^2)\right] \tau_0 / 2c^2 \quad (4\text{-}3\text{-}16)$$  
其中 $h \ll R$ 是飞行高度，$g$ 是地面重力加速度（详细推证见第 8 章选读 8-1）。上式就是从狭义相对论和广义相对论出发求得的时间差。在与实验数据对比之前还要考虑一系列实际情况，例如，出于经济考虑而采用商用飞机，而商用飞机并不在赤道正上空飞行，其纬度、高度和速度在飞行期间也不保持常数。考虑所有这些因素后得到一个修正公式，由此可求得飞行钟与地面惯性参考钟的时间差的理论预言值：东飞钟为 $(40 \pm 23) \times 10^{-9}  \mathrm{s}$，西飞钟为 $(275 \pm 21) \times 10^{-9}  \mathrm{s}$。  

实际飞行是在 1971 年 10 月进行的。第一次为东飞，持续时间为 65.4 小时，其中飞行时间是 41.2 小时；第二次（约一周后）为西飞，持续时间为 80.3 小时。

> [!WARNING] 🛡️ 原文勘误  
> - 原文 `(2R\Omega v + v^2) / 2c^2 / \hat{\tau}`（式 $(4\text{-}3\text{-}13)$）存在语法错误：分母重复 `/` 且 `\hat{\tau}` 位置错误。根据前页公式 $(4\text{-}3\text{-}8)$ 和物理逻辑（时间差应正比于 $\hat{\tau}$），修正为 `-\frac{(2R\Omega v + v^2)}{2c^2} \hat{\tau}`。  
> - 原文 `v = R\Omega` 时 $u = 0$ 的描述需澄清：根据前页选读 4-5，$v < 0$ 代表西飞，故 $v = -R\Omega$ 时 $u = 0$（飞机抵消地球自转）。已补充括号说明以确保符号一致性。

<CTX>
{ "summary": "本页定量分析双子效应中的环球飞行时间差，推导东飞/西飞的钟差公式（含狭义与广义相对论修正），并给出1971年Hafele-Keating实验的理论预言值。核心是公式(4-3-15)和(4-3-16)的建立与简化。", "keywords": ["双子效应", "环球飞行时间差", "Hafele-Keating实验", "狭义相对论", "广义相对论修正"] }
</CTX>