# Slide 1

H₁, H₂, H₃ 拉梅系数，q₁, q₂, q₃ 三轴

$$ \nabla f = \frac{1}{H_1} \partial_1 f \vec{e_1} = \frac{1}{H_1} \frac{\partial f}{\partial q_1} \vec{e_1} + \frac{1}{H_2} \frac{\partial f}{\partial q_2} \vec{e_2} + \frac{1}{H_3} \frac{\partial f}{\partial q_3} \vec{e_3} $$

$$ \nabla \cdot \vec{a} = \frac{1}{H_1 H_2 H_3} \left( \partial_1 (H_2 H_3 a_1) + \partial_2 (H_1 H_3 a_2) + \partial_3 (H_1 H_2 a_3) \right) $$

$$ \nabla \times \vec{a} = \frac{1}{H_1 H_2 H_3} \begin{vmatrix} H_1 \vec{e_1} & H_2 \vec{e_2} & H_3 \vec{e_3} \\ \partial_1 & \partial_2 & \partial_3 \\ H_1 a_1 & H_2 a_2 & H_3 a_3 \end{vmatrix} $$

球坐标 H₁=1, H₂=r, H₃=r sinθ  
q₁=r, q₂=θ, q₃=φ

$$ \nabla f = \partial_r f \vec{e_r} + \frac{1}{r} \partial_\theta f \vec{e_\theta} + \frac{1}{r \sin\theta} \partial_\phi f \vec{e_\phi} $$

$$ \nabla \cdot \vec{a} = \frac{1}{r^2 \sin\theta} \left( \partial_r (r^2 \sin\theta a_r) + \partial_\theta (r \sin\theta a_\theta) + \partial_\phi (r a_\phi) \right) $$
$$ = \frac{1}{r^2} \partial_r (r^2 a_r) + \frac{1}{r \sin\theta} \partial_\theta (\sin\theta a_\theta) + \frac{1}{r \sin\theta} \partial_\phi (a_\phi) $$

$$ \nabla^2 u = \nabla \cdot \nabla u = \frac{1}{r^2} \partial_r (r^2 \partial_r u) + \frac{1}{r \sin\theta} \partial_\theta \left( \sin\theta \cdot \frac{1}{r} \partial_\theta u \right) + \frac{1}{r \sin\theta} \partial_\phi \left( \frac{1}{r \sin\theta} \partial_\phi u \right) $$
$$ \nabla^2 u = \frac{1}{r^2} \partial_r (r^2 \partial_r u) + \frac{1}{r^2 \sin\theta} \partial_\theta (\sin\theta \partial_\theta u) + \frac{1}{r^2 \sin^2\theta} \partial_\phi^2 u $$

## Figure & Layout Description
图片为方格纸背景的手写数学推导页，整体布局为垂直排列的多行公式与文字说明。背景为浅灰色方格网格（约5mm×5mm），手写内容使用黑色墨水书写。文字与公式从上至下依次排列：第一行为坐标系定义说明，其下三行分别为梯度、散度、旋度的通用正交曲线坐标表达式，再下两行为球坐标系参数定义，最后四行为球坐标系下微分算子的具体展开式。公式中包含分式、行列式、偏导符号（∂）和向量符号（→），所有下标（如H₁、q₁）均以标准手写体呈现。公式排版保持对齐，关键算子（∇）和坐标变量（r, θ, φ）使用标准数学符号书写，无特殊颜色或图形元素。

<CTX>
{
   "topic": "正交曲线坐标系中的微分算子与拉梅系数",
   "keywords": ["拉梅系数", "梯度", "散度", "旋度", "拉普拉斯算子", "球坐标系"],
   "summary": "推导了正交曲线坐标系下梯度、散度、旋度及拉普拉斯算子的通用表达式，并以球坐标系为例进行具体展开",
   "pending_concepts": []
}
</CTX>