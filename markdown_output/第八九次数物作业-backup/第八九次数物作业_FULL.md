# 第八九次数物作业 汇总

> 生成时间: 2025-12-20 22:50:27

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

---

# Slide 2

再尝试求解 $\nabla^2 u = 0$.

分离变量得 $u(r, \theta, \phi) = R(r) Y(\theta, \phi)$  
（$Y$ 下方标注"球函数"并加波浪线）

$$
Y \frac{1}{r^2} \partial_r (r^2 \partial_r R) + R \frac{1}{r^2 \sin\theta} \partial_\theta (\sin\theta \partial_\theta Y) + R \frac{1}{r^2 \sin^2\theta} \partial_\phi^2 Y = 0
$$

移项，乘 $\frac{Y}{R}$:

$$
\frac{1}{R} \partial_r (r^2 \partial_r R) = -\frac{1}{Y \sin\theta} \partial_\theta (\sin\theta \partial_\theta Y) - \frac{1}{Y \sin^2\theta} \partial_\phi^2 Y
$$

设上两式为 $G$ 常数:

$$
\partial_r (r^2 \partial_r R) - R G = 0
$$

设 $R = r^n$，则:
$$
\partial_r (r^2 n r^{n-1}) - R G = 0 \quad \Rightarrow \quad n(n+1) r^n - r^n G = 0.
$$
（推导过程：$(-n)(-n+1)r^{-n} - r^{-n}G = 0$）

$G = n(n+1)$

所以设 $G = l(l+1)$  
（注：因 $n > 0$，解出 $n = -l$ 或 $n = l+1$，取 $n = l+1$）

有 $\frac{1}{R} \partial_r (r^2 \partial_r R) = l(l+1) \Rightarrow R(r) = A r^l + \frac{B}{r^{l+1}}$.

$$
\frac{1}{\sin\theta} \partial_\theta (\sin\theta \partial_\theta Y) + \frac{1}{\sin^2\theta} \partial_\phi^2 Y + Y l(l+1) = 0.
$$

## Figure & Layout Description
手写内容书写在方格纸背景上，纸张为白色底色配浅灰色网格线。文字以黑色墨水书写，包含数学公式和汉字说明。整体布局为垂直排列的推导过程：
1. 顶部为标题式语句"再尝试求解 $\nabla^2 u = 0$."
2. 中间区域包含多行数学推导，公式与文字交替出现
3. "球函数"标注位于$Y(\theta,\phi)$下方，用波浪线连接并手写标注
4. 推导过程包含多级等式展开，关键步骤如"移项"、"设上两式为G常数"等用汉字说明
5. 右侧有部分推导过程的辅助计算（如$(-n)(-n+1)=l(l+1)$）
6. 所有偏导数符号$\partial$均手写为类似"$\partial$"的符号
7. 公式中出现的分数均以水平线形式书写，如$\frac{1}{r^2}$
8. 文字与公式混排时，汉字说明通常位于公式上方或左侧

<CTX>
{
   "topic": "球坐标系中拉普拉斯方程的分离变量解法",
   "keywords": ["拉普拉斯方程", "分离变量法", "球谐函数", "径向方程", "角向方程"],
   "summary": "通过分离变量法将球坐标系下的拉普拉斯方程分解为径向方程和角向方程，推导出径向解的通式及角向方程的特征形式",
   "pending_concepts": ["球谐函数的具体表达式", "边界条件对解的约束", "负幂次项的物理意义"]
}
</CTX>

---

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

---

# Slide 4

$$\frac{d^2 \Phi}{d\phi^2} + \lambda \Phi = 0$$

由于周期性 $\Phi(\phi) = \Phi(\phi + 2\pi)$，所以 $\lambda < 0$ 的指数解不行  
$\Phi(\phi)$ 必为三角函数解，$\lambda > 0$ 且 $\lambda = m^2$，$m = 0, 1, 2, \ldots$ 是特征值。  
$$\Phi(\phi) = A \cos m\phi + B \sin m\phi$$

## Figure & Layout Description
图片背景为标准方格纸（1cm×1cm网格），黑色手写文字占据上半部分区域。内容按垂直顺序排列：第一行是二阶常微分方程，采用上标平方符号和希腊字母Φ；第二行中文说明包含周期性条件公式，其中$\Phi(\phi+2\pi)$的括号与符号清晰；第三行文字中"m=0,1,2,⋯"的省略号为三点式，"特征值"三字末尾带句号；第四行通解公式中A、B为大写拉丁字母，三角函数符号与变量间有空格。所有文字均为黑色墨水书写，字迹工整但存在轻微连笔现象，如"由于"二字的"于"字末笔与"周"字首笔相连。公式中希腊字母φ的写法为带横线的斜体形式，与普通字母有明显区分。

<CTX>
{
   "topic": "球坐标系方位角方程的特征值确定与通解形式",
   "keywords": ["方位角方程", "周期性边界条件", "特征值", "三角函数解", "m量子数"],
   "summary": "通过周期性边界条件确定方位角方程的特征值条件，推导出三角函数形式的通解并明确m的离散取值",
   "pending_concepts": ["m值的物理意义（角动量量子数）", "边界条件对A/B系数的具体约束", "m≠0时与连带勒让德方程的衔接"]
}
</CTX>

---

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

---

# Slide 6

本页无可见文字或公式内容。

## Figure & Layout Description
该页面为纯白色背景的方格坐标纸布局。整体由浅灰色细实线构成规则网格，横向与纵向线条等距分布。经精确计数，网格包含20行×20列的正方形单元格，每个单元格边长约1.5cm（按标准PPT比例估算）。线条颜色为#E0E0E0（浅灰色），线宽约0.5pt，无任何文字标注、图形元素或色彩填充。页面四周边距均匀，无页眉页脚信息，整体呈现典型的数学推导用空白坐标纸样式，适合手写公式或绘制示意图。

<CTX>
{
   "topic": "柱坐标系中微分算子的表达式推导",
   "keywords": ["柱坐标系", "梯度算子", "散度算子", "拉普拉斯算子"],
   "summary": "本页为空白网格页，未提供新的数学推导内容或公式表达式",
   "pending_concepts": ["柱坐标与球坐标的算子形式对比", "拉普拉斯方程在柱坐标下的分离变量法", "径向方程与贝塞尔函数的关联"]
}
</CTX>

---

# Slide 7

## 15.3

(1) $$y'' - xy' = 0$$

$$p(x) = -x,\ q(x) = 0,\ \text{在}\ x=0\ \text{处是有限的，}\ \text{则}\ x=0\ \text{是常点}$$

在 $x=0$ 的邻域内，设解为 $$y(x) = \sum_{k=0}^{\infty} a_k x^k$$

则 $$y' = \sum_{k=0}^{\infty} k a_k x^{k-1},\ y'' = \sum_{k=0}^{\infty} k(k-1) a_k x^{k-2}$$

$$y'' - xy' = \sum_{k=0}^{\infty} k(k-1) a_k x^{k-2} - \sum_{k=0}^{\infty} k a_k x^{k-1} \cdot x$$
$$= \sum_{k=0}^{\infty} k(k-1) a_k x^{k-2} - \sum_{k=0}^{\infty} k a_k x^k$$
$$= 0 + 0 + \sum_{k=0}^{\infty} (k+1)(k+2) a_{k+2} x^k - \sum_{k=0}^{\infty} k a_k x^k$$
$$= a_2 + \sum_{k=1}^{\infty} \left[(k+1)(k+2) a_{k+2} - k a_k\right] x^k = 0$$

各项为 $0$，得 $a_2 = 0,\ (k+1)(k+2) a_{k+2} - k a_k = 0\ (k \geq 1)$

有递推公式 $$a_{k+2} = \frac{k}{(k+1)(k+2)} a_k\ \ (k \geq 1)$$

A. $k$ 为偶数：由于 $a_2 = 0$，则 $a_2 = a_4 = a_6 = a_8 = \cdots = 0$，$a_0$ 待定，所以一个特解为 $y_1(x) = a_0$

B. $k$ 为奇数：$a_{k+2} = \frac{k}{(k+1)(k+2)} a_k$
$$a_3 = \frac{1}{2 \cdot 3} a_1$$
$$a_5 = \frac{3}{4 \cdot 5} a_3 = \frac{3}{4 \cdot 5} \cdot \frac{1}{2 \cdot 3} a_1$$
$$a_7 = \frac{5}{6 \cdot 7} a_5 = \frac{5}{6 \cdot 7} \cdot \frac{3}{4 \cdot 5} \cdot \frac{1}{2 \cdot 3} a_1$$

定义 $(2n)!! = 2 \cdot 4 \cdot 6 \cdot 8 \cdots 2n,\ (2n-1)!! = 1 \cdot 3 \cdot 5 \cdot 7 \cdots (2n-1)$

## Figure & Layout Description

该PPT页面为手写数学推导内容，背景为浅灰色方格纸（网格线间距均匀，呈正方形格子）。所有文字和公式均为黑色手写体，书写工整且层次分明。页面顶部左侧标注章节号"15.3"，其下方为问题编号"(1)"及微分方程$y'' - xy' = 0$。推导过程从上至下垂直排列，包含以下视觉层次：

1. **标题区域**：左上角用较大字体书写"15.3"，下方紧接问题编号"(1)"和主方程
2. **理论分析区**：包含$p(x)$和$q(x)$的定义及"常点"判定说明，文字居中偏左
3. **公式推导区**：核心幂级数解法推导占页面主体，公式分行排列，每步推导单独成行
   - 幂级数假设式作为独立行间公式
   - 一阶/二阶导数表达式并列显示
   - 代入方程后的展开过程分三行展示，含详细求和符号变换
   - 递推关系推导包含多项式合并步骤
4. **分类讨论区**：用"A"和"B"标注偶数项/奇数项分析，奇数项推导包含三级递推展开
5. **定义区**：页面底部给出双阶乘定义，包含两个并列公式

公式中求和符号$\sum$、下标$k$、系数$a_k$等数学符号书写规范，关键步骤用波浪线标注（如$k=0,k=1$时项为0的说明）。整体排版遵循"问题-假设-推导-结论"逻辑流，重要结论（如$a_2=0$）用文字明确标注。

<CTX>
{
   "topic": "二阶线性微分方程的幂级数解法",
   "keywords": ["常点", "幂级数展开", "递推公式", "双阶乘", "微分方程特解"],
   "summary": "通过幂级数展开法求解微分方程 $y'' - xy' = 0$，推导出系数递推关系并分析偶数项与奇数项的通项规律",
   "pending_concepts": ["贝塞尔函数与幂级数解的关联", "双阶乘在特殊函数中的应用", "非正则奇点的处理方法"]
}
</CTX>

---

# Slide 8

则 $a_{2k+1} = \frac{(2k-1)!!}{(2k+1)!!} a_1$

所以一个特解为 $y_2(x) = a_1 x + \sum_{k=1}^{\infty} \frac{(2k-1)!!}{(2k+1)!!} a_1 x^{2k+1}$

$y = y_1 + y_2 = a_0 + a_1 x + \sum_{k=1}^{\infty} \frac{(2k-1)!!}{(2k+1)!!} a_1 x^{2k+1}$

(2). $y'' - x^2 y' = 0$

$p(x) = -x^2$, $q(x) = 0$, 在 $x=0$ 处是有界值, 则 $x=0$ 是常点

在 $x=0$ 的邻域内, 设解为 $y(x) = \sum_{k=0}^{\infty} a_k x^k$

则 $y' = \sum_{k=0}^{\infty} k a_k x^{k-1}$, $y'' = \sum_{k=0}^{\infty} (k-1)k a_k x^{k-2}$

$y'' - x^2 y' = \sum_{k=0}^{\infty} (k-1)k a_k x^{k-2} - \sum_{k=0}^{\infty}k a_k x^{k+1}$

$= \sum_{k=0}^{\infty} (k-1)k a_k x^{k-2} - \sum_{k=0}^{\infty} k a_k x^{k+1}$ 

$= 2a_2 + 6a_3 x + \sum_{k=4}^{\infty} (k-1)k a_k x^{k-2} - \sum_{k=1}^{\infty} k a_k x^{k+1}$

$= 2a_2 + 6a_3 x + \sum_{k=1}^{\infty} (k+2)(k+3) a_{k+3} x^{k+1} - \sum_{k=1}^{\infty} k a_k x^{k+1}$

$= 2a_2 + 6a_3 x + \sum_{k=1}^{\infty} \left[ (k+2)(k+3) a_{k+3} - k a_k \right] x^{k+1} = 0$

则 $a_2 = 0$, $a_3 = 0$, $(k+2)(k+3) a_{k+3} - k a_k = 0$ ($k \geq 1$)

有三组解, $k = 3m+1$, $k = 3m+2$, $k = 3m+3$

| 1 | 4 | 7 |
|---|---|---|
| 2 | 5 | 8 |
| 3 | 6 | 9 |

## Figure & Layout Description
图片为手写数学推导的单页PPT，背景为浅灰色网格纸（类似笔记本纸张），文字为黑色墨水书写。内容分为上下两部分：上半部分延续前页关于双阶乘递推关系的推导，包含三个连续的数学公式（系数递推式、特解表达式、通解表达式），公式中使用标准数学符号如双阶乘!!、无穷级数求和∑；下半部分以"(2)."开头，开始新微分方程$y'' - x^2 y = 0$的求解过程，包含方程定义、常点判定、幂级数假设、导数展开、级数代入、项重组、系数递推关系推导。推导过程中有手写注释（如"在x=0处是有界值"）和下划线标注关键步骤。页面右下角有一个3×3数字表格，内容为1-9按列排列。整体布局为纵向书写，公式与文字混合，部分推导步骤有笔误修正痕迹（如$x^2 y$项误写为含$k a_k$的表达式）。无彩色元素，纯黑白手写内容，字迹工整但有自然书写倾斜。

