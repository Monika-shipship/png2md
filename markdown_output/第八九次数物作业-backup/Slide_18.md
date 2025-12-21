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