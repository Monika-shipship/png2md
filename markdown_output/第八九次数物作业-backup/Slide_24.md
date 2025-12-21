# Slide 24

若在 $P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{(z^2-1)^l}{(z-t)^{l+1}} dz$ 中

换元 $t = \cos\theta$

选路径为以 $t = \cos\theta$ 为圆心，$\sqrt{1-t^2} = \sin\theta$ 为半径

则 $z = \cos\theta + \sin\theta e^{i\varphi}$

$dz = i \sin\theta e^{i\varphi} d\varphi$

$$P_l(\cos\theta) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[(\cos\theta + \sin\theta e^{i\varphi})^2 - 1]^l}{(\sin\theta e^{i\varphi})^{l+1}} i \sin\theta e^{i\varphi} d\varphi$$

$$= \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint_C \frac{[\cos^2\theta + 2\cos\theta\sin\theta e^{i\varphi} + \sin^2\theta e^{2i\varphi} - 1]^l}{(\sin\theta e^{i\varphi})^l} i d\varphi$$

$$= \frac{1}{2\pi} \cdot \frac{1}{2^l} \oint_C (-\sin\theta e^{i\varphi} + 2\cos\theta + \sin\theta e^{i\varphi})^l d\varphi$$

$$= \frac{1}{2\pi} \frac{1}{2^l} \int_{-\pi}^{\pi} (\sin\theta (e^{i\varphi} - e^{-i\varphi}) + 2\cos\theta)^l d\varphi, \, e^{i\varphi} - e^{-i\varphi} = 2i\sin\varphi$$

$$= \frac{1}{2\pi} \int_{-\pi}^{\pi} (\sin\theta \cdot i\sin\varphi + \cos\theta)^l d\varphi$$

$$P_l(\cos\theta) = \frac{1}{\pi} \int_0^{\pi} (\cos\theta + i\sin\theta\sin\varphi)^l d\varphi$$

令 $\theta = \frac{\pi}{2}$, $P_l(0) = \frac{1}{\pi} \int_0^{\pi} \sin^l\varphi d\varphi = \begin{cases} 
1, & l=0 \\
0, & l\text{为奇数} \\
\frac{1}{\pi} \cdot 2 \cdot \frac{(l-1)!!}{l!!} \cdot \frac{\pi}{2} = (-1)^{\frac{l}{2}} \frac{(l-1)!!}{l!!}, & l\text{为偶数}
\end{cases}$

$i^l = (-1)^{\frac{l}{2}}$

## Figure & Layout Description
图片为方格纸背景的手写数学推导，整体布局为纵向排列的公式与文字。左上角开始是初始积分表达式，使用黑色墨水书写。中间偏左位置有一个手绘圆图，圆心标记为"t"，半径用斜线连接并标注"$\sqrt{1-t^2}$"，圆周上标有角度符号"φ"。公式推导过程占据页面主体，从上至下逐行展开，每行公式间有适当的垂直间距。页面右侧有零散的分数草稿（$\frac{3}{4}$, $\frac{1}{2}$, $\frac{\pi}{2}$, $\frac{4}{5}$, $\frac{2}{3}$），呈现为随意的演算痕迹。底部有红色墨水标注的等式"$i^l = (-1)^{\frac{l}{2}}$"，与其他黑色公式形成视觉对比。整个页面的推导过程逻辑连贯，从变量替换到最终结果，层次分明，公式与文字混合排布，关键步骤之间有适当的换行和缩进，便于阅读推导流程。

<CTX>
{
   "topic": "勒让德多项式在特定角度的积分计算与奇偶性分析",
   "keywords": ["勒让德多项式", "复变积分路径", "三角替换", "奇偶性分析", "θ=π/2特例"],
   "summary": "本页完成勒让德多项式在θ=π/2时的具体积分计算，展示其奇偶性特征及闭合表达式，为后续物理应用提供数学基础",
   "pending_concepts": ["积分路径的几何意义与收敛性", "复指数形式与实数生成函数的转换条件", "奇偶性结果在多极展开中的物理诠释"]
}
</CTX>