<CTX>
{
   "topic": "二阶线性微分方程的幂级数解法（续）：含$x^2$项的方程求解",
   "keywords": ["常点判定", "幂级数代入", "系数递推关系", "三组解结构", "项重组技巧"],
   "summary": "针对$y'' - x^2 y = 0$建立幂级数解法，推导出三组独立系数递推关系并展示解的分组结构",
   "pending_concepts": ["三组解对应的具体通解形式", "非整数指数幂级数解的处理", "解的收敛半径分析"]
}
</CTX>

---

# Slide 9

但由于 $u_2 = a_3 = 0$，后两组解 $k = 3m+2, 3m+3$ 都为 $0$.

对第一组解为 $k = 3m+1$，$(k+2)(k+3)a_{k+3} - ka_k = 0 \ (k \geq 1)$

$$
a_{k+3} = \frac{k}{(k+2)(k+3)} a_k \quad (k \geq 1)
$$

$$
a_4 = \frac{1}{3 \cdot 4} a_1
$$

$$
a_7 = \frac{4}{6 \cdot 7} a_4 = \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 7} = \frac{1}{3^2 \cdot 1 \cdot 2 \cdot 7}
$$

$$
a_{10} = \frac{7}{9 \cdot 10} a_7 = \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 10} = \frac{1}{3^3 \cdot 1 \cdot 2 \cdot 3 \cdot 10}
$$

$$
a_{13} = \frac{10}{12 \cdot 13} a_{10} = \frac{10}{12 \cdot 13} \cdot \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 12 \cdot 13} = \frac{1}{3^4 \cdot 1 \cdot 2 \cdot 3 \cdot 4 \cdot 13}
$$

$$
a_{16} = \frac{13}{15 \cdot 16} a_{13} = \frac{13}{15 \cdot 16} \cdot \frac{10}{12 \cdot 13} \cdot \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 12 \cdot 15 \cdot 16} = \frac{1}{3^5 \cdot 1 \cdot 2 \cdot 3 \cdot 4 \cdot 5 \cdot 16}
$$

$$
a_{3m+1} = \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1
$$

$$
y_1 = \sum_{m=0}^{\infty} \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1 x^{3m+1}
$$

$$
y_2 = a_0
$$

$$
y = y_1 + y_2 = a_0 + \sum_{m=0}^{\infty} \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1 x^{3m+1}
$$

## Figure & Layout Description

手写内容呈现在方格纸背景上，整体为竖向排列的数学推导过程。顶部有结论性语句，中间部分为递推关系的逐步推导，底部为通解表达式。文字和公式全部为黑色手写体，部分中间推导步骤中的错误计算项被红色笔迹划掉（如 $a_7$、$a_{10}$、$a_{13}$、$a_{16}$ 推导中的中间系数）。公式结构清晰，分步骤展示从 $a_4$ 到 $a_{16}$ 的递推过程，每行公式对齐整齐。关键递推关系 $(k+2)(k+3)a_{k+3} - ka_k = 0$ 以较大字体书写，作为推导核心。最后归纳出通项公式 $a_{3m+1}$ 和级数解 $y_1$、$y_2$，并给出完整通解表达式。红色划线部分显示了计算过程中的修正痕迹，体现推导的动态过程。

<CTX>
{
   "topic": "二阶线性微分方程幂级数解的通解构造：第一组解的显式表达式推导",
   "keywords": ["系数递推关系", "三组解结构", "通解构造", "项重组技巧", "显式表达式"],
   "summary": "本页完成第一组非零解的递推关系求解，通过归纳法得到显式通项公式并构造出完整通解形式",
   "pending_concepts": ["解的收敛半径具体计算", "非整数指数幂级数解的处理方法", "三组解中零解的严格证明"]
}
</CTX>

---

# Slide 10

$$
15.5 \quad (1-x^2)y'' - xy' + n^2 y = 0 \ , \ n = 1, 2, 3, \dots
$$

$$
y'' - \frac{x}{1-x^2} y' + \frac{n^2}{1-x^2} y = 0 \ ,
$$

$$
p(x) = -\frac{x}{1-x^2} \quad q(x) = \frac{n^2}{1-x^2} = \frac{\frac{1}{2}n^2}{x-1} + \frac{-\frac{1}{2}n^2}{x+1}
$$
$$
 \frac{1}{1-x^2}= \frac{\frac{1}{2}}{x-1} + \frac{-\frac{1}{2}}{x+1}
$$

$x = \pm 1$ 都是 $p(x), q(x)$ 的一阶极点，在 $x=0$ 处 $p,q$ 有限。

所以 $x=0$ 是方程的常点，在 $|x|<1$ 内

设 $y = \sum_{k=0}^{\infty} a_k x^k \quad (|x|<1)$

$$
y' = \sum_{k=1}^{\infty} k a_k x^{k-1} \ , \ y'' = \sum_{k=2}^{\infty} k(k-1) a_k x^{k-2} \ .
$$

$$
(1-x^2)y'' = \sum_{k=2}^{\infty} k(k-1)a_k x^{k-2} - \sum_{k=2}^{\infty} k(k-1)a_k x^k
$$
$$
= \sum_{k=0}^{\infty} (k+2)(k+1)a_{k+2} x^k - \sum_{k=2}^{\infty} k(k-1)a_k x^k
$$
$$
= 2 \cdot 1 a_2 + 3 \cdot 2 a_3 x + \sum_{k=2}^{\infty} (k+2)(k+1)a_{k+2} x^k - \sum_{k=2}^{\infty} k(k-1)a_k x^k
$$

$$
-xy' = -\sum_{k=1}^{\infty} k a_k x^k = -a_1 x - \sum_{k=2}^{\infty} k a_k x^k
$$

$$
n^2 y = \sum_{k=0}^{\infty} n^2 a_k x^k = n^2 a_0 + n^2 a_1 x + \sum_{k=2}^{\infty} n^2 a_k x^k
$$

$$
(1-x^2)y'' - xy' + n^2 y
$$
$$
= n^2 a_0 + 2 a_2 + [6 a_3 + (n^2 - 1)a_1]x + \sum_{k=2}^{\infty} \left[ (k+2)(k+1)a_{k+2} - k(k-1)a_k - k a_k + n^2 a_k \right] x^k \ .
$$

## Figure & Layout Description
手写内容呈现在方格稿纸上，使用黑色墨水书写。整体布局为纵向排列的数学推导过程，从上至下分为五个逻辑区块：1) 方程标题与标准形式转换（顶部居中）；2) 系数函数p(x)和q(x)的定义与部分分式分解（中部偏上）；3) 奇点分析结论（中部）；4) 幂级数解假设与导数展开（中下部）；5) 代入原方程后的项重组过程（底部）。公式中分式结构使用水平分数线，求和符号∑带有明确上下限，下标字母与数字区分清晰。文字说明穿插在公式之间，使用中文书写，字迹工整但存在少量连笔现象。网格线为浅灰色，作为书写辅助线贯穿整个页面。

<CTX>
{
   "topic": "Legendre方程在常点x=0处的幂级数解构造：系数递推关系建立",
   "keywords": ["常点判定", "幂级数展开", "项重组技巧", "系数递推关系", "Legendre方程"],
   "summary": "本页通过将Legendre方程转化为标准形式，验证x=0为常点后建立幂级数解，完成代入方程后的项重组并得到递推关系初始形式",
   "pending_concepts": ["递推关系的通解求解", "收敛半径的严格证明", "多项式解与无穷级数解的分界条件"]
}
</CTX>

---

# Slide 11

$$
= \sum_{k=0}^{\infty} \left[ (k+2)(k+1)a_{k+2} - \left[ k(k-1) + k - n^2 \right] a_k \right] x^k
$$

$$(1 - x^2)y'' - xy' + n^2 y = 0 \implies$$

$$(k+2)(k+1)a_{k+2} - \left[ k(k-1) + k - n^2 \right] a_k = 0 \quad (k \geq 0)$$

$$\implies a_{k+2} = \frac{k^2 - k + k = n^2}{(k+2)(k+1)} a_k = \frac{(k-n)(k+n)}{(k+2)(k+1)} a_k \quad (k \geq 0), \quad a_{n+2} = 0$$

分为两族，$k=2m$，$k=2m+1$，$m=0,1,2,3\cdots$

A 假设 $n$ 为偶数

① $k=2m$ 时

$m=1$ $a_2 = \frac{(0-n)(0+n)}{2 \cdot 1} a_0$

$m=2$ $a_4 = \frac{(2-n)(2+n)}{4 \cdot 3} a_2 = \frac{(2-n)(2+n)}{4 \cdot 3} \frac{(0-n)(0+n)}{2 \cdot 1} a_0$

$m=3$ $a_6 = \frac{(4-n)(4+n)}{6 \cdot 5} a_4 = \frac{(4-n)(4+n)}{6 \cdot 5} \frac{(2-n)(2+n)}{4 \cdot 3} \frac{(0-n)(0+n)}{2 \cdot 1} a_0$

$$a_{2m} = (-1)^m \cdot \frac{(n)!!}{(n-2m)!!} \cdot \frac{(n+2m-2)!!}{(n-2)!!} \cdot \frac{1}{(2m)!} a_0$$

