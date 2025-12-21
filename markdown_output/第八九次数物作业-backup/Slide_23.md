# Slide 23

$$
\frac{1}{\sqrt{1 + y^2 - 2yt}} = \frac{|z^2 - 1|}{|z^2 - 2zt + 1|} = \frac{-(z^2 - 1)}{|z^2 - 2zt + 1|}
$$

$$
\frac{1}{y^{l+1}} dy = \frac{1}{z^{l+1}} \frac{(z^2 - 1)^{l+1}}{(z - t)^{l+1}} \cdot 2 \frac{-z^2 - 1 + 2zt}{z^2 - 1}
$$

故 $P_l(t) = \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + y^2 - 2yt}} \frac{1}{y^{l+1}} dy$.

$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}} dz
$$

利用 $f^{(n)}(x_0) = \frac{n!}{2\pi i} \oint \frac{f(y)}{y - x_0} dy$

$$
P_l(t) = \frac{1}{2^l} \cdot \frac{1}{l!} \cdot \partial_t^l (t^2 - 1)^l
$$

综上，

$$
P_l(t) = \frac{1}{2^l} \cdot \frac{1}{l!} \cdot \partial_t^l (t^2 - 1)^l
$$

$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}} dz
$$

$$
\frac{1}{r} = \frac{1}{\gamma \sqrt{1 + x^2 - 2x \cos\theta}} = \begin{cases} 
\frac{1}{\gamma} \sum_{l=0}^{\infty} P_l(\cos\theta) \cdot x^l, & x \le 1 \text{（球内）} \\
\frac{1}{\gamma} \sum_{l=0}^{\infty} P_l(\cos\theta) \frac{1}{x^{l+1}}, & x > 1 \text{（球外）}
\end{cases}
$$

## Figure & Layout Description
图片为方格纸背景的手写数学推导内容，整体布局为纵向排列的多行公式与文字说明。所有内容以黑色墨水书写，无其他颜色元素。页面顶部开始是分式等式推导，中间包含复变函数积分表达式，底部展示勒让德多项式生成函数的分段展开形式。公式间通过"故"、"利用"、"综上"等连接词形成逻辑链条。积分符号$\oint$以手写圆圈形式呈现，下标如$l$、$t$等均以标准手写体标注。方格纸的浅灰色网格线作为背景，每个公式占据1-2行网格空间，关键推导步骤间留有适当行距。无表格、图形或高亮标记，纯文本与数学符号构成完整推导流程。

<CTX>
{
   "topic": "勒让德多项式的复变函数推导与生成函数展开",
   "keywords": ["勒让德多项式", "柯西积分公式", "生成函数", "多极展开", "复变变量替换"],
   "summary": "本页完成勒让德多项式生成函数的复变函数推导，建立积分表达式与高阶导数表示的等价性，并展示其在球坐标系多极展开中的具体应用",
   "pending_concepts": ["积分路径的收敛性条件", "复变推导与实分析方法的等价性证明", "生成函数分段展开的物理意义"]
}
</CTX>