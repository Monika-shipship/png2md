# Slide 26

本页继续推进勒让德多项式正交性关系的证明，通过对生成函数乘积积分 $ I_1 = \int_{-1}^{1} G(x,t)G(u,t)\,dt $ 的显式计算，将其转化为关于变量 $ x $ 和 $ u $ 的闭合表达式，并通过变量替换与对数展开获得级数形式，为后续提取正交内积 $ \int_{-1}^{1} P_l(t)P_m(t)\,dt $ 提供基础。

## 正交性积分的显式计算

考虑生成函数乘积的积分：
$$
I_1 = \int_{-1}^{1} \frac{1}{pq}\,dt,
\quad \text{其中} \quad
p = \sqrt{1 + x^2 - 2xt},\quad
q = \sqrt{1 + u^2 - 2ut}.
$$

利用微分关系：
$$
2p\,dp = -2x\,dt \quad \Rightarrow \quad \frac{dt}{p} = -\frac{1}{x}\,dp,
\quad
2q\,dq = -2u\,dt \quad \Rightarrow \quad dt = -\frac{q}{u}\,du \text{（此处用于辅助变换）}.
$$

将 $ dt $ 代入并整理得：
$$
I_1 = \int_{-1}^{1} \frac{1}{pq}\,dt = -\frac{1}{x} \int \frac{dp}{q},
\quad \text{沿路径从 } t=-1 \text{ 到 } t=1.
$$

引入守恒量 $ C $，由下式确定：
$$
up^2 - xq^2 = C.
$$

代入边界 $ t = \pm 1 $ 计算常数 $ C $：
$$
C = u(1 + x^2 \mp 2x) - x(1 + u^2 \mp 2u) \Big|_{t=\pm1}
\Rightarrow C = u - x + ux(x - u) = (u - x)(1 - ux).
$$

令新变量：
$$
r = \sqrt{u}\,p, \quad s = \sqrt{x}\,q,
\quad \Rightarrow \quad r^2 - s^2 = C = (u - x)(1 - ux).
$$

此时有：
$$
q = \frac{1}{\sqrt{x}} s, \quad dp = \frac{1}{\sqrt{u}} dr,
\quad \Rightarrow \quad \frac{dp}{q} = \frac{\sqrt{x}}{\sqrt{u}} \frac{dr}{s}.
$$

因此积分变为：
$$
I_1 = -\frac{1}{x} \cdot \frac{\sqrt{x}}{\sqrt{u}} \int \frac{dr}{s} = -\frac{1}{\sqrt{xu}} \int \frac{dr}{s}.
$$

由 $ r^2 - s^2 = C $ 可得 $ r\,dr = s\,ds $，于是：
$$
\frac{dr}{s} = \frac{ds}{r} = \frac{d(r+s)}{r+s} = d(\ln|r+s|).
$$

积分结果为：
$$
I_1 = -\frac{1}{\sqrt{xu}} \left[ \ln|r + s| \right]_{t=-1}^{t=1}.
$$

代入 $ r = \sqrt{u}\,p = \sqrt{u(1 + x^2 - 2xt)} $, $ s = \sqrt{x(1 + u^2 - 2ut)} $，在端点处计算：

- 当 $ t = 1 $:
  $$
  r + s = \sqrt{u}(1 - x) + \sqrt{x}(1 - u)
  $$
- 当 $ t = -1 $:
  $$
  r + s = \sqrt{u}(1 + x) + \sqrt{x}(1 + u)
  $$

注意：实际上 $ p = \sqrt{(1 - xt)^2 + \cdots} $ 应取正值，且 $ \sqrt{1 + x^2 - 2xt} = |1 - x t| $ 在 $ |x|<1 $ 下为正，故直接使用：
$$
\sqrt{1 + x^2 - 2x t} \Big|_{t=1} = |1 - x| = 1 - x \quad (\text{若 } |x| < 1),
\quad \text{同理其他项。}
$$