$$= (-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 \quad (2m \leq n)$$

其中 $a_n = (-1)^{\frac{n}{2}} n \cdot (2n-2)!! \cdot \frac{1}{n!} a_0$ （$2m = n$ 时）

再下一个 $a_{n+2} = 0$，往后全为 $0$。

$$a_{2m} = 
\begin{cases} 
a_0 & (m=0) \\
(-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 & (2m \leq n, m \geq 1) \\
0 & (2m > n)
\end{cases}$$

## Figure & Layout Description
图片为手写数学推导内容，背景是标准方格纸（1cm×1cm网格），整体为黑白手写体。内容从上至下垂直排列，分为四个主要区域：顶部是幂级数展开的求和公式（行间公式），占据第一行；第二行是Legendre方程的标准形式；第三行开始是递推关系的推导过程，包含多个等式和条件说明；中下部详细展示了当$k=2m$时的系数递推计算，包括$m=1,2,3$的具体计算步骤；底部是通项公式和分段函数表达式。文字与公式混合排布，公式中包含下标（如$a_{k+2}$）、双阶乘符号（!!）和条件括号（如$(k \geq 0)$）。手写笔迹清晰但有轻微倾斜，部分公式有修改痕迹（如$k^2 - k + k = n^2$处有重写迹象）。右侧有少量辅助计算的碎片化公式（如$\frac{n!!}{(n-6)!!}$等），与主推导线并列但未整合。整体布局符合数学推导的逻辑顺序，无颜色区分，仅通过换行和缩进体现层级。

<CTX>
{
   "topic": "Legendre方程在n为偶数时的多项式解构造：递推关系求解与通项公式推导",
   "keywords": ["递推关系求解", "多项式解", "双阶乘表示", "分段系数表达式", "n为偶数条件"],
   "summary": "本页通过递推关系求解得到当n为偶数时的多项式解形式，明确系数通项公式及分段表达式，揭示解在2m > n时截断为多项式",
   "pending_concepts": ["奇数n的解构造", "Legendre多项式标准化", "无穷级数解的收敛性验证"]
}
</CTX>

---

# Slide 12

而奇数时类似 $a_{k+2} = \frac{k^2 - k + k - n^2}{(k+2)(k+1)} a_k = \frac{(k-n)(k+n)}{(k+2)(k+1)} a_k \quad (k > 0)$.

$m=1 \quad a_3 = \frac{(1-n)(1+n)}{3 \cdot 2} a_1$

$m=2 \quad a_5 = \frac{(3-n)(3+n)}{5 \cdot 4} a_3 = \frac{(3-n)(3+n)}{5 \cdot 4} \frac{(1-n)(1+n)}{3 \cdot 2} a_1$

$m=3 \quad a_7 = \frac{(5-n)(5+n)}{7 \cdot 6} a_5 = \frac{(5-n)(5+n)}{7 \cdot 6} \frac{(3-n)(3+n)}{5 \cdot 4} \frac{(1-n)(1+n)}{3 \cdot 2} a_1$

$$a_{2m+1} = (-1)^m \cdot \frac{(n-1)!!}{(n-2m-1)!!} \cdot \frac{(n+2m-1)!!}{(n-1)!!} \cdot \frac{1}{(2m+1)!} a_1$$

$$= (-1)^m \frac{(n+2m-1)!!}{(n-2m-1)!!} \cdot \frac{1}{(2m+1)!} a_1$$

当 $2m < n$ 时，即 $2m < n+1, \, 2m \leq n$

当 $2m = n$ 时，$a_{n+1} = (-1)^{\frac{n}{2}} \frac{(2n-1)!!}{(-1)!!} \cdot \frac{1}{(n+1)!} a_1$

$a_{n+1} = (-1)^{\frac{n}{2}} (2n-1)!! \cdot \frac{1}{(n+1)!} a_1$

再往后，$a_{k+2} = \frac{(k-n)(k+n)}{(k+2)(k+1)} a_k$，$k > n$ 恒为正

则 $2m > n$，即 $2m > n+2$ 时

$$a_{2m+1} = (-1)^m \frac{(n+2m-1)(n+2m-2) \cdots 3 \cdot 1 \cdot (-1) \cdot (-3) \cdots (n-2m+1)(n-2m-1)}{(n-2m-1)} \cdot \frac{1}{(2m+1)!} a_1$$

共有 $\frac{|n-2m-1|+1}{2}$ 个

提出-1来

## Figure & Layout Description

图片为手写数学推导内容，书写在浅灰色方格坐标纸上（网格线清晰可见，每格约5mm×5mm）。所有文字和公式使用黑色墨水书写，字迹工整但带有手写特征。内容从上至下垂直排列，分为四个主要区域：

1. **顶部区域**：包含递推关系通式，文字"而奇数时类似"后接两行公式，第一行公式右侧标注$(k>0)$。公式中分式结构清晰，分子分母用水平线表示。

2. **中部左侧**：三行分情况讨论（m=1, m=2, m=3），每行以"m="开头，后接对应$a_{2m+1}$的表达式，表达式包含多层分数和乘积。公式中下标（如$a_3, a_5$）和括号内表达式（如$(1-n)(1+n)$）书写规范。

3. **中部右侧**：包含通项公式推导，分为两行。第一行是完整通项公式，第二行是简化形式。公式中双阶乘符号"!!"和阶乘"!"清晰可辨。右侧有手写注释，包含分子分母的展开式$(n+5)(n+3)\cdots$和$(n-1)(n-3)\cdots$，用斜线分隔。

4. **底部区域**：包含条件讨论和最终推导。左侧有"当$2m<n$时"和"当$2m=n$时"两段条件说明，右侧有垂直排列的补充条件（$2m+1<n$等）。最下方是"再往后"开始的递推关系讨论，包含长分式和"共有...个"的计数说明。

整体布局为左对齐为主，公式部分适当缩进以体现层次。关键符号如"!!"、"(-1)^m"等用加重笔触书写，部分括号和分数线略长于标准印刷体。无彩色元素，纯黑白手写内容。

<CTX>
{
   "topic": "Legendre方程在n为奇数时的多项式解构造：递推关系求解与通项公式推导",
   "keywords": ["递推关系求解", "多项式解", "双阶乘表示", "分段系数表达式", "n为奇数条件", "奇偶分情况讨论"],
   "summary": "本页通过递推关系推导了n为奇数时的多项式解形式，建立奇数项系数通项公式并分析截断条件，完善了Legendre方程多项式解的奇偶分情况理论体系",
   "pending_concepts": ["Legendre多项式标准化", "无穷级数解的收敛性验证", "奇偶解的统一表达形式"]
}
</CTX>

---

# Slide 13

$$
-(-1)^m \cdot \frac{(n+2m-1)!! \cdot (2m+1-n)!! \cdot (-1)^{\frac{2m+1-n+1}{2}}}{|n-2m-1|}
$$

$$
\cdot \frac{1}{(2m+1)!} a_1
$$

$$
= (-1)^m \cdot (-1)^{\frac{n}{2}} \cdot (n+2m-1)!! (2m-n-1)!! \cdot \frac{1}{(2m+1)!} a_1 \quad (2m \ge n+2)
$$

$$
a_{2m+1} = 
\begin{cases} 
a_1 & (m=0) \\
(-1)^m \dfrac{(n+2m-1)!!}{(n-2m-1)!!} \cdot \dfrac{1}{(2m+1)!} a_1 & \left(1 \le m \le \dfrac{n}{2}\right) \\
(-1)^{\frac{n}{2}} (n+2m-1)!! (2m-n-1)!! \cdot \dfrac{1}{(2m+1)!} a_1 & \left(m \ge \dfrac{n}{2} + 1\right)
\end{cases}
$$

所以方程解为 (n为偶数)。

$$
y_0 = a_0 + \sum_{m=1}^{\frac{n}{2}} (-1)^m \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 x^{2m}
$$

$$
y_1 = a_1 x + \sum_{m=1}^{\frac{n}{2}} (-1)^m \frac{(n+2m-1)!!}{(n-2m-1)!!} \cdot \frac{1}{(2m+1)!} a_1 x^{2m+1} + \sum_{m=\frac{n}{2}+1}^{\infty} (-1)^{\frac{n}{2}} (n+2m-1)!! (2m-n-1)!! \cdot \frac{1}{(2m+1)!} a_1 x^{2m+1}
$$

## Figure & Layout Description
图片为手写数学推导内容，书写在标准方格稿纸上（20×20网格），背景为白色方格纸，文字为黑色墨水手写体。整体布局为垂直排列的数学公式和文字说明，从上至下分为四个逻辑区域：1) 顶部是递推关系的推导过程，包含分数形式的双阶乘表达式和指数运算；2) 中部是分段函数定义，使用大括号明确区分三种情况（m=0、1≤m≤n/2、m≥n/2+1），其中分段条件用括号标注在右侧；3) 下部是结论性文字"所以方程解为 (n为偶数)"，采用手写汉字标注；4) 最底部是两个级数解表达式y₀和y₁，包含求和符号、双阶乘和幂级数项。所有公式均采用手写数学符号，包括双阶乘(!!)、绝对值符号、求和符号(∑)和分段函数大括号。公式中的下标和上标均清晰手写，如"2m+1"作为下标时字体略小但清晰可辨。整体视觉层次分明，推导过程与最终解表达式通过垂直间距自然分隔，关键条件标注在公式右侧，符合数学推导笔记的典型排版风格。

<CTX>
{
   "topic": "Legendre方程在n为偶数时的多项式解构造：递推关系求解与通项公式推导",
   "keywords": ["递推关系求解", "多项式解", "双阶乘表示", "分段系数表达式", "n为偶数条件", "奇偶分情况讨论"],
   "summary": "本页通过递推关系推导了n为偶数时的多项式解形式，建立偶数项系数通项公式并给出完整解表达式，完善了Legendre方程多项式解的奇偶分情况理论体系",
   "pending_concepts": ["Legendre多项式标准化", "无穷级数解的收敛性验证", "奇偶解的统一表达形式"]
}
</CTX>

---

# Slide 14

n为奇数时，$a_{k+2} = \frac{(k-n)(k+n)}{(k+2)(k+1)} a_k$

当 $2m+1-2=n$ 时  
奇数项 $a_{2m+1}$，$2m+1=n+2 \Rightarrow m = \frac{n+1}{2}$  
$a_{n+2}=0$，此时 $m=\frac{n+1}{2}$ 开始截断  

而偶数项 $a_{2m} \neq 0$ 不会截断  

① $a_{2m}$，考察偶数项：  
$$
a_{2m} = 
\begin{cases} 
a_0 & (m=0) \\
(-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 & (m \geq 1 \text{ 且 } m \leq \frac{n-1}{2}) \\
? & (m > \frac{n+1}{2})
\end{cases}
$$
$n-2m > 0$ 时  
$n > 2m$  
$2m < n$  
$2m \leq n-1$

当 $m > \frac{n+1}{2}$ 时  
$$
a_{2m} = (-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0
$$
提出 $(-1)$  
共有 $\frac{|n-2m+2|+1}{2} = \frac{2m-2-n+1}{2} = \frac{2m-1-n}{2}$  
$$
= (-1)^m \cdot n \cdot \frac{(n+2m-2)(n+2m-4)\cdots 5\cdot3\cdot1 \cdot (-1)\cdot(-3)\cdot(-5)\cdots (n-2m+2)(n-2m)}{(n-2m)} \cdot \frac{1}{(2m)!} a_0
$$
$$
= (-1)^m \cdot n \cdot (n+2m-2)!! \cdot (-1)^{\frac{2m-2-n}{2}} \cdot (2m-2-n)!! \cdot \frac{1}{(2m)!} a_0
$$
$$
= (-1)^{m + \frac{2m-2-n}{2}} n \cdot (n+2m-2)!! \cdot (2m-2-n)!! \cdot \frac{1}{(2m)!} a_0
$$
$$
= (-1)^{\frac{1+n}{2}} n \cdot (n+2m-2)!! \cdot (2m-2-n)!! \cdot \frac{1}{(2m)!} a_0
$$

## Figure & Layout Description
图片为手写数学推导稿，绘制在浅灰色网格背景上（类似方格笔记本）。整体布局为垂直排列的数学公式和文字说明，从上至下分为四个逻辑区块：1) 顶部为n为奇数时的递推关系式；2) 中上部讨论奇数项截断条件，包含条件等式和推导步骤；3) 中部明确偶数项不截断的结论，并以带圈数字①标注偶数项分析；4) 底部为偶数项系数的分段表达式及当m > (n+1)/2时的详细推导过程。文字为黑色手写体，公式中包含双阶乘符号"!!"、分段函数大括号、分数结构和多层括号。推导过程中有手写注释（如"提出(-1)"、"共有"）用箭头指向对应公式部分。关键条件标注在公式右侧（如"n-2m > 0 时"、"2m < n"），部分区域有手写修改痕迹（如"3"的标注）。整体字迹清晰，公式结构完整，但部分下标和符号因手写风格需结合上下文辨认。

<CTX>
{
   "topic": "Legendre方程在n为奇数时的多项式解构造：递推关系截断条件与偶数项通项公式推导",
   "keywords": ["奇数项截断条件", "偶数项通项公式", "双阶乘展开", "分段系数表达式", "n为奇数条件", "符号指数化简"],
   "summary": "本页补充推导了n为奇数时Legendre方程的解，重点分析奇数项截断条件及偶数项系数的完整通项公式，通过双阶乘展开和符号化简建立与偶数解的对应关系",
   "pending_concepts": ["奇偶解的统一标准化形式", "截断条件的几何意义", "双阶乘表达式与Gamma函数的关联"]
}
</CTX>

---

# Slide 15

综上，
$$
a_{2m} = 
\begin{cases} 
a_0 & (m=0) \\
(-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 & \left(m \geq 1 \text{ 且 } m \leq \frac{n-1}{2}\right) \\
(-1)^{\frac{1+m}{2}} n \cdot \frac{(n+2m-2)!! (2m-2-n)!!}{(2m)!} a_0 & \left(m > \frac{n+1}{2}\right)
\end{cases}
$$
而奇数项在 $m = \frac{n+1}{2}$ 截断
$$
a_{2m+1} = 
\begin{cases} 
a_1 & (m=0) \\
(-1)^m \frac{(n+2m-1)!!}{(n-2m-1)!!} \cdot \frac{1}{(2m+1)!} a_1 & \left(1 \leq m \leq \frac{n-1}{2}\right) \\
0 & \left(m > \frac{n+1}{2}\right)
\end{cases}
$$
($n$ 为奇数)、  
故解为 
$$
y_0 = a_0 + \sum_{m=1}^{\frac{n-1}{2}} (-1)^m n \cdot \frac{(n+2m-2)!!}{(n-2m)!!} \cdot \frac{1}{(2m)!} a_0 x^{2m} + \sum_{m=\frac{n+1}{2}}^{\infty} (-1)^{\frac{1+m}{2}} n \cdot \frac{(n+2m-2)!! (2m-2-n)!!}{(2m)!} a_0 x^{2m}
$$
$$
y_1 = a_1 x + \sum_{m=1}^{\frac{n-1}{2}} (-1)^m \frac{(n+2m-1)!!}{(n-2m-1)!!} \cdot \frac{1}{(2m+1)!} a_1 x^{2m+1}
$$
(以上方法是用了双阶乘的延拓，定义 $\frac{n!!}{(-m)!!} = \frac{n(n-2)(n-4)\cdots 3 \cdot 1 \cdot (-1) \cdot (-3) \cdots (-m)}{-m}$)  
即 $\frac{7!!}{(-5)!!} = \frac{7 \cdot 5 \cdot 3 \cdot 1 \cdot (-1) \cdot (-3) (-5) \cdot (-7)\cdots}{(-5) \cdot (-7)\cdots}=\frac{7 \cdot 5 \cdot 3 \cdot 1 \cdot (-1) \cdot (-3) }{1}$

## Figure & Layout Description
图片为手写数学推导内容，绘制在浅灰色方格坐标纸上，背景为标准方格网格（约1cm×1cm）。文字全部为黑色墨水手写体，字迹清晰但略带倾斜。内容按垂直顺序排列：顶部为"综上，"引导的偶数项系数 $a_{2m}$ 分段定义（含三行分段公式）；中部为"而奇数项在、$m = \frac{n+1}{2}$ 截断"说明及奇数项系数 $a_{2m+1}$ 分段定义；下部标注"($n$ 为奇数)"后给出两个级数解 $y_0$ 和 $y_1$ 的完整表达式；最底部为双阶乘延拓的定义说明及具体数值示例。公式中双阶乘符号"!!"清晰可见，求和符号$\sum$下标范围明确标注。所有文字与公式均沿水平方向书写，无彩色标记或图形元素，整体布局为典型的数学推导笔记样式，重点公式通过分段大括号结构突出显示。

<CTX>
{
   "topic": "Legendre方程n为奇数时的奇偶解通项公式与双阶乘延拓定义",
   "keywords": ["奇数项截断条件", "偶数项通项公式", "双阶乘延拓", "分段系数表达式", "级数解构造", "符号指数化简"],
   "summary": "本页完整推导了n为奇数时Legendre方程的奇偶解通项公式，通过双阶乘延拓明确定义了负数双阶乘的运算规则，并给出具体数值验证示例",
   "pending_concepts": ["奇偶解的统一标准化形式", "双阶乘与Gamma函数的解析延拓关联", "截断条件在物理问题中的几何解释"]
}
</CTX>

---

# Slide 16

15.7 $x y'' - x y' + y = 0$，在 $x=0$ 的邻域内

$$y'' - y' + \frac{1}{x} y = 0$$

$p(x) = -1$, $q(x) = \frac{1}{x}$, $q_{-1} = 1$, $q_{-2} = 0$.

有定理可证 $y'' + p y' + q y = 0$ 解为

$$
\begin{cases}
y_1 = \sum_{k=0}^{\infty} a_k x^{k+s_1} \\
y_2 = \sum_{k=0}^{\infty} b_k x^{k+s_2}
\end{cases}
$$

$s_1, s_2$ 为 $s(s-1) + s p_{-1} + q_{-2} = 0$ 之两根

$y_1' = \sum_{k=0}^{\infty} (k+s_1) a_k x^{k+s_1 -1}$

$y_1'' = \sum_{k=0}^{\infty} (k+s_1)(k+s_1 -1) a_k x^{k+s_1 -2}$

$p(x) = \frac{p_{-1}}{x} + \cdots$

$q(x) = \frac{q_{-2}}{x^2} + \frac{q_{-1}}{x} + \cdots$

各项最低阶为 $y_1'' \sim s_1(s_1-1) a_k x^{s_1-2}$

$p y' \sim p_{-1} s_1 a_k x^{s_1-2}$

$q y \sim q_{-2} a_k x^{s_1-2}$

故有 $s_1(s_1-1) + s_1 p_{-1} + q_{-2} = 0$

$s_2$ 同理

$s_1, s_2$ 为 $s(s-1) + s p_{-1} + q_{-2} = 0$ 之两根

当 $s_1 - s_2$ 为整数时，$y_2$ 变为 $A y_1(x) \ln x + \sum_{k=0}^{\infty} b_k x^{k+s_2}$

## Figure & Layout Description
手写数学推导内容呈现在方格纸背景上，黑色墨水书写。内容从上至下分为四个逻辑区块：1) 微分方程原始形式及化简（15.7题号突出显示）；2) 系数函数定义（p(x), q(x)及其极点系数）；3) 级数解结构定理（含大括号方程组）；4) 指标方程推导过程（包含导数展开、最低阶项分析及最终特征方程）。公式使用标准手写体，求和符号Σ清晰可见，下标/上标通过位置区分（如s₁, s₂）。关键结论"有定理可证"使用加粗手写体，"故有"等推导连接词以常规字体书写。整页无彩色标记，仅通过文字大小和排版层次区分重点。

