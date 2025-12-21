# Slide 2

我们继续在球坐标系中求解拉普拉斯方程：
$$
\nabla^2 u = 0
$$

采用**分离变量法**，设解的形式为：
$$
u(r, \theta, \varphi) = R(r) \widetilde{Y}(\theta, \varphi)
$$

将上述形式代入球坐标系下的拉普拉斯算子表达式：
$$
\frac{1}{r^2} \partial_r (r^2 \partial_r u) + \frac{1}{r^2 \sin\theta} \partial_\theta (\sin\theta \partial_\theta u) + \frac{1}{r^2 \sin^2\theta} \partial_\varphi^2 u = 0
$$

代入 $ u = R(r) \widetilde{Y}(\theta, \varphi) $ 得：
$$
\widetilde{Y} \cdot \frac{1}{r^2} \partial_r (r^2 \partial_r R) + R \cdot \frac{1}{r^2 \sin\theta} \partial_\theta (\sin\theta \partial_\theta \widetilde{Y}) + R \cdot \frac{1}{r^2 \sin^2\theta} \partial_\varphi^2 \widetilde{Y} = 0
$$

两边同乘 $ \frac{r^2}{R \widetilde{Y}} $，整理得：
$$
\frac{1}{R} \partial_r (r^2 \partial_r R) = -\frac{1}{\widetilde{Y} \sin\theta} \partial_\theta (\sin\theta \partial_\theta \widetilde{Y}) - \frac{1}{\widetilde{Y} \sin^2\theta} \partial_\varphi^2 \widetilde{Y}
$$

由于左右两边分别为仅含 $ r $ 和仅含 $ (\theta, \varphi) $ 的函数，必须等于同一常数。设该常数为 $ G $，即：
$$
\frac{1}{R} \partial_r (r^2 \partial_r R) = G, \quad 
-\left[ \frac{1}{\widetilde{Y} \sin\theta} \partial_\theta (\sin\theta \partial_\theta \widetilde{Y}) + \frac{1}{\widetilde{Y} \sin^2\theta} \partial_\varphi^2 \widetilde{Y} \right] = G
$$

考虑径向方程：
$$
\partial_r (r^2 \partial_r R) = G R
$$

尝试幂函数解：设 $ R(r) = r^n $，则：
$$
\partial_r (r^2 \cdot n r^{n-1}) = \partial_r (n r^{n+1}) = n(n+1) r^n
$$
右边为 $ G r^n $，故有：
$$
n(n+1) = G
$$

因此令 $ G = l(l+1) $，其中 $ l $ 为非负整数。

于是径向方程的通解为：
$$
R(r) = A r^l + B r^{-l-1}
$$

接下来分析角向部分。由上可得：
$$
\frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta \widetilde{Y}) + \frac{1}{\sin^2\theta} \partial_\varphi^2 \widetilde{Y} + l(l+1) \widetilde{Y} = 0
$$

此即**球谐函数满足的微分方程**，其解为球谐函数 $ Y_l^m(\theta, \varphi) $，构成完备正交基，用于描述球面上的标量场分布。

综上，拉普拉斯方程 $ \nabla^2 u = 0 $ 在球坐标系中的分离变量解为：
$$
u(r, \theta, \varphi) = \sum_{l=0}^{\infty} \sum_{m=-l}^{l} \left( A_{lm} r^l + \frac{B_{lm}}{r^{l+1}} \right) Y_l^m(\theta, \varphi)
$$

## Figure Description

图片为方格纸背景的手写推导过程，文字与公式垂直排列，从上至下展示了拉普拉斯方程在球坐标系中进行分离变量法的完整步骤。包括变量分离假设、代入展开、分离出径向和角向方程、试探解代入求解特征指数、最终得出径向函数形式及角向方程结构。无图表或图像元素，仅为多行数学推导手稿。

<CTX>
{
  "topic": "球坐标系中拉普拉斯方程的分离变量法",
  "keywords": ["分离变量法", "球谐函数", "径向方程", "角向方程", "拉普拉斯方程"],
  "summary": "本页详细推导了拉普拉斯方程在球坐标系下的分离变量解法，得到径向函数为幂律形式 $ R(r) = A r^l + B r^{-l-1} $，角向部分满足球谐函数方程，整体解由球谐函数展开。",
  "last_formula_context": "最后一个公式是拉普拉斯方程在球坐标系中的通解形式，由球谐函数和径向幂次项组成，将在后续用于边界值问题求解。"
}
</CTX>