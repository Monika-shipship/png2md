# Slide 21  
**16. 勒让德多项式及其在电势展开中的应用**  

#### 电势问题的级数展开背景  
考虑源点电荷密度 $\rho(\vec{r}')$ 在场点 $\vec{r}$ 处产生的电势：  
$$
V(\vec{r}) = \frac{1}{4\pi\epsilon_0} \int \rho(\vec{r}') \frac{dV'}{|\vec{r} - \vec{r}'|},
$$  
其中带撇变量（如 $\vec{r}'$）表示源点坐标。由余弦定理，距离 $z = |\vec{r} - \vec{r}'|$ 满足：  
$$
z^2 = r^2 + r'^2 - 2rr'\cos\theta \quad \Rightarrow \quad z = r \sqrt{1 + \left(\frac{r'}{r}\right)^2 - 2\frac{r'}{r}\cos\theta}.
$$  
引入无量纲变量 $x = \frac{r'}{r}$，电势核可表示为：  
$$
\frac{1}{z} = \frac{1}{r} (1 + x^2 - 2x\cos\theta)^{-1/2}.
$$  
对 $(1 + x^2 - 2x\cos\theta)^{-1/2}$ 进行二项式级数展开：  
- 令 $\xi = x^2 - 2x\cos\theta$，利用 $(1 + \xi)^{-1/2} = 1 - \frac{1}{2}\xi + \frac{3}{8}\xi^2 + \mathcal{O}(\xi^3)$，  
- 代入得：  
  $$
  \begin{aligned}
  (1 + x^2 - 2x\cos\theta)^{-1/2} &= 1 - \frac{1}{2}(x^2 - 2x\cos\theta) + \frac{3}{8}(x^2 - 2x\cos\theta)^2 + \cdots \\
  &= 1 + x\cos\theta + \left(\frac{3}{2}\cos^2\theta - \frac{1}{2}\right)x^2 + \mathcal{O}(x^3).
  \end{aligned}
  $$  
令 $t = \cos\theta$，则展开式可写为：  
$$
(1 + x^2 - 2xt)^{-1/2} = \sum_{l=0}^{\infty} P_l(t) x^l,
$$  
其中 $P_l(t)$ 为 **勒让德多项式**，其低阶形式为：  
$$
P_0(t) = 1, \quad P_1(t) = t, \quad P_2(t) = \frac{1}{2}(3t^2 - 1).
$$  
该级数在 $|x| \leq 1$ 时收敛，为后续推导任意阶 $P_l(t)$ 奠定基础（详见 Slide 22）。  

## Figure Description  
方格纸背景的手写数学推导，内容纵向排列：左侧为电势问题的物理示意图（坐标原点 $O$ 处标有场点 $\vec{r}$，源点 $\vec{r}'$ 与 $\vec{r}$ 夹角 $\theta$，体积元 $dV'$ 附近标有 $\rho(\vec{r}')$，红色箭头表示 $\vec{z} = \vec{r} - \vec{r}'$）；右侧为公式推导过程，包含余弦定理应用、变量替换 $x = r'/r$、二项式展开 $(1+\xi)^{-1/2}$ 的分步计算，以及 $P_l(t)$ 的定义与低阶特例。关键步骤用等号对齐，$P_0, P_1, P_2$ 用方框标注，手写体中存在符号笔误（如二项式展开项未正确展开 $\xi^2$）。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$(1 + x^2 - 2x\cos\theta)^{-\frac{1}{2}} = 1 - \frac{1}{2}x^2 + \cos\theta \cdot x + \frac{3}{8}(4x^2\cos^2\theta)$"  
> - **疑点**:  
>   1. 二项式展开错误：$\xi = x^2 - 2x\cos\theta$ 代入 $(1+\xi)^{-1/2}$ 时，$\frac{3}{8}\xi^2$ 项应展开为 $\frac{3}{8}(x^4 - 4x^3\cos\theta + 4x^2\cos^2\theta)$，但原文仅保留 $4x^2\cos^2\theta$ 项，遗漏 $x^4$ 和 $x^3$ 项，导致 $x^2$ 项系数计算错误（正确应为 $\frac{3}{2}\cos^2\theta - \frac{1}{2}$，但原文形式缺失交叉项）。  
>   2. 符号冗余：$\frac{3}{8}(4x^2\cos^2\theta)$ 写法易引发歧义，应明确为 $\frac{3}{8} \times 4x^2\cos^2\theta = \frac{3}{2}x^2\cos^2\theta$，但此表达式未体现 $\xi^2$ 展开的完整性。  
> - **修正**: 严格按二项式定理重写展开式：  
>   $$
>   (1 + x^2 - 2x\cos\theta)^{-1/2} = 1 + x\cos\theta + \left(\frac{3}{2}\cos^2\theta - \frac{1}{2}\right)x^2 + \mathcal{O}(x^3),
>   $$  
>   其中 $x^2$ 项系数由 $-\frac{1}{2}(x^2) + \frac{3}{8}(4x^2\cos^2\theta) = -\frac{1}{2}x^2 + \frac{3}{2}x^2\cos^2\theta$ 合并而来（$x^3$ 及高阶项在 $|x| \ll 1$ 时可忽略）。  

<CTX>
{ "summary": "本页推导电势问题中 $1/z$ 的级数展开，引入勒让德多项式 $P_l(t)$ 定义及低阶形式，为任意阶 $P_l(t)$ 的严格推导做铺垫", "keywords": ["勒让德多项式", "电势展开", "二项式级数", "$P_l(t)$", "余弦定理"] }
</CTX>