<CTX>
{
   "topic": "Frobenius方法求解二阶线性微分方程的指标方程与级数解结构",
   "keywords": ["指标方程", "Frobenius方法", "正则奇点", "级数解构造", "整数差指标", "对数解形式"],
   "summary": "本页系统推导了Frobenius方法中指标方程的建立过程，阐明当指标差为整数时第二个线性无关解需引入对数项的必要性",
   "pending_concepts": ["收敛半径的具体确定方法", "物理问题中奇点的物理解释", "对数解系数A的计算规则"]
}
</CTX>

---

# Slide 17

综上 $y'' + py' + qy = 0$ 解的  

① 当 $s_1 - s_2 \neq$ 整数：  
$$
\begin{cases}
y_1 = \sum_{k=0}^{\infty} a_k (x - x_0)^{k+s_1} \\
y_2 = \sum_{k=0}^{\infty} b_k (x - x_0)^{k+s_2}
\end{cases}
$$  
$s_1, s_2$ 为 $s(s-1) + s p_{-1} + q_{-2} = 0$ 之两根，且 $s_2$ 为较小之根（红色标注 $s_2 < s_1$）  

② 当 $s_1 - s_2 =$ 整数：  
$$
\begin{cases}
y_1 = \sum_{k=0}^{\infty} a_k (x - x_0)^{k+s_1} \\
y_2 = A y_1(x) \ln(x - x_0) + \sum_{k=0}^{\infty} b_k (x - x_0)^{k+s_2}
\end{cases}
$$  
$s_1, s_2$ 为 $s(s-1) + s p_{-1} + q_{-2} = 0$ 之两根，且 $s_2$ 为较小之根（红色标注 $s_2 < s_1$）  

在此题中，$y'' - y' + \frac{1}{x} y = 0$，$x_0 = 0$  
$p(x) = -1$，$q(x) = \frac{1}{x}$，$q_{-1} = 1$，$q_{-2} = 0$，$p_{-1} = 0$  
故 $s_1, s_2$ 为 $s(s-1) = 0$ 两根，且 $s_2$ 为较小之根（红色标注 $s_2 < s_1$）  
所以 $s_1 = 1$，$s_2 = 0$，这里 $s_1 - s_2 = 1$ 是整数，故用 ②  
$$
\begin{cases}
y_1 = \sum_{k=0}^{\infty} a_k x^{k+1} \\
y_2 = A y_1(x) \ln x + \sum_{k=0}^{\infty} b_k x^k
\end{cases}
$$

## Figure & Layout Description  
图片为方格纸背景的手写笔记，黑色墨水书写主体内容，红色墨水标注关键条件。内容分为两大部分：  
1. **指标方程与解结构**：  
   - 以带大括号的方程组形式分两种情况讨论（$s_1-s_2 \neq$ 整数 vs $s_1-s_2 =$ 整数），每种情况包含 $y_1$ 和 $y_2$ 的级数表达式。  
   - 红色文字标注 "且 $s_2$ 为较小之根" 及 "$s_2 < s_1$"，强调根的大小关系，红色标注位于对应公式右侧。  
2. **具体应用示例**：  
   - 下方列出微分方程 $y'' - y' + \frac{1}{x}y = 0$ 的参数（$x_0=0$，$p(x)=-1$ 等），推导指标方程 $s(s-1)=0$，并明确 $s_1=1, s_2=0$。  
   - "故用 ②" 以黑色手写体标注，指示选择第二种解结构。  
整体布局为纵向排列，公式与文字交替出现，关键结论通过红色标注突出显示，手写字体工整但带有自然书写痕迹。

<CTX>
{
   "topic": "Frobenius方法中指标差为整数时的级数解构造与对数解形式",
   "keywords": ["指标方程", "Frobenius方法", "正则奇点", "级数解构造", "整数差指标", "对数解形式", "对数解系数A"],
   "summary": "本页通过具体微分方程实例演示了当指标差为整数时，第二个线性无关解需引入对数项的构造过程，并明确参数化条件",
   "pending_concepts": ["对数解系数A的计算规则"]
}
</CTX>

---

# Slide 18

$$y_1'' - y_1' + \frac{1}{x} y_1 = 0$$

$$y_1' = \sum_{k=0}^{\infty} (k+1)a_k x^k \quad y_1'' = \sum_{k=0}^{\infty} k(k+1)a_k x^{k-1} = \sum_{k=1}^{\infty} k(k+1)a_k x^{k-1}$$

$$\frac{y_1}{x} = \sum_{k=0}^{\infty} a_k x^k \quad \overset{k \to k+1}{=} \sum_{k=0}^{\infty} (k+1)(k+2)a_{k+1} x^k$$

$$y_1'' - y_1' + \frac{1}{x} y_1 = 0 \Rightarrow$$

$$\sum_{k=0}^{\infty} \left[ (k+1)(k+2)a_{k+1} - (k+1)a_k + a_k \right] x^k = 0$$

$$\sum_{k=0}^{\infty} \left[ (k+1)(k+2)a_{k+1} - k a_k \right] x^k = 0$$

$$2a_1 + \sum_{k=1}^{\infty} \left[ (k+1)(k+2)a_{k+1} - k a_k \right] x^k = 0$$

$$\Rightarrow a_1 = 0, \, (k+1)(k+2)a_{k+1} - k a_k = 0 \, (k \geq 1)$$

由此知 $a_1$ 之后全为 0

$$a_k = 0 \, (k \geq 1)$$

所以 $y_1 = \sum_{k=0}^{\infty} a_k x^{k+1} = a_0 x$

而 $y_2 = A y_1(x) \ln x + \sum_{k=0}^{\infty} b_k x^k$

$$= A a_0 x \ln x + \sum_{k=0}^{\infty} b_k x^k$$

$$y_2' = A a_0 (\ln x + 1) + \sum_{k=0}^{\infty} k b_k x^{k-1} = A a_0 (\ln x + 1) + \sum_{k=1}^{\infty} k b_k x^{k-1}$$

$$\overset{k \to k+1}{=} A a_0 (\ln x + 1) + \sum_{k=0}^{\infty} (k+1) b_{k+1} x^k$$

## Figure & Layout Description
手写数学推导内容呈现在方格纸背景上，文字和公式以黑色墨水书写。整体布局为垂直排列的推导步骤，从顶部开始依次向下展开。公式主要集中在页面中央区域，包含多行级数展开和递推关系推导。页面上半部分展示微分方程及其级数解的导数展开，中间部分是代入方程后的系数比较过程，下半部分推导对数解形式。所有公式均采用标准数学符号书写，包括求和符号（$\sum$）、下标（如$a_k$）、分数（$\frac{1}{x}$）和指数（$x^k$）。中文说明文字穿插在关键推导步骤之间，如"由此知$a_1$之后全为0"等。方格纸的浅灰色网格线作为背景，每个公式块大致占据2-3个网格高度，整体排版紧凑但层次分明。

<CTX>
{
   "topic": "Frobenius方法中指标差为整数时的级数解构造与对数解形式",
   "keywords": ["指标方程", "Frobenius方法", "正则奇点", "级数解构造", "整数差指标", "对数解形式", "对数解系数A", "递推关系"],
   "summary": "本页通过具体微分方程实例完成了当指标差为整数时第二个线性无关解的构造，推导出第一个解为一次多项式，并展示对数解的参数化形式",
   "pending_concepts": ["对数解系数A的计算规则"]
}
</CTX>

---

# Slide 19

$$y_2'' = A a_0 \frac{1}{x} + \sum_{k=0}^{\infty} k(k-1) b_k x^{k-2} = A a_0 \frac{1}{x} + \sum_{k=2}^{\infty} k(k-1) b_k x^{k-2}$$

$$\overset{k \to k+2}{=} A a_0 \frac{1}{x} + \sum_{k=0}^{\infty} (k+2)(k+1) b_{k+2} x^{k}$$

$$\frac{y_2}{x} = A a_0 \ln x + \sum_{k=0}^{\infty} b_k x^{k-1} = A a_0 \ln x + \frac{b_0}{x} + \sum_{k=0}^{\infty} b_{k+1} x^{k}$$

$$y_2'' - y_2' + \frac{1}{x} y_2 = 0 \implies$$

$$A a_0 \frac{1}{x} + \sum_{k=0}^{\infty} (k+2)(k+1) b_{k+2} x^{k} - A a_0 (\ln x + 1) - \sum_{k=0}^{\infty} (k+1) b_{k+1} x^{k} + A a_0 \ln x + \frac{b_0}{x} + \sum_{k=0}^{\infty} b_{k+1} x^{k} = 0$$

$$0 \ln x + \frac{A a_0 + b_0}{x} - A a_0 + \sum_{k=0}^{\infty} \left[ (k+2)(k+1) b_{k+2} - (k+1) b_{k+1} + b_{k+1} \right] x^k = 0$$

$$\frac{A a_0 + b_0}{x} + 2 b_2 - A a_0 + \sum_{k=1}^{\infty} \left[ (k+2)(k+1) b_{k+2} - k b_{k+1} \right] x^k = 0$$

$$\implies \begin{cases} 
A a_0 + b_0 = 0 \implies b_0 = -A a_0 \\
2 b_2 - A a_0 = 0 \implies b_2 = +\frac{1}{2} A a_0 \\
(k+2)(k+1) b_{k+2} - k b_{k+1} = 0 \quad (k \geq 1)
\end{cases}$$

$$b_{k+2} = \frac{k}{(k+2)(k+1)} b_{k+1} \quad (k \geq 1)$$

$$b_3 = \frac{1}{3 \cdot 2} b_2$$

$$b_4 = \frac{2}{4 \cdot 3} b_3 = \frac{2}{4 \cdot 3} \cdot \frac{1}{3 \cdot 2} b_2 = \frac{2! \cdot 2}{4! \cdot 3!} b_2$$

$$b_5 = \frac{3}{5 \cdot 4} b_4 = \frac{3}{5 \cdot 4} \cdot \frac{2}{4 \cdot 3} \cdot \frac{1}{3 \cdot 2} b_2 = \frac{3! \cdot 2}{5! \cdot 4!} b_2$$

$$b_6 = \frac{4}{6 \cdot 5} b_5 = \frac{4}{6 \cdot 5} \cdot \frac{3}{5 \cdot 4} \cdot \frac{2}{4 \cdot 3} \cdot \frac{1}{3 \cdot 2} b_2 = \frac{4! \cdot 2}{6! \cdot 5!} b_2$$

## Figure & Layout Description

该PPT页面为手写数学推导内容，背景为浅灰色方格纸（1cm×1cm网格）。内容以黑色墨水书写，共分11行数学推导，每行公式垂直排列。关键视觉元素包括：
1. **颜色标记**：
   - 红色下划线：标记了三个关键项（"A a₀/x"、"b₀/x"和"2b₂ - A a₀"）
   - 蓝色波浪线：标记了两个"ln x"项（"A a₀(ln x +1)"和"A a₀ ln x"）
2. **公式结构**：
   - 顶部两行展示二阶导数的级数展开与指标替换（k→k+2）
   - 中间四行展示微分方程代入过程，含红色/蓝色标记项
   - 下部五行展示系数比较结果，包含分段函数和递推关系
3. **特殊符号**：
   - 求和符号（∑）上下限清晰标注
   - 下标使用标准手写体（如b_{k+2}）
   - 递推关系中使用"⇒"箭头表示推导结果
4. **布局特征**：
   - 所有公式左对齐排列
   - 分段函数使用大括号包裹
   - 递推计算部分逐行展开b₃到b₆的具体表达式

