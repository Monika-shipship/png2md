# Slide 3

再分离 $Y(\theta, \phi) = \Theta(\theta) \Phi(\phi)$.

$$
\Phi \frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \Theta \frac{1}{\sin^2\theta} \frac{\partial^2 \Phi}{\partial \phi^2} + \Theta \Phi l(l+1) = 0.
$$

$$
\frac{\sin\theta}{\Theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \frac{1}{\Phi} \frac{\partial^2 \Phi}{\partial \phi^2} + l(l+1) \sin^2\theta = 0.
$$

$$
\frac{\sin\theta}{\Theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + l(l+1) \sin^2\theta = -\frac{1}{\Phi} \frac{\partial^2 \Phi}{\partial \phi^2} = \lambda
$$

$$
\sin\theta \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \left[ l(l+1) \sin^2\theta - \lambda \right] \Theta = 0.
$$

$$
\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) + \left[ l(l+1) - \frac{\lambda}{\sin^2\theta} \right] \Theta = 0.
$$

令 $x = \cos\theta$，$\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} = -\frac{\partial}{\partial \cos\theta} = -\frac{\partial}{\partial x}$

故 $\frac{1}{\sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial \Theta}{\partial \theta} \right) = -\frac{\partial}{\partial x} \left( \sin^2\theta \frac{\partial \Theta}{\partial x} \right) = \frac{\partial}{\partial x} \left( (1-x^2) \frac{\partial \Theta}{\partial x} \right)$

$$
\frac{\partial}{\partial x} \left( (1-x^2) \frac{\partial \Theta}{\partial x} \right) + \left[ l(l+1) - \frac{m^2}{\sin^2\theta} \right] \Theta = 0. \quad (\lambda = m^2 \text{ 来源见后文})
$$

这是 $l$ 阶连带勒让德方程

$m=0$ 时是 $l$ 阶勒让德方程.

$$
\frac{\partial}{\partial x} \left( (1-x^2) \frac{\partial \Theta}{\partial x} \right) + l(l+1) \Theta = 0.
$$

$$
(1-x^2) \frac{\partial^2 \Theta}{\partial x^2} - 2x \frac{\partial \Theta}{\partial x} + l(l+1) \Theta = 0.
$$

## Figure & Layout Description
图片为方格纸背景的手写数学推导，整体布局为垂直排列的公式序列。所有公式均用黑色墨水书写，字迹工整但带有手写特征。第一行以"再分离"开头，定义$Y(\theta,\phi)$的分离形式。后续6行是连续的偏微分方程推导，每行公式占据独立行高，其中第三行右侧有红色手写标记"三入"（实际应为特征值符号$\lambda$的误写）。推导过程中包含分式、偏导符号和三角函数表达式，部分公式使用方括号进行项的分组。中间有"令$x=\cos\theta$"的变量替换说明，末尾两行以中文说明方程类型。红色标记仅出现在第三行右侧，其余文字均为黑色。公式中存在明显的上下标结构（如$\sin^2\theta$、$l(l+1)$），且部分偏导数使用分数形式表示。整体排版遵循从上到下的逻辑推导顺序，无表格或图形元素，仅包含纯数学表达式和简短中文注释。

<CTX>
{
   "topic": "球坐标系中角向方程的变量替换与连带勒让德方程推导",
   "keywords": ["拉普拉斯方程", "分离变量法", "球谐函数", "连带勒让德方程", "变量替换"],
   "summary": "通过变量替换将角向方程转化为连带勒让德方程形式，明确m=0时退化为勒让德方程的特殊情况",
   "pending_concepts": ["球谐函数的具体表达式", "边界条件对解的约束", "m值的物理意义"]
}
</CTX>