### Slide 5  
**拉普拉斯方程在柱坐标系下的算子表达式推导**  

承接坐标系转换的一般方法，柱坐标系 $(r, \varphi, z)$ 的标度因子定义为：  
$$
H_1 = 1, \quad H_2 = r, \quad H_3 = 1; \quad q_1 = r, \quad q_2 = \varphi, \quad q_3 = z.
$$  
基于正交曲线坐标系的梯度、散度和拉普拉斯算子通式，依次推导：  

1. **梯度算子**：  
   $$
   \nabla f = \frac{\partial f}{\partial r} \vec{e_r} + \frac{1}{r} \frac{\partial f}{\partial \varphi} \vec{e_\varphi} + \frac{\partial f}{\partial z} \vec{e_z}
   $$  

2. **散度算子**：  
   $$
   \nabla \cdot \vec{a} = \frac{1}{r} \frac{\partial}{\partial r} (r a_r) + \frac{1}{r} \frac{\partial a_\varphi}{\partial \varphi} + \frac{\partial a_z}{\partial z}
   $$  

3. **拉普拉斯算子**（通过 $\nabla^2 u = \nabla \cdot (\nabla u)$ 推导）：  
   $$
   \nabla^2 u = \frac{1}{r} \frac{\partial}{\partial r} \left( r \frac{\partial u}{\partial r} \right) + \frac{1}{r} \frac{\partial}{\partial \varphi} \left( \frac{1}{r} \frac{\partial u}{\partial \varphi} \right) + \frac{\partial}{\partial z} \left( \frac{\partial u}{\partial z} \right)
   $$  
   简化后得标准形式：  
   $$
   \nabla^2 u = \frac{1}{r} \frac{\partial}{\partial r} \left( r \frac{\partial u}{\partial r} \right) + \frac{1}{r^2} \frac{\partial^2 u}{\partial \varphi^2} + \frac{\partial^2 u}{\partial z^2}
   $$  

## Figure Description  
手写于浅色方格纸的数学推导，内容垂直排列。顶部为柱坐标系标度因子 $H_1, H_2, H_3$ 及坐标变量 $q_1, q_2, q_3$ 的定义，中部依次展示梯度、散度和拉普拉斯算子的推导过程（含中间步骤 $\nabla \cdot (\nabla u)$ 的展开），底部为拉普拉斯算子的最终简化形式。所有公式为黑色墨水手写体，向量符号以箭头表示（如 $\vec{e_r}$），偏导数使用完整形式 $\frac{\partial}{\partial r}$（修正后），背景为均匀浅色网格线；字迹工整，公式结构清晰，与 Slide 1–4 的推导风格一致。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$\nabla f = \partial_r f \vec{e_r} + \frac{1}{r} \partial_\varphi f \vec{e_\varphi} + \partial_z f \vec{e_z}$" 和 "$\nabla \cdot \vec{a} = \frac{1}{r} \partial_r (r a_r) + \frac{1}{r} \partial_\varphi (a_\varphi) + \partial_z (a_z)$"  
> - **疑点**: 在 Slide 3–4 中已强调符号严谨性（如 Slide 4 勘误要求统一使用 $\varphi$ 而非 $\theta$），但此处 $\partial_r$/$\partial_\varphi$/$\partial_z$ 为简写形式，与 Slide 1–4 的完整偏导符号 $\frac{\partial}{\partial r}$/$\frac{\partial}{\partial \varphi}$/$\frac{\partial}{\partial z}$ 不一致。这可能导致初学者混淆（简写 $\partial_r$ 未明确表示偏导算子），且与课程一贯的数学严谨性冲突。  
> - **修正**: 所有简写 $\partial_r$/$\partial_\varphi$/$\partial_z$ 统一修正为完整形式 $\frac{\partial}{\partial r}$/$\frac{\partial}{\partial \varphi}$/$\frac{\partial}{\partial z}$，以确保符号规范性和教学一致性（例如 $\frac{\partial f}{\partial r}$ 而非 $\partial_r f$）。

<CTX>
{ "summary": "本页系统推导柱坐标系下梯度、散度及拉普拉斯算子的表达式，修正偏导符号简写问题后得到标准拉普拉斯方程形式，为后续分离变量法提供数学基础。", "keywords": ["柱坐标系", "标度因子", "梯度算子", "散度算子", "拉普拉斯算子"] }
</CTX>