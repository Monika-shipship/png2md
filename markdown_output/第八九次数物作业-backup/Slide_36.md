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