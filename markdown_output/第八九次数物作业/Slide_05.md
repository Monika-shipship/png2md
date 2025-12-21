# Slide 5

本页推导了柱坐标系下的梯度、散度和拉普拉斯算子表达式，基于正交曲线坐标系的标度因子方法。这些微分算子在求解柱对称问题（如圆柱体内的热传导或电磁场）中具有重要作用。

## 柱坐标系下的微分算子

柱坐标系定义为：
- 坐标变量：$ q_1 = r $, $ q_2 = \varphi $, $ q_3 = z $
- 标度因子：$ H_1 = 1 $, $ H_2 = r $, $ H_3 = 1 $

### 梯度（Gradient）
$$
\nabla f = \frac{\partial f}{\partial r} \vec{e}_r + \frac{1}{r} \frac{\partial f}{\partial \varphi} \vec{e}_\varphi + \frac{\partial f}{\partial z} \vec{e}_z
$$

### 散度（Divergence）
$$
\nabla \cdot \vec{a} = \frac{1}{r} \frac{\partial}{\partial r} (r a_r) + \frac{1}{r} \frac{\partial}{\partial \varphi} (a_\varphi) + \frac{\partial}{\partial z} (a_z)
$$

### 拉普拉斯算子（Laplacian）
首先计算：
$$
\nabla^2 u = \nabla \cdot (\nabla u) = \frac{1}{r} \frac{\partial}{\partial r} \left( r \frac{\partial u}{\partial r} \right) + \frac{1}{r} \frac{\partial}{\partial \varphi} \left( \frac{1}{r} \frac{\partial u}{\partial \varphi} \right) + \frac{\partial}{\partial z} \left( \frac{\partial u}{\partial z} \right)
$$

简化后得：
$$
\nabla^2 u = \frac{1}{r} \frac{\partial}{\partial r} \left( r \frac{\partial u}{\partial r} \right) + \frac{1}{r^2} \frac{\partial^2 u}{\partial \varphi^2} + \frac{\partial^2 u}{\partial z^2}
$$

该表达式是柱坐标系下拉普拉斯方程的标准形式，常用于分离变量法求解偏微分方程。

## Figure Description

图片为方格纸背景的手写内容，文字与公式纵向排列。顶部标注“柱坐标”，随后列出标度因子 $H_i$ 与坐标变量 $q_i$ 的定义。其下依次推导梯度、散度与拉普拉斯算子的表达式。所有公式以手写体书写，符号清晰：向量用箭头标记（如 $\vec{e}_r$），偏导数使用 $\partial$ 符号，角度坐标记为 $\varphi$。无图形图表，仅含数学公式与少量中文注释。公式排版整齐，每行独立，逻辑连贯。

<CTX>
{
  "topic": "柱坐标系下的微分算子推导",
  "keywords": ["柱坐标", "标度因子", "梯度", "散度", "拉普拉斯算子"],
  "summary": "本页基于正交曲线坐标系的通用公式，利用标度因子 H₁=1, H₂=r, H₃=1 推导出柱坐标系下的梯度、散度和拉普拉斯算子表达式，最终得到 ∇²u 的标准形式，为后续分离变量法求解柱域内偏微分方程做准备。",
  "last_formula_context": "最后一个公式是柱坐标系下的拉普拉斯算子：∇²u = (1/r)∂/∂r(r∂u/∂r) + (1/r²)∂²u/∂φ² + ∂²u/∂z²，将在下一页用于分离变量法求解轴对称问题。"
}
</CTX>