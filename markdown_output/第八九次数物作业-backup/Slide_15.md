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