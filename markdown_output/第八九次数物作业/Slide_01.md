# Slide 1

## 正交曲线坐标系中的微分算子

在正交曲线坐标系中，引入拉梅系数 $ H_1, H_2, H_3 $ 和广义坐标 $ q_1, q_2, q_3 $，对应的单位基向量为 $ \vec{e}_1, \vec{e}_2, \vec{e}_3 $。以下为梯度、散度和旋度的一般表达式。

### 梯度（Gradient）
标量函数 $ f $ 的梯度表达式为：
$$
\nabla f = \frac{1}{H_1} \frac{\partial f}{\partial q_1} \vec{e}_1 + \frac{1}{H_2} \frac{\partial f}{\partial q_2} \vec{e}_2 + \frac{1}{H_3} \frac{\partial f}{\partial q_3} \vec{e}_3
$$

### 散度（Divergence）
向量场 $ \vec{a} = a_1 \vec{e}_1 + a_2 \vec{e}_2 + a_3 \vec{e}_3 $ 的散度为：
$$
\nabla \cdot \vec{a} = \frac{1}{H_1 H_2 H_3} \left( \frac{\partial}{\partial q_1} (H_2 H_3 a_1) + \frac{\partial}{\partial q_2} (H_1 H_3 a_2) + \frac{\partial}{\partial q_3} (H_1 H_2 a_3) \right)
$$

### 旋度（Curl）

向量场 $ \vec{a} $ 的旋度由行列式形式给出：
$$
\nabla \times \vec{a} = \frac{1}{H_1 H_2 H_3} 
\begin{vmatrix}
H_1 \vec{e}_1 & H_2 \vec{e}_2 & H_3 \vec{e}_3 \\
\frac{\partial}{\partial q_1} & \frac{\partial}{\partial q_2} & \frac{\partial}{\partial q_3} \\
H_1 a_1 & H_2 a_2 & H_3 a_3
\end{vmatrix}
$$

## 球坐标系下的具体形式

球坐标系中，坐标变量与拉梅系数对应关系如下：

- $ q_1 = r,\quad H_1 = 1 $
- $ q_2 = \theta,\quad H_2 = r $
- $ q_3 = \phi,\quad H_3 = r \sin\theta $

代入一般公式可得以下结果。

### 梯度（球坐标）
$$
\nabla f = \frac{\partial f}{\partial r} \vec{e}_r + \frac{1}{r} \frac{\partial f}{\partial \theta} \vec{e}_\theta + \frac{1}{r \sin\theta} \frac{\partial f}{\partial \phi} \vec{e}_\phi
$$

### 散度（球坐标）
$$
\nabla \cdot \vec{a} = \frac{1}{r^2 \sin\theta} \left( \frac{\partial}{\partial r} (r^2 \sin\theta \, a_r) + \frac{\partial}{\partial \theta} (r \sin\theta \, a_\theta) + \frac{\partial}{\partial \phi} (r \, a_\phi) \right)
$$
化简后为：
$$
\nabla \cdot \vec{a} = \frac{1}{r^2} \frac{\partial}{\partial r} (r^2 a_r) + \frac{1}{r \sin\theta} \frac{\partial}{\partial \theta} (\sin\theta \, a_\theta) + \frac{1}{r \sin\theta} \frac{\partial a_\phi}{\partial \phi}
$$

### 拉普拉斯算子（Laplacian）
标量函数 $ u $ 的拉普拉斯算子定义为 $ \nabla^2 u = \nabla \cdot \nabla u $。经推导得：
$$
\nabla^2 u = \frac{1}{r^2} \frac{\partial}{\partial r} \left( r^2 \frac{\partial u}{\partial r} \right) + \frac{1}{r^2 \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial u}{\partial \theta} \right) + \frac{1}{r^2 \sin^2\theta} \frac{\partial^2 u}{\partial \phi^2}
$$

## Figure Description

图片内容为手写于浅色方格纸上的数学推导过程，布局垂直，从上至下依次包含：拉梅系数与广义坐标的定义、正交曲线坐标系中梯度、散度、旋度的通用表达式，随后列出球坐标系下的拉梅系数赋值（$ H_1=1, H_2=r, H_3=r\sin\theta $），并进一步展开球坐标系中梯度、散度及拉普拉斯算子的具体形式。所有公式以手写体呈现，包含清晰的向量符号（带箭头）、偏导数符号、行列式结构以及多行代数展开。无图像、图表或数据可视化元素，纯为理论公式演算过程。

<CTX>
{
  "topic": "正交曲线坐标系与球坐标系中的微分算子",
  "keywords": ["拉梅系数", "球坐标系", "梯度", "散度", "旋度", "拉普拉斯算子"],
  "summary": "本页介绍了正交曲线坐标系中梯度、散度和旋度的一般表达式，并通过代入球坐标系的拉梅系数，推导出这些算子在球坐标下的具体形式，重点包括拉普拉斯算子的标准展开。",
  "last_formula_context": "最后一个公式是球坐标系下的拉普拉斯算子，用于标量场的二阶微分，将在后续分离变量法或调和函数分析中使用。"
}
</CTX>