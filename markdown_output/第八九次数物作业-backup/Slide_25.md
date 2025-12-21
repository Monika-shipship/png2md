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