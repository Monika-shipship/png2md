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