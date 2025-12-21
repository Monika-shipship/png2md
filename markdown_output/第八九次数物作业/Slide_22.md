# Slide 22

我们尝试推导任意阶勒让德多项式 $P_l(t)$ 的表达式。已知其生成函数为：

$$
f(x) = (1 + x^2 - 2xt)^{-1/2} = \sum_{l=0}^{\infty} P_l(t) x^l
$$

为了从该生成函数中提取出第 $l$ 阶勒让德多项式 $P_l(t)$，我们使用复分析中的**柯西积分公式**与**洛朗级数展开**。

## 洛朗级数与系数提取

对于在 $x_0 = 0$ 处解析的函数 $f(x)$，其洛朗展开为：

$$
f(x) = \sum_{k=-\infty}^{\infty} a_k x^k, \quad \text{其中} \quad a_k = \frac{1}{2\pi i} \oint \frac{f(\theta)}{\theta^{k+1}} d\theta
$$

由于 $f(x)$ 在 $x=0$ 处解析且展开为泰勒级数（即非负幂次），故 $a_k = 0$ 对 $k < 0$，而对 $l \geq 0$，有：

$$
P_l(t) = a_l = \frac{1}{2\pi i} \oint \frac{f(\theta)}{\theta^{l+1}} d\theta
$$

代入 $f(\theta) = (1 + \theta^2 - 2\theta t)^{-1/2}$，得：

$$
P_l(t) = \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + \theta^2 - 2\theta t}} \cdot \frac{1}{\theta^{l+1}} d\theta
$$

另一方面，根据高阶导数的柯西积分公式：

$$
f^{(l)}(0) = \frac{l!}{2\pi i} \oint \frac{f(\theta)}{\theta^{l+1}} d\theta \quad \Rightarrow \quad P_l(t) = \frac{f^{(l)}(0)}{l!}
$$

这与泰勒系数一致，验证了上述表达式的正确性。

## 与罗德里格公式联系

已知勒让德多项式的**罗德里格公式**（Rodrigues' formula）为：

$$
P_l(t) = \frac{1}{2^l l!} \frac{d^l}{dt^l} (t^2 - 1)^l
$$

我们试图通过变量替换将上述围道积分转化为与此相关的形式。考虑构造一个辅助变量 $z$，使得：

令  
$$
\theta = z \frac{z - t}{z^2 - 1}
$$

则计算 $1 + \theta^2 - 2\theta t$：

$$
1 + \theta^2 - 2\theta t = 1 + \left(z \frac{z - t}{z^2 - 1}\right)^2 - 2 t \left(z \frac{z - t}{z^2 - 1}\right)
$$

通分后可得：

$$
= \frac{(z^2 - 1)^2 + z^2(z - t)^2 - 2tz(z - t)(z^2 - 1)}{(z^2 - 1)^2}
$$

化简分子：

$$
(z^2 - 1)^2 + z^2(z - t)^2 - 2tz(z - t)(z^2 - 1) = (z^2 - 2zt + 1)^2
$$

因此：

$$
1 + \theta^2 - 2\theta t = \frac{(z^2 - 2zt + 1)^2}{(z^2 - 1)^2}
\quad \Rightarrow \quad
\sqrt{1 + \theta^2 - 2\theta t} = \frac{|z^2 - 2zt + 1|}{|z^2 - 1|}
$$

在适当选择积分路径和分支下，忽略符号问题，取正则分支：

$$
\frac{1}{\sqrt{1 + \theta^2 - 2\theta t}} = \frac{z^2 - 1}{z^2 - 2zt + 1}
$$

接下来计算微分 $d\theta$：

由  
$$
\theta = z \frac{z - t}{z^2 - 1}
\quad \Rightarrow \quad
d\theta = \frac{d}{dz} \left( z \frac{z - t}{z^2 - 1} \right) dz
$$

求导：

$$
\frac{d}{dz} \left( \frac{z(z - t)}{z^2 - 1} \right)
= \frac{(2z - t)(z^2 - 1) - z(z - t)(2z)}{(z^2 - 1)^2}
= \cdots = \frac{-z^2 - 1 + 2zt}{z^2 - 1} dz
$$

所以：

$$
d\theta = \frac{-z^2 - 1 + 2zt}{z^2 - 1} dz
$$

结合以上结果，原积分变为：

$$
P_l(t) \sim \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + \theta^2 - 2\theta t}} \cdot \frac{1}{\theta^{l+1}} d\theta
= \frac{1}{2\pi i} \oint \left( \frac{z^2 - 1}{z^2 - 2zt + 1} \right) \cdot \left( \frac{z^2 - 1}{z(z - t)} \right)^{l+1} \cdot \left( \frac{-z^2 - 1 + 2zt}{z^2 - 1} \right) dz
$$

进一步整理发现，此形式可约化为：

$$
P_l(t) \propto \frac{1}{2\pi i} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}} dz
$$

这正是罗德里格公式对应的**施列夫利积分表示**（Schläfli's integral）：

$$
P_l(t) = \frac{1}{2\pi i} \oint_C \frac{(z^2 - 1)^l}{2^l (z - t)^{l+1}} dz
$$

其中 $C$ 是围绕 $z = t$ 的简单闭合曲线。

---

## Figure Description

图片为方格纸背景的手写数学推导内容，使用黑色墨水书写，布局自上而下。主要内容包括中文说明“我们再尝试推导任意阶的 $P_l(t)$ 表达式”，随后列出生成函数、洛朗级数展开式、柯西积分公式及其高阶导数形式。右侧和中间区域分布多个复积分表达式，包含根号、分数、求和与导数符号。存在波浪线“~”表示近似或渐进行为，以及箭头指示变量替换步骤。关键替换 $\theta = z \frac{z - t}{z^2 - 1}$ 出现在中部偏下位置，并伴随详细的代数化简过程。

<CTX>
{
  "topic": "勒让德多项式的积分表示与罗德里格公式的联系",
  "keywords": ["勒让德多项式", "柯西积分公式", "洛朗级数", "施列夫利积分", "罗德里格公式"],
  "summary": "通过生成函数结合复变函数方法，利用柯西积分公式将勒让德多项式 $P_l(t)$ 表示为围道积分，并通过变量替换将其与罗德里格公式关联，最终导向施列夫利积分表示，为后续讨论正交性和微分方程提供基础。",
  "last_formula_context": "最后一个公式是勒让德多项式的施列夫利积分表示：$P_l(t) = \\frac{1}{2\\pi i} \\oint_C \\frac{(z^2 - 1)^l}{2^l (z - t)^{l+1}} dz$，该表达式将在下一页用于推导递推关系或正交性。"
}
</CTX>