# Slide 206

将上式沿图8-10(b)的光子世界线从 $p_i$ 点积分到 $q$ 点，由 $p_i=(t_i, r_i)$ 及 $q=(t, r)$ 可知变量 $r$ 的积分下、上限是 $r_i$ 和 $r$（因此宜将积分变量改记作 $r'$），得  
$$  
c(t - t_i) = \int_{r_i}^{r} \left(1 + \frac{\Psi_0}{c^2}\right) \mathrm{d}r' + \int_{r_i}^{r} \frac{2GM}{c^2} \frac{\mathrm{d}r'}{r'} = \left(1 + \frac{\Psi_0}{c^2}\right) (r - r_i) + \frac{2GM}{c^2} \ln \frac{r}{r_i}。  
\quad (8\text{-}6\text{-}49)  
$$  

上式中的 $r$ 是用户所在空间点的待求径向坐标，取决于该点的海拔高度，但在量级估算时不妨取 $r = R = 6.4 \times 10^6  \text{m}$。结合已知数据：  
$$  
\frac{GM}{c^2} = 4.43 \times 10^{-3}  \text{m} \quad \text{及} \quad r_i(\text{卫星径向坐标}) = 26.4 \times 10^6  \text{m}，  
$$  
可知  
$$  
\text{式}(8\text{-}6\text{-}49)\text{右边第二项} \equiv \frac{2GM}{c^2} \ln \frac{r}{r_i} \approx 2 \times (4.43 \times 10^{-3}  \text{m}) \times (-1.4) \approx -1.2  \text{cm}。  
\quad (8\text{-}6\text{-}50)  
$$  

另一方面，将式(8-6-28)用于赤道上的海平面得  
$$  
\frac{\Psi_0}{c^2} = \frac{\Phi(R)}{c^2} - \frac{(\Omega R)^2}{2c^2} = -\frac{GM}{c^2} \frac{1}{R} - \frac{u_{\phi}^2}{2c^2} = -\frac{4.43 \times 10^{-3}}{6.4 \times 10^6} - \frac{1}{2} \left( \frac{465}{3 \times 10^8} \right)^2 \approx -7 \times 10^{-10}。  
\quad (8\text{-}6\text{-}51)  
$$  

故  
$$  
\text{式}(8\text{-}6\text{-}49)\text{右边第一项} = (r - r_i) + (r - r_i) \frac{\Psi_0}{c^2} \approx r - r_i + (-2 \times 10^7)(-7 \times 10^{-10}) = r - r_i + 1.4 \times 10^{-2}  \text{m} = r - r_i + 1.4  \text{cm}，  
\quad (8\text{-}6\text{-}52)  
$$  

于是式(8-6-49)成为  
$$  
c(t - t_i) = r - r_i + 1.4  \text{cm} - 1.2  \text{cm} = r - r_i + 0.2  \text{cm}。  
\quad (8\text{-}6\text{-}53)  
$$  

目前GPS测距的最高精度虽然可达10 m左右，但0.2 cm仍可忽略。所以就有  
$$  
c(t - t_i) \approx r - r_i，  
\quad (8\text{-}6\text{-}54)  
$$  

这正是传播延迟方程(8-6-2)用于径向光子世界线的结果。非径向光子世界线虽然更为复杂，但也有类似结果。就是说，传播延迟方程(8-6-2)在GPS的要求精度内是近似成立的。请注意我们只说近似成立，而我们读到的文献则认为（至少强烈暗示）它准确成立。

[选读8-3 完]

> [!NOTE] 🖼️ Figure 描述  
> 图8-10(b) 展示光子世界线在径向坐标系中的几何结构：  
> - $p_i$ 点位于卫星轨道（径向坐标 $r_i = 26.4 \times 10^6  \text{m}$），对应发射时刻 $t_i$；  
> - $q$ 点位于用户位置（径向坐标 $r = R = 6.4 \times 10^6  \text{m}$），对应接收时刻 $t$；  
> - 光子世界线沿径向（$\mathrm{d}\theta = 0$, $\mathrm{d}\varphi = 0$）从 $p_i$ 到 $q$ 积分；  
> - 线元基于近似史瓦西度规，包含引力势 $\Phi$ 和常数 $\Psi_0$ 修正项；  
> - 积分路径需注意 $r < r_i$（用户低于卫星），导致 $\ln(r/r_i) < 0$。

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号一致性修正**：OCR 原文中式(8-6-51) 的 "$u_{\phi}^2$" 在 LaTeX 渲染时易与 $\nu$（希腊字母 nu）混淆。基于 [P-1] 页式(8-6-47) 和 [P-2] 页式(8-6-46) 的上下文（均使用 $u$ 表示线速率），统一修正为 $u_{\phi}$（$\phi$ 下标表示赤道方向速率），避免物理含义歧义。  
> 2. **逻辑补充**：式(8-6-52) 中 "$(-2 \times 10^7)$" 源于 $r - r_i \approx -2 \times 10^7  \text{m}$（卫星高度差），但原文未显式说明。已隐含在推导中，为保持严谨性，在 Markdown 中保留计算过程。

<CTX>
{
  "summary": "本页完成选读8-3，通过积分弯曲线元验证GPS传播延迟方程(8-6-2)在精度要求内的近似成立性：计算表明引力势与自转效应导致的0.2 cm修正可忽略，从而衔接前文对光速常数原理的质疑。核心在于证明$\\Psi_0$的常数性使纬度相关项抵消，且弯曲线元下光程近似平直。",
  "keywords": ["传播延迟方程", "GPS精度", "$\\Psi_0$常数性", "弯曲线元积分", "坐标奇性"]
}
</CTX>