因此：
$$
I_1 = -\frac{1}{\sqrt{xu}} \ln \left( \frac{ \sqrt{u}(1 - x) + \sqrt{x}(1 - u) }{ \sqrt{u}(1 + x) + \sqrt{x}(1 + u) } \right).
$$

化简分子与分母：

**分子**：
$$
\sqrt{u}(1 - x) + \sqrt{x}(1 - u) = \sqrt{u} + \sqrt{x} - \sqrt{u}x - \sqrt{x}u
= (\sqrt{u} + \sqrt{x}) - \sqrt{ux}(\sqrt{x} + \sqrt{u})
= (\sqrt{u} + \sqrt{x})(1 - \sqrt{ux}).
$$

**分母**：
$$
\sqrt{u}(1 + x) + \sqrt{x}(1 + u) = \sqrt{u} + \sqrt{x} + \sqrt{u}x + \sqrt{x}u
= (\sqrt{u} + \sqrt{x}) + \sqrt{ux}(\sqrt{x} + \sqrt{u})
= (\sqrt{u} + \sqrt{x})(1 + \sqrt{ux}).
$$

所以：
$$
I_1 = -\frac{1}{\sqrt{xu}} \ln \left( \frac{1 - \sqrt{ux}}{1 + \sqrt{ux}} \right)
= \frac{1}{\sqrt{xu}} \ln \left( \frac{1 + \sqrt{ux}}{1 - \sqrt{ux}} \right).
$$

利用对数恒等式：
$$
\ln\left( \frac{1+z}{1-z} \right) = 2 \sum_{k=0}^{\infty} \frac{z^{2k+1}}{2k+1}, \quad |z| < 1,
$$
令 $ z = \sqrt{ux} $，则：
$$
I_1 = \frac{1}{\sqrt{xu}} \cdot 2 \sum_{k=0}^{\infty} \frac{ (\sqrt{ux})^{2k+1} }{2k+1}
= 2 \sum_{k=0}^{\infty} \frac{ (ux)^k }{2k+1}.
$$

最终得到：
$$
I_1 = 2 \sum_{k=0}^{\infty} \frac{(ux)^k}{2k+1}.
$$

该结果是 $ x $ 和 $ u $ 的双变量幂级数，其系数将用于匹配原始双重级数展开中的 $ \int_{-1}^{1} P_l(t)P_m(t)\,dt $。

## Figure Description

图示可能包含生成函数 $ G(x,t) = \frac{1}{\sqrt{1 - 2xt + x^2}} $ 的几何解释或积分路径示意图，重点展示变量替换 $ r = \sqrt{u} p,\, s = \sqrt{x} q $ 如何将积分转化为双曲型坐标下的对数形式。也可能显示函数 $ \ln\left( \frac{1+\sqrt{ux}}{1-\sqrt{ux}} \right) $ 的级数收敛行为。

<CTX>
{
  "topic": "生成函数乘积积分的闭合解与级数展开",
  "keywords": ["生成函数乘积", "正交性积分", "变量替换", "对数展开", "幂级数匹配"],
  "summary": "通过巧妙的变量替换和守恒量构造，成功计算了生成函数乘积的积分 $ I_1 = \\int_{-1}^{1} G(x,t)G(u,t)\\,dt $，得到了闭合表达式 $ \\frac{1}{\\sqrt{xu}} \\ln\\left( \\frac{1 + \\sqrt{ux}}{1 - \\sqrt{ux}} \\right) $，并进一步展开为幂级数 $ 2 \\sum_{k=0}^{\\infty} \\frac{(ux)^k}{2k+1} $，为提取勒让德多项式的正交内积做好准备。",
  "last_formula_context": "最后一个公式是 $ I_1 = 2 \\sum_{k=0}^{\\infty} \\frac{(ux)^k}{2k+1} $，它表示生成函数乘积积分的级数展开，其系数对应 $ \\int_{-1}^{1} P_l(t)P_m(t)\\,dt $ 的加权和，下一页将进行级数匹配以得出正交性关系的具体形式。"
}
</CTX>