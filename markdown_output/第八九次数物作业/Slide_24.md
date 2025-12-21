# Slide 24

## 施列夫利积分的参数化与勒让德多项式在 $\theta = \pi/2$ 处的取值

从施列夫利积分表达式出发：

$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{(z^2 - 1)^l}{(z - t)^{l+1}} \, dz
$$

令 $ t = \cos\theta $，并选择积分路径 $ C $ 为以 $ t = \cos\theta $ 为圆心、半径为 $ \sqrt{1 - t^2} = \sin\theta $ 的圆周。对该路径进行参数化：

$$
z = \cos\theta + \sin\theta \, e^{i\varphi}, \quad dz = i \sin\theta \, e^{i\varphi} \, d\varphi
$$

代入原积分表达式：

$$
P_l(\cos\theta) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{\left[ (\cos\theta + \sin\theta \, e^{i\varphi})^2 - 1 \right]^l}{(\sin\theta \, e^{i\varphi})^{l+1}} \cdot i \sin\theta \, e^{i\varphi} \, d\varphi
$$

化简分子：

$$
(\cos\theta + \sin\theta \, e^{i\varphi})^2 - 1 = \cos^2\theta + 2\cos\theta\sin\theta \, e^{i\varphi} + \sin^2\theta \, e^{2i\varphi} - 1
$$

利用恒等式 $ \cos^2\theta - 1 = -\sin^2\theta $，得：

$$
= -\sin^2\theta + 2\cos\theta\sin\theta \, e^{i\varphi} + \sin^2\theta \, e^{2i\varphi} = \sin^2\theta (e^{2i\varphi} - 1) + 2\cos\theta\sin\theta \, e^{i\varphi}
$$

更简洁地整理整个分式：

$$
P_l(\cos\theta) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[\cdots]^l}{(\sin\theta \, e^{i\varphi})^{l+1}} \cdot i \sin\theta \, e^{i\varphi} \, d\varphi = \frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} \left( 2\cos\theta + \sin\theta (e^{i\varphi} - e^{-i\varphi}) \right)^l d\varphi
$$

利用 $ e^{i\varphi} - e^{-i\varphi} = 2i\sin\varphi $，有：

$$
P_l(\cos\theta) = \frac{1}{2\pi} \cdot \frac{1}{2^l} \int_{-\pi}^{\pi} \left( 2\cos\theta + \sin\theta \cdot 2i\sin\varphi \right)^l d\varphi = \frac{1}{2\pi} \int_{-\pi}^{\pi} \left( \cos\theta + i\sin\theta \sin\varphi \right)^l d\varphi
$$

由于被积函数关于 $\varphi$ 是偶函数（因 $\sin^l\varphi$ 在对称区间中偶次幂对称），可化为：

$$
P_l(\cos\theta) = \frac{1}{\pi} \int_0^{\pi} \left( \cos\theta + i\sin\theta \sin\varphi \right)^l d\varphi
$$

### 特例：$\theta = \frac{\pi}{2}$ 时计算 $P_l(0)$

当 $\theta = \frac{\pi}{2}$，则 $\cos\theta = 0$, $\sin\theta = 1$，故：

$$
P_l(0) = \frac{1}{\pi} \int_0^{\pi} (i \sin\varphi)^l \, d\varphi = \frac{i^l}{\pi} \int_0^{\pi} \sin^l\varphi \, d\varphi
$$

注意到 $\int_0^{\pi} \sin^l\varphi \, d\varphi = 2 \int_0^{\pi/2} \sin^l\varphi \, d\varphi$，利用标准积分公式：

$$
\int_0^{\pi/2} \sin^n x \, dx = 
\begin{cases}
\frac{(n-1)!!}{n!!} \cdot \frac{\pi}{2}, & n \text{ 为偶数} \\
\frac{(n-1)!!}{n!!}, & n \text{ 为奇数}
\end{cases}
$$

因此，

- 若 $ l $ 为奇数，则 $ \int_0^\pi \sin^l\varphi \, d\varphi $ 对称且奇函数部分积分为零 → $ P_l(0) = 0 $
- 若 $ l $ 为偶数，设 $ l = 2k $，则：

$$
P_l(0) = \frac{i^{2k}}{\pi} \cdot 2 \cdot \frac{(l-1)!!}{l!!} \cdot \frac{\pi}{2} = (-1)^k \cdot \frac{(l-1)!!}{l!!}
$$

因为 $ i^{2k} = (-1)^k $，且 $ k = l/2 $，所以：

$$
P_l(0) =
\begin{cases}
1, & l = 0 \\
0, & l \text{ 为奇数} \\
(-1)^{l/2} \dfrac{(l-1)!!}{l!!}, & l \text{ 为偶数}
\end{cases}
$$

> **注**：右下角补充示例：
> - $ \int_0^{\pi/2} \sin^3\varphi \, d\varphi = \frac{2}{3} $
> - $ \int_0^{\pi/2} \sin^4\varphi \, d\varphi = \frac{3}{4} \cdot \frac{1}{2} \cdot \frac{\pi}{2} = \frac{3\pi}{16} $

---

## Figure Description

手绘示意图位于左上角：一个圆形路径 $ C $，圆心标记为 $ t = \cos\theta $，半径标注为 $ \sqrt{1 - t^2} = \sin\theta $，从圆心向圆周引出一条线段表示复变量 $ z $ 的位置。推导过程纵向排列，包含多个步骤的复积分变换和三角恒等变形。关键符号如 $ i\sin\varphi $ 中的虚数单位 $ i $ 以红色强调，$ (-1)^{l/2} $ 旁有红色批注“仅适用于偶 $ l $”。右下角列出常用正弦幂积分结果，并给出数值示例。

<CTX>
{
  "topic": "施列夫利积分的参数化与 P_l(0) 的显式计算",
  "keywords": ["施列夫利积分", "参数化路径", "勒让德多项式", "双阶乘", "实积分表示"],
  "summary": "通过将施列夫利积分在单位圆上参数化，成功将其转化为关于角度 \\varphi 的实积分形式；进一步计算 \\theta = \\pi/2 时的特例 P_l(0)，得到其依赖于 l 奇偶性的闭式表达式，强化了复积分方法与特殊函数值之间的联系。",
  "last_formula_context": "最后一个公式是 P_l(0) 的分段表达式，特别指出当 l 为偶数时由双阶乘和交错符号构成，该结果可用于后续讨论勒让德多项式的对称性与展开系数估计。"
}
</CTX>