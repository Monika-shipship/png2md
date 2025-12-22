 
### Slide 4  
**拉普拉斯方程在球坐标系下的分离变量法（方位角部分）**  

承接 Slide 3 中角度部分分离变量 $\widetilde{Y}(\theta, \varphi) = \Theta(\theta) \Phi(\varphi)$ 的结果，方位角 $\varphi$ 方程为：  
$$
\frac{\partial^2 \Phi}{\partial \varphi^2} + \lambda \Phi = 0
$$  
由周期性边界条件 $\Phi(\varphi) = \Phi(\varphi + 2\pi)$，$\lambda < 0$ 的指数解不满足物理要求（解在 $2\pi$ 周期内不收敛）。因此，$\lambda > 0$ 且必须为本征值 $\lambda = m^2$（$m = 0, 1, 2, \ldots$）。此时，方程的通解为三角函数形式：  
$$
\Phi(\varphi) = A \cos m\varphi + B \sin m\varphi
$$  
其中 $A$ 和 $B$ 为常数，由具体边界条件确定。该解严格满足 $2\pi$ 周期性，且与 Slide 3 中设定的常数 $\lambda = m^2$ 一致。

## Figure Description  
手写于白色方格纸的数学推导，内容垂直排列。顶部为方位角微分方程 $\frac{\partial^2 \Phi}{\partial \varphi^2} + \lambda \Phi = 0$，中部说明周期性条件 $\Phi(\varphi) = \Phi(\varphi + 2\pi)$ 及 $\lambda < 0$ 解的排除，底部给出本征值条件 $\lambda = m^2$ 和三角函数解 $\Phi(\varphi) = A \cos m\varphi + B \sin m\varphi$。所有公式为黑色墨水手写体，背景为均匀浅色网格线，无图表或数据图；字迹工整，公式结构清晰，与 Slide 1–3 的推导风格一致。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$\frac{\partial^2 \Phi}{\partial \theta^2} + \lambda \Phi = 0$" 和 "$\Phi(\theta) = \Phi(\theta + 2\pi)$"  
> - **疑点**: 在球坐标系分离变量中，$\Phi$ 明确定义为方位角 $\varphi$ 的函数（Slide 3 已设定 $\widetilde{Y}(\theta, \varphi) = \Theta(\theta) \Phi(\varphi)$），但原文误用 $\theta$（极角）作为变量符号。这会导致逻辑矛盾：$\theta$ 的定义域为 $[0, \pi]$，无周期性；而 $\varphi$ 的定义域为 $[0, 2\pi)$，需满足 $2\pi$ 周期性。  
> - **修正**: 所有 $\theta$ 应统一修正为 $\varphi$，以确保符号一致性与物理意义正确（即 $\frac{\partial^2 \Phi}{\partial \varphi^2} + \lambda \Phi = 0$ 和 $\Phi(\varphi) = \Phi(\varphi + 2\pi)$）。

<CTX>
{ "summary": "本页完成球坐标系拉普拉斯方程的角度部分求解，聚焦方位角 $\varphi$ 方程的周期性条件与本征解推导，修正变量符号错误后得到三角函数形式的通解。", "keywords": ["方位角方程", "周期性边界条件", "本征值", "三角函数解", "符号一致性"] }
</CTX>