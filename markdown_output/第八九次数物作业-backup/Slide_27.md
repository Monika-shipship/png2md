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