<CTX>
{
   "topic": "Frobenius方法中指标差为整数时对数解的系数确定与递推关系",
   "keywords": ["指标差整数", "对数解系数", "递推关系", "级数解构造", "正则奇点", "二阶微分方程"],
   "summary": "本页通过具体微分方程实例推导出对数解中系数A与b₀的关系，并建立完整的递推公式体系确定所有级数系数",
   "pending_concepts": ["对数解中系数A的归一化条件", "递推关系的通项公式"]
}
</CTX>

---

# Slide 20

故 $b_k = \frac{(k-2)! \cdot 2}{k! \, (k-1)!} b_2 = \frac{2}{k! \, (k-1)} b_2 \quad (k \geq 3)$.

$b_2 = +\frac{A a_0}{2}$ 故 $b_k = \frac{A a_0}{k! \, (k-1)} \quad (k \geq 3)$.

$$
\begin{cases}
b_0 = -A a_0 \\
b_2 = +\frac{1}{2} A a_0
\end{cases}
$$

$$
y_2 = A a_0 x \ln x + \sum_{k=0}^{\infty} b_k x^k
$$

$$
= A a_0 x \ln x - A a_0 + b_1 x + \frac{1}{2} A a_0 x^2 + \sum_{k=3}^{\infty} \frac{A a_0}{k! \, (k-1)} x^k
$$

$$
y_2 = A a_0 \left( x \ln x - 1 + \sum_{k=2}^{\infty} \frac{1}{k! \, (k-1)} x^k \right) + b_1 x
$$

$$
y_1 = \sum_{k=0}^{\infty} a_k x^{k+1} = a_0 x
$$

$$
y = y_1 + y_2 = A a_0 \left( x \ln x - 1 + \sum_{k=2}^{\infty} \frac{1}{k! \, (k-1)} x^k \right) + (a_0 + b_1) x
$$

## Figure & Layout Description
图像为方格纸背景的手写数学推导，整体布局分为左右两部分：左侧为系数递推关系推导（含"故"字引导的公式链），右侧为大括号标注的边界条件。所有公式采用黑色墨水书写，关键项 $k=2$ 在两个求和式中用红色墨水突出标记。公式排列遵循从上至下的逻辑流：顶部为 $b_k$ 递推公式，中部展示 $y_2$ 的级数展开与化简过程，底部给出 $y_1$ 和通解 $y$ 的表达式。分式结构清晰显示阶乘项的约分过程，求和符号 $\sum$ 的上下限标注完整，括号嵌套层次分明。网格线作为背景辅助对齐，但不影响公式主体的可读性。

<CTX>
{
   "topic": "Frobenius方法中对数解系数的显式表达与通解构造",
   "keywords": ["指标差整数", "对数解系数", "递推关系", "级数解构造", "正则奇点", "二阶微分方程", "通解形式"],
   "summary": "通过具体计算确定对数解中系数A与b_k的显式关系，并完成通解的完整级数表达式构造",
   "pending_concepts": ["对数解中系数A的归一化条件", "递推关系的通项公式"]
}
</CTX>

---

# Slide 21

## 勒让德多项式

引入：电荷密度 $\rho(\vec{r}')$ 欲求 $\vec{r}'$ 源点在 $\vec{r}$ 场点处的电势，有

$$V(\vec{r}) = \frac{1}{4\pi\varepsilon_0} \int \rho(\vec{r}') \frac{dv'}{z}$$

带撇的是源点

由余弦公式可推得 $z^2 = r^2 + r'^2 - 2rr'\cos\theta$

提出 $r$，有 $z = r\sqrt{1 + \left(\frac{r'}{r}\right)^2 - 2\frac{r'}{r}\cos\theta}$

令 $x = \frac{r'}{r}$，有 $\frac{1}{z} = \frac{1}{r\sqrt{1 + x^2 - 2x\cos\theta}}$

$\frac{1}{z}$ 对 $x$ 展开，有

$$(1+\xi)^n = 1 + n\xi + \frac{n(n-1)}{2}\xi^2 + \cdots$$

$$(1+\xi)^{-\frac{1}{2}} = 1 - \frac{1}{2}\xi + \frac{3}{8}\xi^2$$

$$(1+x^2-2x\cos\theta)^{-\frac{1}{2}} = 1 - \frac{1}{2}x^2 + \cos\theta \cdot x + \frac{3}{8}(4x^2\cos^2\theta)$$
$$= 1 + \cos\theta \cdot x + \left(\frac{3}{2}\cos^2\theta - \frac{1}{2}\right)x^2 + \cdots$$

若令 $\cos\theta = t$，有

$$(1+x^2-2xt)^{-\frac{1}{2}} = 1 + t \cdot x + \frac{1}{2}(3t^2-1)x^2 + \cdots$$

令右侧为 $= \sum_{l=0}^{\infty} P_l(t)x^l$

$$P_0(t) = 1$$
$$P_1(t) = t$$
$$P_2(t) = \frac{1}{2}(3t^2-1)$$
$$\vdots$$

## Figure & Layout Description

该图像是一张手写笔记，背景为方格纸。页面左上角标注"16章"，下方是标题"勒让德多项式"。左侧有一个手绘示意图：一个不规则闭合曲线表示电荷分布区域，内部标有"dv'"和源点位置"$\vec{r}'$"，从原点"O"到源点有一条线段，标注"θ"角；从原点到场点有一条红色箭头线段"$\vec{r}$"，从源点到场点有一条红色箭头线段"$\vec{z}$"。公式推导部分从上到下依次排列，包含多行数学表达式和文字说明。文字主要为黑色墨水书写，图中的$\vec{r}$和$\vec{z}$向量用红色标注。页面整体布局清晰，左侧为示意图，右侧为公式推导，文字与公式交替排列。字迹工整，数学符号规范，包括积分符号、希腊字母、上下标等。页面右上部分有部分空白区域，整体为典型的物理或数学课程笔记格式。

<CTX>
{
   "topic": "勒让德多项式的生成函数推导与正交多项式性质",
   "keywords": ["勒让德多项式", "生成函数", "电势展开", "正交多项式", "球坐标系", "多极展开"],
   "summary": "通过电势的多极展开推导勒让德多项式的生成函数表达式，并给出前几项多项式显式形式",
   "pending_concepts": ["勒让德多项式的正交性证明", "多极展开的物理意义", "高阶勒让德多项式的递推关系"]
}
</CTX>

---

# Slide 22

我们再尝试推导 任意阶的$P_l(t)$表达式.

$$f(x) = (1 + x^2 - 2xt)^{-\frac{1}{2}} = \sum_{l=0}^{\infty} P_l(t) x^l$$

利用洛朗级数 $f(x) = \sum_{k=-\infty}^{\infty} a_k (x - x_0)^k$, $a_k = \frac{f^{(k)}(x_0)}{k!}$

$$f(x_0) = \frac{1}{2\pi i} \oint \frac{f(\zeta)}{\zeta - x_0} d\zeta$$
$$a_k = \frac{1}{2\pi i} \oint \frac{f(\zeta)}{(\zeta - x_0)^{k+1}} d\zeta$$
$$f'(x_0) = \frac{1}{2\pi i} \oint \frac{f(\zeta)}{(\zeta - x_0)^2} d\zeta$$
$$f^{(n)}(x_0) = \frac{n!}{2\pi i} \oint \frac{f(\zeta)}{(\zeta - x_0)^{n+1}} d\zeta$$

$x_0 = 0$.

故 $P_l(t) = \frac{1}{2\pi i} \oint \frac{f(\zeta)}{\zeta^{l+1}} d\zeta$

$$= \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + \zeta^2 - 2\zeta t}} \cdot \frac{1}{\zeta^{l+1}} d\zeta \quad \sim \frac{f^{(l)}(0)}{l!}$$

已知 $P_l(t) = \frac{1}{l! 2^l} \frac{d^l}{dx^l} (x^2 - 1)^l$

$$\sim \frac{1}{2\pi i} \oint \frac{\left(\frac{z^2 - 1}{z - t}\right)^l}{(z - t)^{l+1}} dz \quad \sim \frac{1}{z^2 - 1} \left(\frac{z^2 - 1}{z - t}\right)^{l+1} \sim \left(\frac{1}{\zeta}\right)^{l+1}$$

令 $\zeta = 2 \frac{z - t}{z^2 - 1}$ ($z$ 是为辅助方)

$$1 + \zeta^2 - 2\zeta t = 1 + 4 \frac{(z - t)^2}{(z^2 - 1)^2} - 4 \frac{z - t}{(z^2 - 1)} \cdot t$$
$$= \frac{(z^2 - 1)^2 + 4(z - t)^2 - 4(z - t)t(z^2 - 1)}{(z^2 - 1)^2}$$
$$= \frac{(z^2 - 2zt + 1)^2}{(z^2 - 1)^2}$$

$$d\zeta = 2 \cdot \frac{z^2 - 1 - 2z(z - t)}{z^2 - 1} = 2 \frac{z^2 - 1 - 2z^2 + 2zt}{z^2 - 1} = 2 \frac{-z^2 - 1 + 2zt}{z^2 - 1}$$

## Figure & Layout Description
手写数学推导内容书写在浅灰色方格纸上，使用黑色墨水笔。整体布局为纵向排列的公式推导，从上至下分为四个主要逻辑区块：1) 生成函数定义与级数展开；2) 洛朗级数与柯西积分公式基础；3) 代入具体函数的积分表达式推导；4) 复变变量替换的详细计算。公式间通过箭头符号"→"和"～"表示推导关系，关键替换步骤（如"令ζ=2..."）用较大字号突出。部分公式右侧有手写注释（如"z是为辅助方"），积分路径符号"∮"清晰可见。页面右下角有部分推导被截断，但核心内容完整。所有数学符号保持手写体特征，如"ζ"的草书形态、分数线的倾斜书写等。

<CTX>
{
   "topic": "勒让德多项式的复变函数推导方法",
   "keywords": ["勒让德多项式", "生成函数", "柯西积分公式", "复变函数方法", "多极展开"],
   "summary": "本页通过复变函数中的柯西积分公式推导勒让德多项式的生成函数表达式，并展示变量替换的具体计算过程",
   "pending_concepts": ["积分路径的收敛性条件", "复变推导与实分析方法的等价性证明", "高阶导数与积分表达式的物理意义"]
}
</CTX>

---

# Slide 23

$$
\frac{1}{\sqrt{1 + y^2 - 2yt}} = \frac{|z^2 - 1|}{|z^2 - 2zt + 1|} = \frac{-(z^2 - 1)}{|z^2 - 2zt + 1|}
$$

$$
\frac{1}{y^{l+1}} dy = \frac{1}{z^{l+1}} \frac{(z^2 - 1)^{l+1}}{(z - t)^{l+1}} \cdot 2 \frac{-z^2 - 1 + 2zt}{z^2 - 1}
$$

故 $P_l(t) = \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + y^2 - 2yt}} \frac{1}{y^{l+1}} dy$.

$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}} dz
$$

利用 $f^{(n)}(x_0) = \frac{n!}{2\pi i} \oint \frac{f(y)}{y - x_0} dy$

$$
P_l(t) = \frac{1}{2^l} \cdot \frac{1}{l!} \cdot \partial_t^l (t^2 - 1)^l
$$

综上，

$$
P_l(t) = \frac{1}{2^l} \cdot \frac{1}{l!} \cdot \partial_t^l (t^2 - 1)^l
$$

$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}} dz
$$

$$
\frac{1}{r} = \frac{1}{\gamma \sqrt{1 + x^2 - 2x \cos\theta}} = \begin{cases} 
\frac{1}{\gamma} \sum_{l=0}^{\infty} P_l(\cos\theta) \cdot x^l, & x \le 1 \text{（球内）} \\
\frac{1}{\gamma} \sum_{l=0}^{\infty} P_l(\cos\theta) \frac{1}{x^{l+1}}, & x > 1 \text{（球外）}
\end{cases}
$$

## Figure & Layout Description
图片为方格纸背景的手写数学推导内容，整体布局为纵向排列的多行公式与文字说明。所有内容以黑色墨水书写，无其他颜色元素。页面顶部开始是分式等式推导，中间包含复变函数积分表达式，底部展示勒让德多项式生成函数的分段展开形式。公式间通过"故"、"利用"、"综上"等连接词形成逻辑链条。积分符号$\oint$以手写圆圈形式呈现，下标如$l$、$t$等均以标准手写体标注。方格纸的浅灰色网格线作为背景，每个公式占据1-2行网格空间，关键推导步骤间留有适当行距。无表格、图形或高亮标记，纯文本与数学符号构成完整推导流程。

<CTX>
{
   "topic": "勒让德多项式的复变函数推导与生成函数展开",
   "keywords": ["勒让德多项式", "柯西积分公式", "生成函数", "多极展开", "复变变量替换"],
   "summary": "本页完成勒让德多项式生成函数的复变函数推导，建立积分表达式与高阶导数表示的等价性，并展示其在球坐标系多极展开中的具体应用",
   "pending_concepts": ["积分路径的收敛性条件", "复变推导与实分析方法的等价性证明", "生成函数分段展开的物理意义"]
}
</CTX>

---

# Slide 24

若在 $P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{(z^2-1)^l}{(z-t)^{l+1}} dz$ 中

换元 $t = \cos\theta$

选路径为以 $t = \cos\theta$ 为圆心，$\sqrt{1-t^2} = \sin\theta$ 为半径

则 $z = \cos\theta + \sin\theta e^{i\varphi}$

$dz = i \sin\theta e^{i\varphi} d\varphi$

$$P_l(\cos\theta) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[(\cos\theta + \sin\theta e^{i\varphi})^2 - 1]^l}{(\sin\theta e^{i\varphi})^{l+1}} i \sin\theta e^{i\varphi} d\varphi$$

