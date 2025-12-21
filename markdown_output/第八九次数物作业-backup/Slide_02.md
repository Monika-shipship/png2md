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