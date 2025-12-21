# Slide 5

柱坐标 $H_1 = 1$ $H_2 = r$ $H_3 = 1$  
$q_1 = r$ $q_2 = \phi$ $q_3 = z$.

所以 $\nabla f = \partial_r f \vec{e_r} + \frac{1}{r} \partial_\phi f \vec{e_\phi} + \partial_z f \vec{e_z}$  
$\nabla \cdot \vec{a} = \frac{1}{r} \partial_r (r a_r) + \frac{1}{r} \partial_\phi (a_\phi) + \partial_z (a_z)$  
$\nabla^2 u = \nabla \cdot \nabla u = \frac{1}{r} \partial_r (r \partial_r u) + \frac{1}{r} \partial_\phi \left( \frac{1}{r} \partial_\phi u \right) + \partial_z (\partial_z u)$  
$\nabla^2 u = \frac{1}{r} \partial_r (r \partial_r u) + \frac{1}{r^2} \partial^2_\phi u + \partial^2_z u$.

## Figure & Layout Description  
图片为方格纸背景的手写数学推导，黑色墨水书写。内容垂直排列，共6行公式。第一行标注"柱坐标"，其后分两行列出度量因子 $H_i$ 与坐标变量 $q_i$ 的对应关系（$H_1=1$, $H_2=r$, $H_3=1$；$q_1=r$, $q_2=\phi$, $q_3=z$）。第三行起为微分算子推导：  
1. 梯度算子 $\nabla f$ 的柱坐标展开式（含向量符号 $\vec{e}$ 带箭头标记）  
2. 散度 $\nabla \cdot \vec{a}$ 的表达式（包含分式系数 $\frac{1}{r}$）  
3. 拉普拉斯算子 $\nabla^2 u$ 的完整展开式（含复合偏导项）  
4. 拉普拉斯算子的简化形式（二次偏导项合并）  
所有公式均严格对齐书写，分式与偏导符号清晰，方格线为浅灰色网格，文字占据页面中上部区域，底部留有空白网格区域。

<CTX>
{
   "topic": "柱坐标系中微分算子的表达式推导",
   "keywords": ["柱坐标系", "梯度算子", "散度算子", "拉普拉斯算子"],
   "summary": "推导并简化了柱坐标系下的梯度、散度及拉普拉斯算子的数学表达式",
   "pending_concepts": ["柱坐标与球坐标的算子形式对比", "拉普拉斯方程在柱坐标下的分离变量法", "径向方程与贝塞尔函数的关联"]
}
</CTX>