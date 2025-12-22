### Slide 2  
**拉普拉斯方程在球坐标系下的分离变量法（径向部分）**  

承接 Slide 1 中球坐标系的拉普拉斯算子，求解 $\nabla^2 u = 0$：  

分离变量得 $u(r, \theta, \varphi) = R(r) \widetilde{Y}(\theta, \varphi)$。代入球坐标系拉普拉斯方程：  
$$
\frac{1}{r^2} \frac{\partial}{\partial r} \left( r^2 \frac{\partial u}{\partial r} \right) + \frac{1}{r^2 \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial u}{\partial \theta} \right) + \frac{1}{r^2 \sin^2\theta} \frac{\partial^2 u}{\partial \varphi^2} = 0
$$  
得：  
$$
\widetilde{Y} \frac{1}{r^2} \frac{\partial}{\partial r} \left( r^2 \frac{\partial R}{\partial r} \right) + R \frac{1}{r^2 \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \widetilde{Y}}{\partial \theta} \right) + R \frac{1}{r^2 \sin^2\theta} \frac{\partial^2 \widetilde{Y}}{\partial \varphi^2} = 0
$$  

移项并乘以 $\frac{r^2}{R}$：  
$$
\frac{1}{R} \frac{\partial}{\partial r} \left( r^2 \frac{\partial R}{\partial r} \right) = -\frac{1}{\widetilde{Y} \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \widetilde{Y}}{\partial \theta} \right) - \frac{1}{\widetilde{Y} \sin^2\theta} \frac{\partial^2 \widetilde{Y}}{\partial \varphi^2}
$$  

设等式两侧等于常数 $G$：  
$$
\frac{1}{R} \frac{\partial}{\partial r} \left( r^2 \frac{\partial R}{\partial r} \right) = G, \quad -\frac{1}{\widetilde{Y} \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \widetilde{Y}}{\partial \theta} \right) - \frac{1}{\widetilde{Y} \sin^2\theta} \frac{\partial^2 \widetilde{Y}}{\partial \varphi^2} = G
$$  

解径向方程 $\frac{\partial}{\partial r} \left( r^2 \frac{\partial R}{\partial r} \right) - G R = 0$：  
- 设 $R = r^n$，代入得：  
  $$
  \frac{\partial}{\partial r} \left( r^2 \cdot n r^{n-1} \right) - G r^n = n(n+1) r^n - G r^n = 0
  $$  
  解得 $G = n(n+1)$。  
- 令 $G = l(l+1)$（$l$ 为非负整数），则：  
  $$
  n(n+1) = l(l+1) \implies n = l \quad \text{或} \quad n = -l-1
  $$  
- 因物理问题要求 $r \to \infty$ 时解有限，取 $n = l$ 或 $n = -l-1$，故径向解为：  
  $$
  R(r) = A r^l + \frac{B}{r^{l+1}}
  $$  

角度部分方程为：  
$$
\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \widetilde{Y}}{\partial \theta} \right) + \frac{1}{\sin^2\theta} \frac{\partial^2 \widetilde{Y}}{\partial \varphi^2} + l(l+1) \widetilde{Y} = 0
$$  

## Figure Description  
手写于浅色方格纸的数学推导，内容垂直排列。顶部为拉普拉斯方程 $\nabla^2 u = 0$ 的分离变量设定，中部为径向方程的求解过程（含 $R = r^n$ 的代入和常数 $G$ 的推导），底部为角度部分方程。所有公式为黑色墨水手写体，背景为均匀浅色网格线，无图表或数据图；字迹工整，公式结构清晰，与 Slide 1 的推导风格一致。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: 分离变量后方程 "$Y \frac{1}{r^2} \partial_r (r^2 \partial_r R) + \cdots$"  
> - **疑点**: 符号不一致——前文定义 $u = R(r) \widetilde{Y}(\theta, \varphi)$，但此处误用 $Y$ 而非 $\widetilde{Y}$，易导致后续推导混淆（如移项后正确使用 $\widetilde{Y}$）。  
> - **修正**: 统一替换为 $\widetilde{Y}$，确保符号与分离变量设定严格一致。  
>   
> - **原文**: 径向解推导 "$R = \frac{1}{r^n} \partial_r (r^2 (-n) r^{-n-1}) - R G = 0$"  
> - **疑点**: 表达式错误——$\frac{1}{r^n}$ 为多余因子，且导数运算逻辑混乱（应直接代入 $R = r^n$ 而非其导数形式）。  
> - **修正**: 移除错误表达式，采用标准代入法：设 $R = r^n$，计算 $\partial_r (r^2 \partial_r R) = n(n+1) r^n$，直接导出 $G = n(n+1)$。  
>   
> - **原文**: 符号使用 "$\varphi$" 与 Slide 1 的 "$\phi$" 不一致  
> - **疑点**: Slide 1 明确定义 $q_3 = \phi$ 且公式中统一用 $\phi$，但此处改用 $\varphi$，违反符号连续性原则。  
> - **修正**: 将所有 $\varphi$ 替换为 $\phi$（LaTeX 中统一用 `\phi`），与 Slide 1 保持一致。  

<CTX>
{ "summary": "本页完成拉普拉斯方程 $\nabla^2 u = 0$ 在球坐标系下的分离变量，求解径向部分 $R(r)$ 并导出角度部分方程。关键步骤包括：设定 $u = R \widetilde{Y}$，分离变量后解径向 ODE，得 $R(r) = A r^l + B r^{-l-1}$，角度方程留待下页分离。", "keywords": ["拉普拉斯方程", "分离变量法", "球坐标系", "径向解", "本征值问题"] }
</CTX>