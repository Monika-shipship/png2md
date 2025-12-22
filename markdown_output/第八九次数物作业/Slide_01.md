### Slide 1  
**正交曲线坐标系与球坐标系下的微分算子**  

在正交曲线坐标系中，定义拉梅系数 $H_1, H_2, H_3$ 和坐标轴 $q_1, q_2, q_3$。梯度、散度和旋度的通用表达式如下：  

- **梯度**：  
  $$
  \nabla f = \frac{1}{H_1} \frac{\partial f}{\partial q_1} \vec{e_1} + \frac{1}{H_2} \frac{\partial f}{\partial q_2} \vec{e_2} + \frac{1}{H_3} \frac{\partial f}{\partial q_3} \vec{e_3}
  $$

- **散度**：  
  $$
  \nabla \cdot \vec{a} = \frac{1}{H_1 H_2 H_3} \left( \frac{\partial}{\partial q_1} (H_2 H_3 a_1) + \frac{\partial}{\partial q_2} (H_1 H_3 a_2) + \frac{\partial}{\partial q_3} (H_1 H_2 a_3) \right)
  $$

- **旋度**：  
  $$
  \nabla \times \vec{a} = \frac{1}{H_1 H_2 H_3} 
  \begin{vmatrix}
  H_1 \vec{e_1} & H_2 \vec{e_2} & H_3 \vec{e_3} \\
  \frac{\partial}{\partial q_1} & \frac{\partial}{\partial q_2} & \frac{\partial}{\partial q_3} \\
  H_1 a_1 & H_2 a_2 & H_3 a_3
  \end{vmatrix}
  $$

在球坐标系中，拉梅系数和坐标变量对应关系为：  
$$
H_1 = 1, \quad H_2 = r, \quad H_3 = r \sin\theta; \quad q_1 = r, \quad q_2 = \theta, \quad q_3 = \phi
$$

代入上述通用公式，得到球坐标系下的具体形式：  

- **梯度**：  
  $$
  \nabla f = \frac{\partial f}{\partial r} \vec{e_r} + \frac{1}{r} \frac{\partial f}{\partial \theta} \vec{e_\theta} + \frac{1}{r \sin\theta} \frac{\partial f}{\partial \phi} \vec{e_\phi}
  $$

- **散度**：  
  $$
  \nabla \cdot \vec{a} = \frac{1}{r^2} \frac{\partial}{\partial r} (r^2 a_r) + \frac{1}{r \sin\theta} \frac{\partial}{\partial \theta} (\sin\theta  a_\theta) + \frac{1}{r \sin\theta} \frac{\partial a_\phi}{\partial \phi}
  $$

- **拉普拉斯算子**：  
  $$
  \nabla^2 u = \frac{1}{r^2} \frac{\partial}{\partial r} \left( r^2 \frac{\partial u}{\partial r} \right) + \frac{1}{r^2 \sin\theta} \frac{\partial}{\partial \theta} \left( \sin\theta \frac{\partial u}{\partial \theta} \right) + \frac{1}{r^2 \sin^2\theta} \frac{\partial^2 u}{\partial \phi^2}
  $$

## Figure Description  
手写于浅色方格纸的数学推导，内容垂直排列。顶部为拉梅系数与坐标轴定义，中部为正交曲线坐标系下梯度、散度、旋度的通用公式（含向量符号、偏导符号及行列式结构），底部为球坐标系下拉梅系数赋值及具体算子形式。所有公式为黑色墨水手写体，背景为均匀浅色网格线，无图表或数据图。  

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: 梯度公式中 "$\nabla f = \frac{1}{H_1} \partial_1 f \vec{e_1} = \frac{1}{H_1} \frac{\partial f}{\partial q_1} \vec{e_1} + \cdots$"  
> - **疑点**: 等号左侧 "$\frac{1}{H_1} \partial_1 f \vec{e_1}$" 与右侧重复，且 $\partial_1 f$ 未定义（应为 $\frac{\partial f}{\partial q_1}$）。标准表达中，$\partial_i$ 通常直接表示对 $q_i$ 的偏导，此处冗余等号易引发歧义。  
> - **修正**: 移除冗余等号，统一使用 $\frac{\partial}{\partial q_i}$ 符号，确保公式简洁性与符号一致性。  
>   
> - **原文**: 拉普拉斯算子第一表达式 "$\nabla^2 u = \cdots + \frac{1}{r \sin\theta} \partial_\theta \left( \sin\theta \cdot \frac{1}{r} \partial_\theta u \right) + \cdots$"  
> - **疑点**: $\frac{1}{r}$ 位置错误，导致量纲不一致（$\partial_\theta$ 作用于无量纲量 $\theta$，但 $\frac{1}{r} \partial_\theta u$ 引入长度量纲倒数）。标准球坐标拉普拉斯算子中，$\theta$ 项应为 $\frac{1}{r^2 \sin\theta} \partial_\theta (\sin\theta  \partial_\theta u)$。  
> - **修正**: 采用第二表达式作为规范形式，移除第一表达式以避免混淆（第二表达式已正确简化）。  

<CTX>  
{ "summary": "正交曲线坐标系微分算子通用公式及球坐标系特例，重点推导梯度、散度、旋度和拉普拉斯算子", "keywords": ["拉梅系数", "正交曲线坐标系", "球坐标系", "拉普拉斯算子", "散度"] }  
</CTX>