$$= \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[\cos^2\theta + 2\cos\theta\sin\theta e^{i\varphi} + \sin^2\theta e^{2i\varphi} - 1]^l}{(\sin\theta e^{i\varphi})^l} i d\varphi$$

$$= \frac{1}{2\pi} \cdot \frac{1}{2^l} \oint_C (-\sin\theta e^{i\varphi} + 2\cos\theta + \sin\theta e^{i\varphi})^l d\varphi$$

$$= \frac{1}{2\pi} \frac{1}{2^l} \int_{-\pi}^{\pi} (\sin\theta (e^{i\varphi} - e^{-i\varphi}) + 2\cos\theta)^l d\varphi, \, e^{i\varphi} - e^{-i\varphi} = 2i\sin\varphi$$

$$= \frac{1}{2\pi} \int_{-\pi}^{\pi} (\sin\theta \cdot i\sin\varphi + \cos\theta)^l d\varphi$$

$$P_l(\cos\theta) = \frac{1}{\pi} \int_0^{\pi} (\cos\theta + i\sin\theta\sin\varphi)^l d\varphi$$

令 $\theta = \frac{\pi}{2}$, $P_l(0) = \frac{1}{\pi} \int_0^{\pi} \sin^l\varphi d\varphi = \begin{cases} 
1, & l=0 \\
0, & l\text{为奇数} \\
\frac{1}{\pi} \cdot 2 \cdot \frac{(l-1)!!}{l!!} \cdot \frac{\pi}{2} = (-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}, & l\text{为偶数}
\end{cases}$

$i^l = (-1)^{\frac{l}{2}}$

## Figure & Layout Description
图片为方格纸背景的手写数学推导，整体布局为纵向排列的公式与文字。左上角开始是初始积分表达式，使用黑色墨水书写。中间偏左位置有一个手绘圆图，圆心标记为"t"，半径用斜线连接并标注"$\sqrt{1-t^2}$"，圆周上标有角度符号"φ"。公式推导过程占据页面主体，从上至下逐行展开，每行公式间有适当的垂直间距。页面右侧有零散的分数草稿（$\frac{3}{4}$, $\frac{1}{2}$, $\frac{\pi}{2}$, $\frac{4}{5}$, $\frac{2}{3}$），呈现为随意的演算痕迹。底部有红色墨水标注的等式"$i^l = (-1)^{\frac{l}{2}}$"，与其他黑色公式形成视觉对比。整个页面的推导过程逻辑连贯，从变量替换到最终结果，层次分明，公式与文字混合排布，关键步骤之间有适当的换行和缩进，便于阅读推导流程。

<CTX>
{
   "topic": "勒让德多项式在特定角度的积分计算与奇偶性分析",
   "keywords": ["勒让德多项式", "复变积分路径", "三角替换", "奇偶性分析", "θ=π/2特例"],
   "summary": "本页完成勒让德多项式在θ=π/2时的具体积分计算，展示其奇偶性特征及闭合表达式，为后续物理应用提供数学基础",
   "pending_concepts": ["积分路径的几何意义与收敛性", "复指数形式与实数生成函数的转换条件", "奇偶性结果在多极展开中的物理诠释"]
}
</CTX>

---

# Slide 25

