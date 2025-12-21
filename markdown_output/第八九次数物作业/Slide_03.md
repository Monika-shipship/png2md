# Slide 3

本页继续对球坐标系中拉普拉斯方程的角向部分进行变量分离，进一步将角向函数 $ Y(\theta, \varphi) $ 分离为极角部分 $ \Theta(\theta) $ 和方位角部分 $ \Phi(\varphi) $，最终导出连带勒让德方程与勒让德方程。

我们从角向方程出发，假设：
$$
Y(\theta, \varphi) = \Theta(\theta)\Phi(\varphi)
$$
代入前页得到的角向方程：
$$
\frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta Y) + \frac{1}{\sin^2\theta} \partial_\varphi^2 Y + l(l+1) Y = 0
$$
代入分离形式后得：
$$
\Phi \cdot \frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + \Theta \cdot \frac{1}{\sin^2\theta} \partial_\varphi^2 \Phi + \Theta \Phi l(l+1) = 0
$$

两边同除以 $ \Theta \Phi $ 并整理：
$$
\frac{1}{\Theta} \cdot \frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + \frac{1}{\Phi} \cdot \frac{1}{\sin^2\theta} \partial_\varphi^2 \Phi + l(l+1) = 0
$$

乘以 $ \sin^2\theta $ 得：
$$
\frac{\sin\theta}{\Theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + \frac{1}{\Phi} \partial_\varphi^2 \Phi + l(l+1) \sin^2\theta = 0
$$

移项分离变量：
$$
\frac{\sin\theta}{\Theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + l(l+1) \sin^2\theta = -\frac{1}{\Phi} \partial_\varphi^2 \Phi
$$

由于左边仅依赖 $ \theta $，右边仅依赖 $ \varphi $，故二者等于同一常数。令该常数为 $ \lambda $，即：
$$
-\frac{1}{\Phi} \frac{d^2\Phi}{d\varphi^2} = \lambda \quad \Rightarrow \quad \frac{d^2\Phi}{d\varphi^2} + \lambda \Phi = 0
$$

同时，极角部分满足：
$$
\sin\theta \partial_\theta (\sin\theta \partial_\theta \Theta) + \left[ l(l+1) \sin^2\theta - \lambda \right] \Theta = 0
$$

两边除以 $ \sin^2\theta $ 得标准形式：
$$
\frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta \Theta) + \left[ l(l+1) - \frac{\lambda}{\sin^2\theta} \right] \Theta = 0
$$

引入变量替换 $ x = \cos\theta $，则有：
$$
\frac{d}{d\theta} = \frac{dx}{d\theta} \frac{d}{dx} = -\sin\theta \frac{d}{dx}, \quad \text{故} \quad \partial_\theta = -\sin\theta \partial_x
$$

计算：
$$
\sin\theta \partial_\theta = \sin\theta (-\sin\theta \partial_x) = -\sin^2\theta \partial_x
$$
于是：
$$
\partial_\theta (\sin\theta \partial_\theta \Theta) = \partial_\theta ( -\sin^2\theta \partial_x \Theta ) = (-\sin\theta \partial_x)( -\sin^2\theta \partial_x \Theta ) = \sin\theta \partial_x (\sin^2\theta \partial_x \Theta)
$$

因此：
$$
\frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta \Theta) = \partial_x (\sin^2\theta \partial_x \Theta) = \partial_x \left( (1 - x^2) \frac{d\Theta}{dx} \right)
$$

代入方程得：
$$
\frac{d}{dx} \left( (1 - x^2) \frac{d\Theta}{dx} \right) + \left[ l(l+1) - \frac{\lambda}{1 - x^2} \right] \Theta = 0
$$

由周期性边界条件 $ \Phi(\varphi + 2\pi) = \Phi(\varphi) $，解 $ \frac{d^2\Phi}{d\varphi^2} + \lambda \Phi = 0 $ 要求 $ \lambda = m^2 $，其中 $ m \in \mathbb{Z} $。代入 $ \lambda = m^2 $，得：

$$
\frac{d}{dx} \left( (1 - x^2) \frac{d\Theta}{dx} \right) + \left[ l(l+1) - \frac{m^2}{1 - x^2} \right] \Theta = 0
$$

此即 **$ l $ 阶连带勒让德方程**（Associated Legendre Equation）。当 $ m = 0 $ 时退化为：

$$
\frac{d}{dx} \left( (1 - x^2) \frac{d\Theta}{dx} \right) + l(l+1) \Theta = 0
$$

展开为：
$$
(1 - x^2) \frac{d^2\Theta}{dx^2} - 2x \frac{d\Theta}{dx} + l(l+1) \Theta = 0
$$

此即 **$ l $ 阶勒让德方程**（Legendre's Equation）。

## Figure Description

图像为方格纸背景的手写推导内容，使用黑色墨水书写，包含多行数学公式与少量中文注释。推导流程自上而下：从 $ Y(\theta,\varphi) = \Theta(\theta)\Phi(\varphi) $ 开始，逐步分离变量，推导至连带勒让德方程。第四行公式后有红色手写标注“三入”，可能意为“三项合并”或“代入三次”，结合上下文推测为强调分离变量的关键步骤。整体书写清晰，逻辑连贯，重点突出变量替换 $ x = \cos\theta $ 的链式微分过程。

<CTX>
{
  "topic": "角向方程的完全分离与连带勒让德方程",
  "keywords": ["连带勒让德方程", "勒让德方程", "变量分离", "周期性边界条件", "方位角方程"],
  "summary": "本页完成了拉普拉斯方程角向部分的完全分离，得到方位角方程和极角方向的连带勒让德方程；通过变量替换 $ x = \\cos\\theta $ 将其化为标准形式，并指出当 $ m=0 $ 时退化为勒让德方程。",
  "last_formula_context": "最后一个公式是 $ l $ 阶勒让德方程的标准形式，将在下一页用于讨论其多项式解与正交性。"
}
</CTX>