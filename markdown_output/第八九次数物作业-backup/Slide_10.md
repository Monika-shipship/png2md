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