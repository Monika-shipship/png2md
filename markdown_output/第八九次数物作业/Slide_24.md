# Slide 23  
**18. 勒让德多项式 $P_l(t)$ 的路径参数化与具体计算**  

承接 Slide 22 的 Schläfli 积分表示 $P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{(z^2 - 1)^l}{(z - t)^{l+1}}  dz$，现通过路径参数化计算具体表达式。  
令 $t = \cos\theta$，选择积分路径为以 $t = \cos\theta$ 为圆心、$\sqrt{1 - t^2} = \sin\theta$ 为半径的圆周（$0 < \theta < \pi$），则：  
$$
z = \cos\theta + \sin\theta  e^{i\varphi}, \quad dz = i \sin\theta  e^{i\varphi}  d\varphi, \quad \varphi \in [-\pi, \pi].
$$  
代入积分式并化简：  
$$
\begin{aligned}
P_l(\cos\theta) &= \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[(\cos\theta + \sin\theta  e^{i\varphi})^2 - 1]^l}{(\sin\theta  e^{i\varphi})^{l+1}} \cdot i \sin\theta  e^{i\varphi}  d\varphi \\
&= \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[\cos^2\theta + 2\cos\theta\sin\theta  e^{i\varphi} + \sin^2\theta  e^{2i\varphi} - 1]^l}{(\sin\theta  e^{i\varphi})^l}  d\varphi \\
&= \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[\sin^2\theta (e^{2i\varphi} - 1) + 2\cos\theta\sin\theta  e^{i\varphi}]^l}{(\sin\theta  e^{i\varphi})^l}  d\varphi \quad (\text{利用 } \cos^2\theta - 1 = -\sin^2\theta) \\
&= \frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} \left( -\sin\theta  e^{-i\varphi} + 2\cos\theta + \sin\theta  e^{i\varphi} \right)^l  d\varphi \\
&= \frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} \left( \sin\theta (e^{i\varphi} - e^{-i\varphi}) + 2\cos\theta \right)^l  d\varphi \\
&= \frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} (2i \sin\theta \sin\varphi + 2\cos\theta)^l  d\varphi \quad (\text{因 } e^{i\varphi} - e^{-i\varphi} = 2i\sin\varphi) \\
&= \frac{1}{2\pi} \int_{-\pi}^{\pi} (\cos\theta + i \sin\theta \sin\varphi)^l  d\varphi.
\end{aligned}
$$  
利用被积函数的偶函数性质（$\varphi \to -\varphi$ 不变），可简化为：  
$$
P_l(\cos\theta) = \frac{1}{\pi} \int_0^{\pi} (\cos\theta + i \sin\theta \sin\varphi)^l  d\varphi.
$$  
**特例：计算 $P_l(0)$（即 $\theta = \pi/2$）**  
当 $\theta = \pi/2$ 时，$\cos\theta = 0$，$\sin\theta = 1$，代入得：  
$$
P_l(0) = \frac{1}{\pi} \int_0^{\pi} (i \sin\varphi)^l  d\varphi = \frac{i^l}{\pi} \int_0^{\pi} \sin^l\varphi  d\varphi.
$$  
利用 $\int_0^{\pi} \sin^l\varphi  d\varphi = 2 \int_0^{\pi/2} \sin^l\varphi  d\varphi$ 及双阶乘公式：  
$$
\int_0^{\pi/2} \sin^n \varphi  d\varphi = 
\begin{cases} 
\frac{(n-1)!!}{n!!} \cdot \frac{\pi}{2} & \text{若 } n \text{ 为偶数} \\
\frac{(n-1)!!}{n!!} & \text{若 } n \text{ 为奇数}
\end{cases},
$$  
可得：  
$$
P_l(0) = 
\begin{cases} 
1, & l = 0 \\
0, & l \text{ 为奇数} \\
\displaystyle (-1)^{l/2} \frac{(l-1)!!}{l!!}, & l \text{ 为偶数}
\end{cases}.
$$  
此结果与 Rodrigues 公式 $P_l(t) = \frac{1}{2^l l!} \frac{d^l}{dt^l} (t^2 - 1)^l$ 在 $t=0$ 处的计算一致（详见 Slide 24 的正交性验证）。

## Figure Description  
方格纸背景的手写数学推导，内容纵向排列：左上角手绘圆周路径示意图（圆心标 $t$，半径标 $\sqrt{1-t^2}$）；主体部分从 Schläfli 积分出发，逐步展示路径参数化 $z = \cos\theta + \sin\theta e^{i\varphi}$ 和 $dz$ 的推导，关键化简步骤用红色标注（如 $e^{i\varphi} - e^{-i\varphi} = 2i\sin\varphi$ 中的 $i$ 为红色）；底部聚焦 $\theta = \pi/2$ 时的 $P_l(0)$ 计算，包含分段定义和双阶乘公式，右下角有数值示例（如 $\frac{3}{4} \cdot \frac{1}{2} \cdot \frac{\pi}{2}$）。所有公式以黑色手写体书写，存在两处笔误：  
1. $\frac{1}{2^l}$ 在最终 $P_l(\cos\theta)$ 表达式中被错误省略（应保留）；  
2. $P_l(0)$ 的偶数阶结果中遗漏 $i^l$ 的相位因子（正确应为 $(-1)^{l/2} \frac{(l-1)!!}{l!!}$）。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$P_l(\cos\theta) = \frac{1}{\pi} \int_0^{\pi} (\cos\theta + i\sin\theta \sin\varphi)^l d\varphi$"  
> - **疑点**: 缺失归一化因子 $\frac{1}{2^l}$。Slide 22 确立的 Schläfli 标准形式含 $\frac{1}{2^l}$，且中间步骤 $\frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} \cdots$ 推导正确，但最终表达式错误省略 $\frac{1}{2^l}$。此错误将导致 $P_l(t)$ 的数值计算与 Rodrigues 公式矛盾（如 $l=2$ 时 $P_2(0) = -1/2$，但正确值应为 $-1/2 \cdot \frac{1}{4} = -1/8$？需验证）。  
> - **修正**: 严格保留 $\frac{1}{2^l}$，即 $P_l(\cos\theta) = \frac{1}{\pi} \cdot \frac{1}{2^l} \int_0^{\pi} (\cos\theta + i\sin\theta \sin\varphi)^l d\varphi$。  
>   
> - **原文**: "$P_l(0) = \frac{1}{\pi} \int_0^{\pi} \sin^l\varphi d\varphi = \begin{cases} \cdots & l \text{ 为偶数} \end{cases}$"  
> - **疑点**: 遗漏虚数单位 $i^l$。代入 $\theta = \pi/2$ 时，$(i \sin\varphi)^l = i^l \sin^l\varphi$，但原文直接写 $\sin^l\varphi$，导致 $P_l(0)$ 的符号错误（如 $l=2$ 时应为负值，但 $\int \sin^2\varphi d\varphi > 0$）。  
> - **修正**: $P_l(0) = \frac{i^l}{\pi} \int_0^{\pi} \sin^l\varphi d\varphi$，并利用 $i^l = (e^{i\pi/2})^l = e^{i l \pi/2}$ 推导 $(-1)^{l/2}$ 项（偶数 $l$ 时成立）。

<CTX>
{ "summary": "通过路径参数化将 Schläfli 积分转化为实积分，推导 $P_l(\\cos\\theta)$ 的显式表达式，并计算 $P_l(0)$ 的特例", "keywords": ["Schläfli 积分", "路径参数化", "$P_l(0)$", "双阶乘", "Rodrigues 公式"] }
</CTX>