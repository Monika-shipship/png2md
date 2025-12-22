# Slide 206

将上式沿图8-10(b)的光子世界线从 $p_i$ 点积分到 $q$ 点，由 $p_i=(t_i, r_i)$ 及 $q=(t, r)$ 可知变量 $r$ 的积分下、上限是 $r_i$ 和 $r$（因此宜将积分变量改记作 $r'$），得  
$$  
c(t - t_i) = \int_{r_i}^{r} \left(1 + \frac{\Psi_0}{c^2}\right) \mathrm{d}r' + \int_{r_i}^{r} \frac{2GM}{c^2} \frac{\mathrm{d}r'}{r'} = \left(1 + \frac{\Psi_0}{c^2}\right) (r - r_i) + \frac{2GM}{c^2} \ln \frac{r}{r_i}.  
$$  
(8-6-49)  

上式中的 $r$ 是用户所在空间点的待求径向坐标，取决于该点的海拔高度，但在量级估算时不妨取 $r = R = 6.4 \times 10^6  \text{m}$。结合已知数据：  
$$  
\frac{GM}{c^2} = 4.43 \times 10^{-3}  \text{m} \quad \text{及} \quad r_i (\text{卫星径向坐标}) = 26.4 \times 10^6  \text{m},  
$$  
可知  
$$  
\text{式}(8\text{-}6\text{-}49)\text{右边第二项} \equiv \frac{2GM}{c^2} \ln \frac{r}{r_i} \approx 2 \times (4.43 \times 10^{-3}  \text{m}) \times (-1.4) \approx -1.2  \text{cm}.  
$$  
(8-6-50)  

另一方面，将式(8-6-28)用于赤道上的海平面得  
$$  
\frac{\Psi_0}{c^2} = \frac{\Phi(R)}{c^2} - \frac{(\Omega R)^2}{2c^2} = -\frac{GM}{c^2} \frac{1}{R} - \frac{u_{\phi}^2}{2c^2} = -\frac{4.43 \times 10^{-3}}{6.4 \times 10^6} - \frac{1}{2} \left( \frac{465}{3 \times 10^8} \right)^2 \approx -7 \times 10^{-10}.  
$$  
(8-6-51)  

故  
$$  
\text{式}(8\text{-}6\text{-}49)\text{右边第一项} = (r - r_i) + (r - r_i) \frac{\Psi_0}{c^2} \approx r - r_i + (-2 \times 10^7) \times (-7 \times 10^{-10}) = r - r_i + 1.4 \times 10^{-2}  \text{m} = r - r_i + 1.4  \text{cm},  
$$  
(8-6-52)  

于是式(8-6-49)成为  
$$  
c(t - t_i) = r - r_i + 1.4  \text{cm} - 1.2  \text{cm} = r - r_i + 0.2  \text{cm}.  
$$  
(8-6-53)  

目前 GPS 测距的最高精度虽然可达 10 m 左右，但 0.2 cm 仍可忽略。所以就有  
$$  
c(t - t_i) \approx r - r_i,  
$$  
(8-6-54)  

这正是传播延迟方程(8-6-2)用于径向光子世界线的结果。非径向光子世界线虽然更为复杂，但也有类似结果。就是说，传播延迟方程(8-6-2)在 GPS 的要求精度内是近似成立的。请注意我们只说近似成立，而我们读到的文献则认为（至少强烈暗示）它准确成立。  

> [!NOTE] 🖼️ Figure 描述  
> 图8-10(b)：光子世界线示意图，展示从卫星发射点 $p_i = (t_i, r_i)$（$r_i \approx 26.4 \times 10^6  \text{m}$）到用户接收点 $q = (t, r)$（$r \approx 6.4 \times 10^6  \text{m}$）的径向传播路径，沿 $r$ 坐标递减方向（$r_i > r$）积分。  

[选读8-3 完]  

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号统一修正**：前文 [P-1] 中明确使用 $u_{\phi}$ 表示赤道线速率（见式(8-6-44)及上下文），而 [Target] 中 " $u_{\phi}^2$ " 的 OCR 识别正确，但为确保一致性，所有线速率符号统一为 $u$（如 $u_{\phi}$ 而非 $\nu_{\phi}$），避免与频率符号混淆。  
> 2. **逻辑补全**：式(8-6-51)中 " $\frac{(\Omega R)^2}{2c^2}$ " 实为 $u_{\phi} = \Omega R$ 的简化表达（$\Omega$ 为地球自转角速率），根据 [P-2] 页 " $u_{\text{赤}} = 465  \text{m/s} $" 及 [P-1] 页 " $u \equiv \Omega r \sin \theta $ "，此处特指赤道 $\theta = \pi/2$ 时的 $u_{\phi}$，故保留原符号无误。  
> 3. **量级修正**：式(8-6-52)计算中 "$ (-2 \times 10^7) $" 源于 $r - r_i \approx 6.4 \times 10^6 - 26.4 \times 10^6 = -2 \times 10^7  \text{m} $，OCR 数据无误，但为明确物理意义，补充说明此为高度差负值（卫星高于用户）。  

<CTX>  
{ "summary": "本页通过积分光子世界线验证GPS传播延迟方程的近似有效性，计算显示相对论修正项（1.4 cm与-1.2 cm）在GPS精度下抵消为0.2 cm，可忽略，故 $c(t - t_i) \\approx r - r_i$ 成立。核心在于统一处理引力与运动效应，强调文献中'光速严格不变'的表述仅适用于近似场景。", "keywords": ["传播延迟方程", "GPS相对论修正", "光子世界线积分", "坐标奇性", "史瓦西时空"] }  
</CTX>