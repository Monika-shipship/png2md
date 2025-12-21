# Slide 26

$$ I_1 = \int \frac{1}{pq} \, dt \quad , \quad 2p \, dp = -2x \, dt \implies \frac{dt}{p} = -\frac{1}{x} \, dp $$
$$ 2q \, dq = -2u \, dt $$
$$ I_1 = \left(1 - \frac{1}{x}\right) \int \frac{dp}{q} \quad , \quad u p^2 - x q^2 = C = u + u x^2 - x - x u^2 $$
$$ = u - x + ux(x - u) $$
$$ = (u - x)(1 - ux) $$
令 $ r = \sqrt{u} p $, $ s = \sqrt{x} q $  
则 $ r^2 - s^2 = C $, $ q = \frac{1}{\sqrt{x}} s $  
$$ I_1 = -\frac{1}{x} \cdot \frac{\sqrt{x}}{\sqrt{u}} \int \frac{dr}{s} \quad , \quad r \, dr = s \, ds $$
$$ \frac{dr}{s} = \frac{ds}{r} = \frac{d(r+s)}{r+s} = d(\ln|r+s|) $$
$$ = -\frac{1}{\sqrt{xu}} \ln |r + s| $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \sqrt{u} \sqrt{1+x^2-2xt} + \sqrt{x} \sqrt{1+u^2-2ut} \right) \bigg|_{t=-1}^{t=1} $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \frac{\sqrt{u}(1-x) + \sqrt{x}(1-u)}{\sqrt{u}(1+x) + \sqrt{x}(1+u)} \right) $$
$$ = -\frac{1}{\sqrt{xu}} \ln \left( \frac{\sqrt{u} + \sqrt{x} - \sqrt{ux} - u\sqrt{x}}{\sqrt{u} + \sqrt{x} + \sqrt{ux} + u\sqrt{x}} \right) \quad \text{有理化} $$
$$ \frac{\sqrt{u} + \sqrt{x} - \sqrt{ux}(\sqrt{x} + \sqrt{u})}{(\sqrt{u} + \sqrt{x})(1 - \sqrt{ux})} = \frac{1 - \sqrt{ux}}{1 + \sqrt{ux}} $$
$$ = -\frac{1}{\sqrt{xu}} \ln \frac{1 - \sqrt{ux}}{1 + \sqrt{ux}} = \frac{1}{\sqrt{xu}} \ln \frac{1 + \sqrt{ux}}{1 - \sqrt{ux}} $$
展开 $ I_1 = \frac{1}{\sqrt{xu}} \left[ \ln(1 + \sqrt{ux}) - \ln(1 - \sqrt{ux}) \right] $

## Figure & Layout Description
图片为方格纸背景的手写数学推导，使用黑色墨水书写。整体布局为多列垂直排列的公式推导：左侧主要展示积分表达式与变量替换过程，右侧为代数展开与化简步骤。公式间通过等号与箭头符号连接，关键推导步骤（如"令 r=√u p"、"有理化"）以中文标注。积分上下限标记在公式右侧，部分分式结构通过水平分数线清晰分隔。底部包含对数函数的泰勒展开式（ln(1+x)等），以三行并列形式呈现。所有数学符号（如√, ∫, ln）均采用标准手写体，变量下标与上标位置准确，方格纸网格线作为排版基准，确保公式对齐。

<CTX>
{
   "topic": "勒让德多项式正交性证明的积分推导",
   "keywords": ["勒让德多项式", "正交性证明", "变量替换", "对数展开", "积分计算"],
   "summary": "本页完成勒让德多项式正交性证明中的关键积分计算，通过变量替换与对数展开验证正交关系",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>