当 $|x| \leq 1$ 时，$G(x,t) = \frac{1}{\sqrt{1+x^2-2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l$

令 $t=1$，则 $\frac{1}{\sqrt{1-x^2}} = \frac{1}{1-x} = 1+x+x^2+x^3+\cdots$

于是 $P_l(1) = 1$

令 $t=0$，$\frac{1}{\sqrt{1+x^2}}$ 为偶函数，故奇次项为 $0$

$P_l(0) = 0$ ($l$ 为奇数)

$G(x,-t) = \frac{1}{\sqrt{1+x^2+2xt}} = \frac{1}{\sqrt{1+x^2-2x(-t)}} = G(-x,t)$

故 $\sum_{l=0}^{\infty} P_l(-t) \cdot x^l = \sum_{l=0}^{\infty} P_l(t) \cdot (-x)^l$

故 $P_l(-t) = (-1)^l P_l(t)$

正交性：$I_2 = \int_{-1}^{1} P_l(t) P_m(t) dt = \frac{2}{2l+1} \delta_{lm}$

证：$G(x,t) = \frac{1}{\sqrt{1+x^2-2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l$  
$G(u,t) = \frac{1}{\sqrt{1+u^2-2ut}} = \sum_{m=0}^{\infty} P_m(t) \cdot u^m$

$\int_{-1}^{1} G(x,t) G(u,t) dt = \sum_{l=0}^{\infty} \sum_{m=0}^{\infty} x^l u^m \int_{-1}^{1} P_l(t) P_m(t) dt$

$I_1 = \int_{-1}^{1} \frac{1}{\sqrt{1+x^2-2xt}} \cdot \frac{1}{\sqrt{1+u^2-2ut}} dt$

令 $p = \sqrt{1+x^2-2xt}$ $\Rightarrow$ $p^2 + 2xt = 1+x^2$  
令 $q = \sqrt{1+u^2-2ut}$ $\Rightarrow$ $q^2 + 2ut = 1+u^2$

## Figure & Layout Description
图片为方格纸背景的手写数学笔记，整体呈纵向排列的推导过程。内容以黑色墨水书写，包含多个数学公式和文字说明。有三处关键结论用红色矩形框突出显示：第一处为 "$P_l(1) = 1$"，位于页面中上部；第二处为 "$P_l(0) = 0$ ($l$ 为奇数)"，位于页面中部；第三处为 "$P_l(-t) = (-1)^l P_l(t)$"，位于页面中下部。公式与文字交替排列，部分推导步骤下方有花括号标注 "$I_1$" 和 "$I_2$" 以指示积分表达式。页面底部有三角替换推导的辅助说明，左侧标注 "$p \to t$" 和 "$q \to t$" 指示变量替换关系。整体布局清晰，重点内容通过红色框线强调，形成视觉层级，便于追踪推导逻辑。

<CTX>
{
   "topic": "勒让德多项式的基本性质与正交性证明",
   "keywords": ["勒让德多项式", "生成函数", "奇偶性", "正交性", "积分性质"],
   "summary": "本页系统推导勒让德多项式的基本性质，包括归一化条件、奇偶性特征及正交性关系，建立生成函数与积分表示的联系",
   "pending_concepts": ["正交性证明的完整积分计算步骤", "生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>

---

# Slide 26

$$ I_1 = \int \frac{1}{pq} \, dt \quad , \quad 2p \, dp = -2x \, dt \implies \frac{dt}{p} = -\frac{1}{x} \, dp $$
$$ 2q \, dq = -2u \, dt $$
$$ I_1 = \left(1 - \frac{1}{x}\right) \int \frac{dp}{q} \quad , \quad u p^2 - x q^2 = C = u + u x^2 - x - x u^2 $$
$$ = u - x + ux(x - u) $$
$$ = (u - x)(1 - ux) $$
令 $ r = \sqrt{u} p $, $ s = \sqrt{x} q $  
则 $ r^2 - s^2 = C $, $ q = \frac{1}{\sqrt{x}} s $  
$$ I_1 = -\frac{1}{x} \cdot \frac{\sqrt{x}}{\sqrt{u}} \int \frac{dr}{s} \quad , \quad r \, dr = s \, ds $$
$$ \frac{dr}{s} = \frac{ds}{r} = \frac{d(r+s)}{r+s} = d(\ln|r+s|) $$
$$ = -\frac{1}{\sqrt{xu}} \ln |r + s| $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \sqrt{u} \sqrt{1+x^2-2xt} + \sqrt{x} \sqrt{1+u^2-2ut} \right) \bigg|_{t=-1}^{t=1} $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \frac{\sqrt{u}(1-x) + \sqrt{x}(1-u)}{\sqrt{u}(1+x) + \sqrt{x}(1+u)} \right) $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \frac{\sqrt{u} + \sqrt{x} - \sqrt{ux} - u\sqrt{x}}{\sqrt{u} + \sqrt{x} + \sqrt{ux} + u\sqrt{x}} \right) \quad \text{有理化} $$
$$ \frac{\sqrt{u} + \sqrt{x} - \sqrt{ux}(\sqrt{x} + \sqrt{u})}{(\sqrt{u} + \sqrt{x})(1 - \sqrt{ux})} = \frac{1 - \sqrt{ux}}{1 + \sqrt{ux}} $$
$$ = -\frac{1}{\sqrt{xu}} \ln \frac{1 - \sqrt{ux}}{1 + \sqrt{ux}} = \frac{1}{\sqrt{xu}} \ln \frac{1 + \sqrt{ux}}{1 - \sqrt{ux}} $$
展开 $ I_1 = \frac{1}{\sqrt{xu}} \left[ \ln(1 + \sqrt{ux}) - \ln(1 - \sqrt{ux}) \right] $

## Figure & Layout Description
图片为方格纸背景的手写数学推导，使用黑色墨水书写。整体布局为多列垂直排列的公式推导：左侧主要展示积分表达式与变量替换过程，右侧为代数展开与化简步骤。公式间通过等号与箭头符号连接，关键推导步骤（如"令 r=√u p"、"有理化"）以中文标注。积分上下限标记在公式右侧，部分分式结构通过水平分数线清晰分隔。底部包含对数函数的泰勒展开式（ln(1+x)等），以三行并列形式呈现。所有数学符号（如√, ∫, ln）均采用标准手写体，变量下标与上标位置准确，方格纸网格线作为排版基准，确保公式对齐。

<CTX>
{
   "topic": "勒让德多项式正交性证明的积分推导",
   "keywords": ["勒让德多项式", "正交性证明", "变量替换", "对数展开", "积分计算"],
   "summary": "本页完成勒让德多项式正交性证明中的关键积分计算，通过变量替换与对数展开验证正交关系",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>

---

# Slide 27

$$
= \frac{1}{\sqrt{ux}} \left[ \sum_{k=1}^{\infty} (-1)^{k-1} \frac{(\sqrt{ux})^k}{k} - \sum_{k=1}^{\infty} (-1)^{k-1} \frac{(-\sqrt{ux})^k}{k} \right].
$$

$$
= \frac{1}{\sqrt{ux}} \left( \sum_{k=0}^{\infty} 2 \frac{(\sqrt{ux})^{2k+1}}{2k+1} \right)
$$

$$
I_1 = \sum_{l=0}^{\infty} \frac{2}{2l+1} u^l x^l.
$$

$$
I_1 = \sum_{l=0}^{\infty} \sum_{m=0}^{\infty} x^l u^m I_2, \quad I_2 = \int_{-1}^{1} P_l(t) P_m(t) \, dt
$$

有
$$
\sum_{l=0}^{\infty} \frac{2}{2l+1} u^l x^l = \sum_{l=0}^{\infty} \sum_{m=0}^{\infty} x^l u^m \int_{-1}^{1} P_l(t) P_m(t) \, dt
$$

对比 $u, x$ 各次系数可知，
$$
\begin{aligned}
l \neq m \text{ 时} \quad & I_2 = 0 \\
l = m \text{ 时} \quad & I_2 = \frac{2}{2l+1}
\end{aligned}
$$

故
$$
I_2 = \int_{-1}^{1} P_l(t) P_m(t) \, dt = \frac{2}{2l+1} \delta_{lm}.
$$

这样，我们就证明了正交性

递推公式：
$$
G(x,t) = \frac{1}{\sqrt{1+x^2-2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l
$$
两边 $\partial x$，$\partial t$，再逐项即可。

## Figure & Layout Description
图片为方格纸背景的手写数学推导，黑色墨水书写。整体布局为纵向排列的公式与文字说明：顶部两行是变量替换的级数展开推导，包含两个求和符号的差分表达式；中间部分依次列出 $I_1$ 的级数定义、双重求和展开式及 $I_2$ 的积分定义；下半部分以"有"字起始进行系数对比分析，包含分段条件说明和最终正交性结论；底部单独列出生成函数 $G(x,t)$ 的表达式及操作说明。公式中使用标准数学符号（$\sum, \int, \sqrt{}$），文字说明为中文手写体，部分公式通过大括号和分式结构体现层级关系。所有内容按逻辑流程自上而下排列，无颜色区分，仅通过书写位置体现推导步骤。

<CTX>
{
   "topic": "勒让德多项式正交性证明中的积分验证与生成函数应用",
   "keywords": ["勒让德多项式", "正交性证明", "生成函数", "克罗内克δ", "积分计算"],
   "summary": "通过生成函数展开与系数对比完成正交性积分验证，明确正交关系中的归一化常数",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>

---

# Slide 28

$$
\partial_x G(x,t) = -\frac{1}{2} \frac{2x - 2t}{(1 + x^2 - 2xt)^{\frac{3}{2}}} = \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
-(x - t) \cdot G^3 = \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
(x - t) \cdot G_T = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
(x - t) \sum_{l=0}^{\infty} P_l(t) \cdot x^l = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^l \quad \text{（右侧标注：$l \to l+1$）}
$$

$$
\sum_{l=0}^{\infty} P_l(t) \cdot x^{l+1} - \sum_{l=0}^{\infty} t P_l(t) \cdot x^l = \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^l
$$

（橙色波浪线标注：$l \to l-1$）

$$
- \sum_{l=0}^{\infty} 2t P_{l+1}(t)(l+1) x^{l+1} \quad \text{（蓝色下划线标注：$l \to l-1$）}
$$

$$
+ \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^{l+2} \quad \text{（红色波浪线标注：$l \to l-2$）}
$$

$$
\text{有} \sum_{l=1}^{\infty} \left( P_{l-1}(t) - t P_l(t) \right) x^l = \sum_{l=1}^{\infty} \left[ P_{l+1}(t)(l+1) - 2t P_l(t) l + P_{l-1}(t)(l-1) \right] x^l
$$

$$
P_{l-1}(t) - t P_l(t) = P_{l+1}(t)(l+1) - 2t P_l(t) l + P_{l-1}(t)(l-1)
$$

（左侧蓝色三角标记，中间橙色波浪线，右侧蓝色箭头）

$$
\boxed{t(2l+1)P_l = (l+1)P_{l+1} + l P_{l-1}} \quad \text{（红色方框标注，右侧红色圆圈①）}
$$

$$
G(x,t) = \frac{1}{\sqrt{1 + x^2 - 2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l
$$

$$
\partial_t G(x,t) = -\frac{1}{2} \frac{-2x}{(1 + x^2 - 2xt)^{\frac{3}{2}}} = \sum_{l=0}^{\infty} P_l'(t) \cdot x^l
$$

$$
x G_T = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_l'(t) \cdot x^l
$$

## Figure & Layout Description

图片背景为标准方格纸，所有内容以黑色手写体垂直排列。公式按逻辑推导顺序自上而下分布，关键步骤通过彩色标记强化：

1. **顶部区域**：包含三个连续的偏微分方程推导，右侧有逗号分隔符和手写注释"l→l+1"（黑色墨水）。
2. **中部区域**：
   - 橙色波浪线横跨第一个求和式下方，标注"l→l-1"（橙色墨水）。
   - 蓝色下划线标记第二个求和项，右侧标注"l→l-1"（蓝色墨水）。
   - 红色波浪线标记第三个求和项，右侧标注"l→l-2"（红色墨水）。
   - 核心递推关系被红色实线方框包围，左侧有蓝色三角标记，右侧有红色圆圈内标"①"。
3. **底部区域**：包含生成函数定义和时间偏导推导，字体稍小但清晰。
4. **颜色系统**：橙色用于指标变换说明，蓝色用于中间推导步骤强调，红色用于关键结论和最终公式标注。所有手写公式保持数学符号的连贯性，部分下标（如$P_{l+1}$）通过上下位置区分。

## Context Update

<CTX>
{
   "topic": "勒让德多项式递推关系的生成函数推导",
   "keywords": ["勒让德多项式", "生成函数", "递推关系", "指标变换", "系数对比"],
   "summary": "通过生成函数微分与级数展开推导出勒让德多项式的三阶递推关系，完成正交性证明的关键中间步骤",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>

---

# Slide 29

$$
\sum_{l=0}^{\infty} P_l(t) \cdot x^{l+1} = \sum_{l=0}^{\infty} P_l'(t) \cdot x^l - \sum_{l=0}^{\infty} 2t P_l'(t) \cdot x^{l+1} + \sum_{l=0}^{\infty} P_l'(t) \cdot x^{l+2}
$$
$\underbrace{\hspace{4cm}}_{\text{l-1 l-1}}$ $\underbrace{\hspace{4cm}}_{\text{l-1 l-2}}$

$$
\sum_{l=2}^{\infty} P_{l-1}(t) \cdot x^l = \sum_{l=2}^{\infty} \left[ P_l'(t) - 2t P_{l-1}'(t) + P_{l-2}'(t) \right] x^l
$$

$$
P_{l-1}(t) = P_l'(t) - 2t P_{l-1}'(t) + P_{l-2}'(t)
$$
$$
\boxed{P_l(t) = P_{l+1}'(t) - 2t P_l'(t) + P_{l-1}'(t)} \quad \text{①} \quad \text{②}
$$

$$
t(2l+1)P_l = (l+1)P_{l+1} + lP_{l-1}
$$
① 求导得 $(2l+1)P_l + t(2l+1)P_l' = (l+1)P_{l+1}' + lP_{l-1}'$

① ② 联立消去 $P_l'$:
$$
(2l+1)P_l(t) = (2l+1)P_{l+1}'(t) - 2t(2l+1)P_l'(t) + (2l+1)P_{l-1}'(t)
$$
$$
2(2l+1)P_l + 2t(2l+1)P_l' = 2(l+1)P_{l+1}' + 2lP_{l-1}'
$$
相减得
$$
\boxed{(2l+1)P_l = P_{l+1}' - P_{l-1}'} \quad \text{③}
$$
②+③得 $(2l+2)P_l = 2P_{l+1}'(t) - 2tP_l'(t)$
$$
\boxed{(l+1)P_l = P_{l+1}'(t) - tP_l'(t)} \quad \text{④}
$$

## Figure & Layout Description
图片呈现于浅灰色方格纸背景上，所有内容为手写数学推导。主要文字使用黑色墨水书写，关键公式、标注和逻辑标记使用红色墨水。推导内容垂直排列，从上至下分为四个逻辑区块：顶部是级数展开式，包含三个求和式，其中第一个求和式下方有红色波浪线标注"l-1 l-1"，第三和第四个求和式下方有橙色波浪线标注"l-1 l-2"；中部是系数对比推导，包含两个等式，第二个等式中的递推关系被红色矩形框包围，右侧标注红色带圈数字"①"和"②"；中下部是微分操作推导，包含原始递推式、求导结果和联立消元步骤，"求导得"和"联立消去P_l'"等说明文字用红色书写；底部是相减操作和最终结果，"相减得"和"②+③得"等说明文字用红色书写，两个关键递推关系分别被红色矩形框包围，右侧标注红色带圈数字"③"和"④"。所有公式中的下标和上标清晰可辨，微分符号使用"'"表示。红色标注与黑色正文形成鲜明对比，突出推导的关键步骤和逻辑节点。

<CTX>
{
   "topic": "勒让德多项式递推关系的生成函数推导",
   "keywords": ["勒让德多项式", "生成函数", "递推关系", "指标变换", "系数对比", "微分关系"],
   "summary": "通过生成函数微分与代数运算推导出勒让德多项式的微分递推关系，完成从生成函数到具体递推公式的转化",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联", "递推关系的物理解释"]
}
</CTX>

---

# Slide 30

由③-④得  
$$l P_l = t P_l' - P_{l-1}' \quad \text{⑤}$$

由⑤，令 $t=0$，则  
$$l P_l(0) = -P_{l-1}'(0)$$  
$$P_{l-1}'(0) = -l P_l(0)$$  
$$P_l'(0) = -(l+1) P_{l+1}(0)$$

而  
$$P_l(0) = \frac{1}{\pi} \int_0^\pi \sin^l \phi \, d\phi = \begin{cases} 
1, & l=0 \\
0, & l \text{为奇数} \\
\frac{2}{\pi} \cdot \frac{(l-1)!!}{l!!} \cdot \frac{\pi}{2} = (-1)^{l/2} \frac{(l-1)!!}{l!!}, & l \text{为偶数}
\end{cases}$$

故  
$$P_l'(0) = \begin{cases} 
0, & l+1 \text{为奇数} \\
-(l+1) \cdot (-1)^{(l+1)/2} \frac{l!!}{(l+1)!!}, & l+1 \text{为偶数}
\end{cases}$$
不为一，是因为 $l+1$ 不可能为 $0$
## Figure & Layout Description
图像为方格纸背景的手写数学推导，主要使用黑色墨水书写，关键步骤和公式用红色标注。顶部左侧有红色手写体"③-④得"，其右侧是红色方框包围的公式$l P_l = t P_l' - P_{l-1}'$，方框右上角有红色圈注"⑤"。推导过程分为四段：第一段"由⑤，令t=0，则"后接三行等式推导；第二段"而"开头的积分表达式，包含分段函数，其中l为偶数的情况有红色修正标记；第三段"故"开头的最终分段结果，偶数情况的系数部分有红色标注。所有公式均采用左对齐排列，积分表达式和分段函数使用标准数学排版，红色标记用于强调递推关系编号、关键等式和修正项。整体布局呈现典型的课堂板书特征，逻辑流程从上至下依次展开。

<CTX>
{
   "topic": "勒让德多项式在t=0点的微分性质与奇偶性分析",
   "keywords": ["勒让德多项式", "微分递推关系", "t=0点性质", "奇偶性分析", "双阶乘"],
   "summary": "通过代入t=0验证微分递推关系，推导出P_l'(0)的奇偶性分段表达式，建立多项式阶数与导数值的显式关联",
   "pending_concepts": ["奇偶性与球谐函数的关联", "双阶乘表达式的物理意义", "递推关系在边界条件中的应用"]
}
</CTX>

---

# Slide 31

16.3  
(1)  
Way 1. $|x| \leq 1$ 时，$G(x,t) = \frac{1}{\sqrt{1 + x^2 - 2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l$  
令 $t=1$，则 $\frac{1}{\sqrt{1 - 2x + x^2}} = \frac{1}{1 - x} = 1 + x + x^2 + x^3 + \cdots$  
于是 $P_l(1) = 1$  
令 $t=0$，$\frac{1}{\sqrt{1 + x^2}}$ 为偶函数，故奇次项为 0  
$P_l(0) = 0$ ($l$ 为奇数)  

Way 2.  
$P_l(\cos\theta) = \frac{1}{\pi} \int_0^\pi (\cos\theta + i \sin\theta \sin\phi)^l d\phi$  
令 $\theta=0$，$P_l(1) = \frac{1}{\pi} \int_0^\pi d\phi = 1$  

(2)  
$G(x, -t) = \frac{1}{\sqrt{1 + x^2 + 2xt}} = \frac{1}{\sqrt{1 + (-x)^2 - 2(-x)t}} = G(-x, t)$  
故 $\sum_{l=0}^{\infty} P_l(-t) \cdot x^l = \sum_{l=0}^{\infty} P_l(t) \cdot (-x)^l$  
故 $P_l(-t) = (-1)^l P_l(t)$

## Figure & Layout Description
图片为手写数学推导内容，书写在方格纸背景上。整体布局分为两个主要部分：(1) 和 (2)，其中 (1) 部分包含 "Way 1" 和 "Way 2" 两种推导路径。文字以黑色墨水书写，关键结论用红色手绘框线标注（共三处：$P_l(1)=1$、$P_l(0)=0$ ($l$ 为奇数)、$P_l(-t)=(-1)^l P_l(t)$）。公式与文字混合排版，等号对齐形成逻辑推导链。顶部标注 "16.3" 作为章节编号，推导过程包含生成函数展开、特殊值代入和积分表示法。红色框线为手绘椭圆形，线条粗细不均，明显区别于黑色正文。方格纸网格线为浅灰色，作为书写基准线。

<CTX>
{
   "topic": "勒让德多项式的奇偶性证明与特殊点取值验证",
   "keywords": ["勒让德多项式", "生成函数", "积分表示", "奇偶性", "特殊点取值"],
   "summary": "通过生成函数展开和积分表示法，严格推导出勒让德多项式的奇偶性关系 $P_l(-t)=(-1)^l P_l(t)$ 并验证 $t=0,1$ 时的特殊取值",
   "pending_concepts": ["生成函数与物理场的关联", "积分表示法的几何解释", "奇偶性在量子力学中的应用"]
}
</CTX>

---

# Slide 32

16.4

(1) $\int_{-1}^1 P_l(x) dx = \int_{-1}^1 P_l(x) P_0(x) dx = \frac{2}{2l+1}\delta_{l0} = 2$.

(b) $\int_0^1 P_k P_l dx$

由于 $P_l(-t) = (-1)^l P_l(t)$

故当 $l$ 为偶数，$P_l(t)$ 偶函数。
$l$ 为奇，$P_l(t)$ 奇。

A 当 $k+l$ 为偶数时，$P_k, P_l$ 同为奇，同为偶，$P_k \cdot P_l$ 偶

故 $\int_0^1 P_k P_l dx = \frac{1}{2}\int_{-1}^1 P_k P_l dx = \frac{1}{2} \cdot \frac{2}{2l+1}\delta_{kl} = \frac{\delta_{kl}}{2l+1}$.

B 当 $k+l$ 为奇数时，$P_k, P_l$ 一奇一偶，$P_k \cdot P_l$ 奇，无法对称

利用其它定义，满足勒让德方程

$\partial_x[(1-x^2)\partial_x P_l] + l(l+1)P_l = 0$.

$\partial_x[(1-x^2)\partial_x P_k] + k(k+1)P_k = 0$.

乘微分

$P_k\partial_x[(1-x^2)\partial_x P_l] + l(l+1)P_l P_k = 0$.

$P_l\partial_x[(1-x^2)\partial_x P_k] + k(k+1)P_k P_l = 0$.

$\partial_x[(1-x^2)P_k\partial_x P_l] - (1-x^2)\partial_x P_l \cdot \partial_x P_k + l(l+1)P_l P_k = 0$.

$\partial_x[(1-x^2)P_l\partial_x P_k] - (1-x^2)\partial_x P_k \cdot \partial_x P_l + k(k+1)P_k P_l = 0$.

## Figure & Layout Description
图片展示了一张手写数学推导的方格纸，背景为白色，带有浅灰色的方格网格线。内容以黑色墨水书写，从左上角开始布局。页面顶部左侧标有"16.4"作为章节编号。正文分为多个逻辑部分：(1)部分展示了勒让德多项式在[-1,1]区间上的积分性质；(b)部分讨论了在[0,1]区间上的积分，包含奇偶性分析。推导过程清晰地分为A、B两个情况讨论，其中A部分处理k+l为偶数的情况，B部分处理k+l为奇数的情况。页面下半部分列出了勒让德方程的微分形式及其乘微分推导过程。文字排版整齐，公式与文字交错排列，每个推导步骤都有明确的逻辑连接词（如"由于"、"故"、"利用"等）。公式中的下标、积分限、微分符号等数学符号书写规范，字体大小均匀，便于阅读。整体布局遵循从上到下、从左到右的阅读顺序，关键推导步骤通过缩进和换行形成清晰的层次结构。

<CTX>
{
   "topic": "勒让德多项式的正交性证明与勒让德方程应用",
   "keywords": ["勒让德多项式", "正交性", "勒让德方程", "奇偶性", "积分表示"],
   "summary": "通过奇偶性分析和勒让德方程推导，证明了勒让德多项式在[0,1]区间上的正交关系并展示了微分方程的乘微分处理方法",
   "pending_concepts": ["勒让德方程的物理意义", "正交性在数值计算中的应用", "生成函数与勒让德方程的联系", "k+l奇偶性对积分结果的具体影响"]
}
</CTX>

---

# Slide 33

相似

$$[l(l+1)-k(k+1)]P_l P_k = \partial_x \left((1-x^2)P_l \partial_x P_k\right) - \partial_x \left((1-x^2)P_k \partial_x P_l\right)$$

$$P_l P_k = \partial_x \left[ \frac{(1-x^2)\left[P_l \partial_x P_k - P_k \partial_x P_l\right]}{l(l+1)-k(k+1)} \right]$$

$$\int_0^1 P_l P_k dx = \left. \frac{(1-x^2)\left[P_l \partial_x P_k - P_k \partial_x P_l\right]}{l(l+1)-k(k+1)} \right|_0^1$$

$$= 0 - \frac{P_l(0)P_k'(0) - P_k(0)P_l'(0)}{l(l+1)-k(k+1)}$$

$$= \frac{P_k(0)P_l'(0) - P_l(0)P_k'(0)}{l(l+1)-k(k+1)}$$

$$\boxed{l P_l = t P_l' - P_{l-1}'} \quad \text{⑤}$$

由⑤，令 $l=0$，则 $l P_l(0) = -P_{l-1}'(0)$

$$P_{l-1}'(0) = -l P_l(0)$$

$$P_l'(0) = -(l+1)P_{l+1}(0), \quad P_0'(0) = -P_1(0) = 0$$

而 $P_l(0) = \frac{1}{\pi} \int_0^\pi \cos^l \phi \, d\phi = \begin{cases} 
0, & l \text{为奇数} \\
\frac{1}{\pi} \cdot 2 \cdot \frac{(l-1)!!}{l!!} \cdot \frac{\pi}{2} = (-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}, & l \text{为偶数}
\end{cases}$

故 $P_l'(0) = \begin{cases} 
0, & l+1 \text{为奇数} \\
-(l+1) \cdot (-1)^{\frac{l}{2}} \frac{l!!}{(l+1)!!}, & l+1 \text{为偶数}
\end{cases}$

$(-1)^{\frac{l+1}{2}} \frac{l!!}{(l-1)!!}$

## Figure & Layout Description
图片为手写数学推导内容，书写在标准方格纸背景上。整体布局为纵向排列的数学公式和文字说明，从上至下依次展开。顶部有"相似"二字作为标题，字体略大于正文。核心内容包含多行数学推导，使用黑色墨水书写，字迹工整清晰。

关键视觉元素包括：
- 一个红色方框标注的公式 $l P_l = t P_l' - P_{l-1}'$，位于页面中部偏下位置
- 红色圆圈标注的"⑤"符号紧邻红色方框公式右侧
- 推导过程中包含积分表达式、边界条件计算和分段函数表示
- 公式中使用了标准数学符号，包括偏导数 $\partial_x$、积分 $\int$、阶乘双阶乘 $!!$ 等
- 有明确的等号对齐和分步推导，显示了从微分方程到积分正交性的完整过程
- 页面右下角有未完成的公式推导，显示部分分式表达式

整体视觉层次分明，主要推导步骤通过等号对齐形成逻辑链条，关键公式通过红色标记突出显示，便于读者识别重要结论。

<CTX>
{
   "topic": "勒让德多项式的正交性证明与端点性质分析",
   "keywords": ["勒让德多项式", "正交性", "勒让德方程", "奇偶性", "端点导数", "边界条件"],
   "summary": "完成勒让德多项式正交性证明并推导出端点处的函数值与导数值的奇偶性表达式，建立了微分方程与正交性的定量联系",
   "pending_concepts": ["勒让德方程的物理意义", "正交性在数值计算中的应用", "生成函数与勒让德方程的联系", "端点导数在边界值问题中的具体应用"]
}
</CTX>

---

# Slide 34

不失一般性，设 $l$ 为偶数且 $l > 0$；$k$ 为奇数

① $l=0$ 时，
$$
\int_0^1 P_0 P_k dx = \frac{P_k(0)P_0'(0) - P_0(0)P_k'(0)}{-k(k+1)} = \frac{P_k'(0)}{k(k+1)}
$$
$$
= \frac{-(k+1)P_{k+1}(0)}{k(k+1)} = 
\begin{cases} 
\frac{1}{2} & (k=1) \\
-\frac{1}{k} (-1)^{\frac{k+1}{2}} \frac{k!!}{(k+1)!!} & (k \geq 3)
\end{cases}.
$$

② $l \geq 2$ 时，
$$
P_l(0) = (-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}, \quad P_l'(0) = 0
$$
$$
P_k(0) = 0, \quad P_k'(0) = (-1)^{\frac{k-1}{2}} \frac{k!!}{(k-1)!!}
$$
$$
\int_0^1 P_l P_k dx = \frac{P_k(0)P_l'(0) - P_l(0)P_k'(0)}{l(l+1) - k(k+1)}
$$
$$
= - \frac{ (-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!} \cdot (-1)^{\frac{k-1}{2}} \frac{k!!}{(k-1)!!} }{ l(l+1) - k(k+1) }
$$

## Figure & Layout Description
手写内容书写在浅灰色方格纸背景上，主要使用黑色墨水书写，关键积分上下限用橙色标注。页面顶部有标题性文字"不失一般性，设 $l$ 为偶数且 $l > 0$；$k$ 为奇数"。内容分为两个主要部分：① $l=0$ 时的推导和② $l \geq 2$ 时的推导。积分符号 $\int_0^1$ 中的上下限"0"和"1"用橙色标注并加下划线（"0"下划线为橙色，"1"下划线为红色）。公式中包含多层分数结构、分段函数大括号表示，以及双阶乘符号"!!"。部分关键表达式（如 $(-1)^{l/2}$）用红色墨水标注指数部分。推导过程中包含等号对齐的多行公式，第二部分包含两个并列的端点性质公式（$P_l(0)$ 与 $P_l'(0)$，$P_k(0)$ 与 $P_k'(0)$）。整体布局为纵向排列，公式间距适中，关键步骤用等号连接形成推导链条。

<CTX>
{
   "topic": "勒让德多项式不同参数下的正交积分计算与端点性质",
   "keywords": ["勒让德多项式", "正交性", "分情况讨论", "端点函数值", "双阶乘"],
   "summary": "本页针对l=0和l≥2两种情况，推导了勒让德多项式正交积分的具体表达式，结合端点处的函数值与导数值完成定量计算",
   "pending_concepts": ["双阶乘在勒让德多项式中的物理意义", "正交积分结果在数值积分中的应用", "奇偶性对积分结果的影响机制"]
}
</CTX>

---

# Slide 35

16.5 $\{P_l(x)\}$

(1) $f(x) = |x|$ \quad (2) $f(x) = 1 + x + x^2 + x^3$

设 $f(x) = \sum_{l=0}^{\infty} a_l P_l(x)$

$$\int_{-1}^{1} f(x) P_m(x) \, dx = \sum_{l=0}^{\infty} \int_{-1}^{1} a_l P_l(x) P_m(x) \, dx =$$
$$= \sum_{l=0}^{\infty} a_l \delta_{lm} \frac{2}{2l+1} = \frac{2}{2m+1} a_m$$

$\Rightarrow a_l = \frac{2l+1}{2} \int_{-1}^{1} f(x) P_l(x) \, dx$

$= \frac{2l+1}{2} \cdot 2 \int_{0}^{1} x P_l(x) \, dx$

$= (2l+1) \int_{0}^{1} P_1(x) P_l(x) \, dx$

① $l=0$ 时 $a_0 = \frac{1}{2}$

② $l \geq 1$ 时 $a_l = (2l+1) \cdot \left[ -\frac{(-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!} (-1)^{\frac{k}{2}} \frac{k!!}{(k-1)!!}}{l(l+1) - k(k+1)} \right], \, k=1$

$a_l = (2l+1) \cdot \left[ \frac{(-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}}{l(l+1) - 2} \right] \, (l \neq 1)$

## Figure & Layout Description
图片展示了一张手写在方格纸上的数学推导笔记。背景是标准的方格纸，网格线为浅灰色，形成规则的正方形网格。文字内容为黑色手写体，部分关键公式用红色笔迹标记强调。

整体布局从上至下依次排列：
1. 顶部标题"16.5 {P_l(x)}"位于页面左上角，字体略大，手写风格
2. 接下来是两个函数定义，标记为"(1)"和"(2)"，并列排列在同一水平线上
3. 中间部分是勒让德级数展开的假设和积分推导过程，公式分多行排列，每行公式左对齐
4. 推导过程包含多个等号对齐的公式行，其中积分表达式和求和符号书写规范
5. 最后部分是针对l=0和l≥1两种情况的系数计算，使用带圈数字"①"和"②"进行标记

视觉特点：
- 公式中的积分符号、求和符号、分数等数学符号书写规范，但部分下标和上标较小
- 红色标记主要用于突出关键系数和公式中的特定部分，特别是最后两行公式中的指数和分式部分
- 部分公式有下划线强调，如积分表达式
- 页面右下角有部分公式被截断，特别是最后一行公式的右侧部分
- 整体书写较为紧凑，行间距较小，符合手写笔记的特点
- 纸张有轻微褶皱痕迹，但不影响内容辨认

## Figure & Layout Description

<CTX>
{
   "topic": "勒让德级数展开系数的计算方法与具体案例",
   "keywords": ["勒让德级数", "展开系数", "正交性应用", "分段函数展开", "双阶乘"],
   "summary": "本页详细推导了将绝对值函数和多项式函数展开为勒让德级数的系数计算方法，展示了如何利用勒让德多项式的正交性求解展开系数",
   "pending_concepts": ["红色标记公式的具体推导过程", "双阶乘在系数表达式中的简化规则", "l=1时的特殊情况处理"]
}
</CTX>

---

# Slide 36

$$|x| = \frac{1}{2} + \sum_{l=1}^{\infty} (2l+1) \left[ \frac{(-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}}{l(l+1)-2} \right] P_l(x).$$

(2) $f(x) = 1 + x + x^2 + x^3.$

$P_0(x) = 1 \quad P_1(x) = x \quad P_2(x) = \frac{1}{2}(3x^2 - 1) \quad P_3(x) = \frac{1}{2}(5x^3 - 3x)$

$a_0P_0 + a_1P_1 + a_2P_2 + a_3P_3 = 1 + x + x^2 + x^3.$

$a_0 - \frac{1}{2}a_2 + \left(a_1 - \frac{3}{2}a_3\right)x + \left(\frac{3}{2}a_2\right)x^2 + \frac{5}{2}a_3x^3$

$= 1 + x + x^2 + x^3.$

$a_0 - \frac{1}{2}a_2 = 1 \implies a_0 = 1 + \frac{1}{2}a_2 = \frac{4}{3}$

$a_1 - \frac{3}{2}a_3 = 1 \implies a_1 = 1 + \frac{3}{2}a_3 = 1 + \frac{3}{2} \cdot \frac{2}{5} = \frac{8}{5}$

$\frac{3}{2}a_2 = 1 \implies a_2 = \frac{2}{3}$

$\frac{5}{2}a_3 = 1 \implies a_3 = \frac{2}{5}$

$f(x) = \frac{4}{3}P_0 + \frac{8}{5}P_1 + \frac{2}{3}P_2 + \frac{2}{5}P_3$

## Figure & Layout Description
The slide displays handwritten mathematical content on grid paper background. The layout consists of five distinct blocks of equations arranged vertically:

1. **Top block**: A complex Legendre series expansion formula for $|x|$ with a red-colored exponent $(-1)^{\frac{l}{2}}$ in the numerator. The summation starts from $l=1$ to $\infty$, with a fraction containing double factorials $(l-1)!!/l!!$ in the numerator and $l(l+1)-2$ in the denominator.

2. **Second block**: Labeled "(2)", shows a cubic polynomial $f(x) = 1 + x + x^2 + x^3$ followed by definitions of Legendre polynomials $P_0$ through $P_3$ with their standard expressions.

3. **Third block**: A linear combination equation showing $a_0P_0 + \cdots = 1 + x + x^2 + x^3$.

4. **Fourth block**: Expanded form of the linear combination showing coefficients grouped by powers of $x$.

5. **Fifth block**: Four coefficient equations with solutions, followed by the final Legendre series expression for $f(x)$.

All text is handwritten in black ink except for the $(-1)^{\frac{l}{2}}$ term which is highlighted in red. The grid lines are light gray and form a standard square grid pattern. The content follows a logical top-to-bottom derivation flow with clear separation between different derivation steps.

<CTX>
{
   "topic": "勒让德级数展开系数的计算方法与多项式函数展开实例",
   "keywords": ["勒让德级数", "展开系数", "正交性应用", "多项式展开", "系数匹配法"],
   "summary": "本页通过具体多项式函数的实例，演示了利用勒让德多项式正交性进行系数匹配的完整计算流程，展示了从方程建立到系数求解的详细步骤",
   "pending_concepts": ["红色标记公式的具体推导过程", "双阶乘在系数表达式中的简化规则", "l=1时的特殊情况处理"]
}
</CTX>

---

