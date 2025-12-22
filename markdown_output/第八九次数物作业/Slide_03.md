### Slide 3  
**拉普拉斯方程在球坐标系下的分离变量法（角度部分）**  

承接 Slide 2 的角度部分方程：  
$$
\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \widetilde{Y}}{\partial \theta} \right) + \frac{1}{\sin^2\theta} \frac{\partial^2 \widetilde{Y}}{\partial \varphi^2} + l(l+1) \widetilde{Y} = 0
$$  
进一步分离变量 $\widetilde{Y}(\theta, \varphi) = \Theta(\theta) \Phi(\varphi)$，代入得：  
$$
\Phi \frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \Theta \frac{1}{\sin^2\theta} \frac{\partial^2 \Phi}{\partial \varphi^2} + \Theta \Phi l(l+1) = 0
$$  
两边同乘 $\frac{\sin^2\theta}{\Theta \Phi}$ 并整理：  
$$
\frac{\sin\theta}{\Theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + l(l+1) \sin^2\theta = -\frac{1}{\Phi} \frac{\partial^2 \Phi}{\partial \varphi^2}
$$  
设等式两侧等于常数 $\lambda$：  
$$
\frac{\sin\theta}{\Theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + l(l+1) \sin^2\theta = \lambda, \quad -\frac{1}{\Phi} \frac{\partial^2 \Phi}{\partial \varphi^2} = \lambda
$$  
解得 $\theta$ 方向方程：  
$$
\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \left[ l(l+1) - \frac{\lambda}{\sin^2\theta} \right] \Theta = 0
$$  
令 $x = \cos\theta$，利用 $\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} = -\frac{\partial}{\partial x}$ 及 $\sin^2\theta = 1 - x^2$，化简为：  
$$
\frac{\partial}{\partial x} \left( (1 - x^2) \frac{\partial \Theta}{\partial x} \right) + \left[ l(l+1) - \frac{m^2}{1 - x^2} \right] \Theta = 0 \quad (\text{其中 } \lambda = m^2)
$$  
此即 $l$ 阶连带勒让德方程。当 $m = 0$ 时退化为 $l$ 阶勒让德方程：  
$$
(1 - x^2) \frac{\partial^2 \Theta}{\partial x^2} - 2x \frac{\partial \Theta}{\partial x} + l(l+1) \Theta = 0
$$  

## Figure Description  
手写于浅色方格纸的数学推导，内容垂直排列。顶部为角度部分分离变量 $\widetilde{Y} = \Theta \Phi$，中部为 $\theta$ 方向方程的推导过程（含常数 $\lambda$ 的设定及变量代换 $x = \cos\theta$），底部为连带勒让德方程及其 $m=0$ 特例。所有公式为黑色墨水手写体，第四行公式右侧有红色手写标注“三入”（意指“设为常数 $\lambda$”），背景为均匀浅色网格线；字迹工整，公式结构清晰，与 Slide 1–2 的推导风格一致。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$\frac{\sin\theta}{\Theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + l(l+1) \sin^2\theta = -\frac{1}{\Phi} \partial_\varphi^2 \Phi$ 三入"  
> - **疑点**: "三入"为手写标注，但符号 $\partial_\theta$/$\partial_\varphi$ 与 Slide 1–2 的 $\frac{\partial}{\partial \theta}$/$\frac{\partial}{\partial \varphi}$ 不一致；且"三入"语义模糊（应为"设为常数 $\lambda$"）。  
> - **修正**: 统一使用 $\frac{\partial}{\partial \theta}$/$\frac{\partial}{\partial \varphi}$ 符号；将"三入"明确表述为"设等式两侧等于常数 $\lambda$"，确保符号规范性与逻辑连贯性。  
>   
> - **原文**: "$\partial_x ((1-x^2) \partial_x \Theta) + \left[l(l+1) - \frac{m^2}{\sin^2\theta}\right] \Theta = 0$"  
> - **疑点**: $\frac{m^2}{\sin^2\theta}$ 未转换为 $x$ 变量（应为 $\frac{m^2}{1-x^2}$），与后文勒让德方程形式矛盾。  
> - **修正**: 依据 $\sin^2\theta = 1 - x^2$，将 $\frac{m^2}{\sin^2\theta}$ 修正为 $\frac{m^2}{1-x^2}$，保持方程在 $x$ 坐标系下的严格一致性。  

<CTX>
{ "summary": "完成球坐标系下拉普拉斯方程角度部分的分离变量，推导出连带勒让德方程及其特例", "keywords": ["分离变量法", "连带勒让德方程", "角度部分", "球坐标系", "常数λ"] }
</CTX>