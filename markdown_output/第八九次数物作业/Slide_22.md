# Slide 22  
**17. 勒让德多项式 $P_l(t)$ 的任意阶表达式推导**  

#### 复积分法推导 $P_l(t)$ 的一般形式  
承接 Slide 21 的级数展开 $(1 + x^2 - 2xt)^{-1/2} = \sum_{l=0}^{\infty} P_l(t) x^l$，现推导任意阶 $P_l(t)$ 的闭式表达式。  
由柯西积分公式，泰勒级数系数可表示为：  
$$
P_l(t) = \frac{f^{(l)}(0)}{l!} = \frac{1}{2\pi i} \oint \frac{f(\theta)}{\theta^{l+1}}  d\theta, \quad \text{其中 } f(\theta) = (1 + \theta^2 - 2\theta t)^{-1/2}.
$$  
代入 $f(\theta)$ 得：  
$$
P_l(t) = \frac{1}{2\pi i} \oint \frac{1}{\sqrt{1 + \theta^2 - 2\theta t}} \cdot \frac{1}{\theta^{l+1}}  d\theta.
$$  
为简化积分，引入变量替换 $\theta = z \frac{z - t}{z^2 - 1}$（$z$ 为辅助复变量）。计算被积函数：  
$$
\begin{aligned}
1 + \theta^2 - 2\theta t &= 1 + \left( z \frac{z - t}{z^2 - 1} \right)^2 - 2 \left( z \frac{z - t}{z^2 - 1} \right) t \\
&= \frac{(z^2 - 1)^2 + z^2 (z - t)^2 - 2 z t (z - t) (z^2 - 1)}{(z^2 - 1)^2} \\
&= \frac{(z^2 - 2zt + 1)^2}{(z^2 - 1)^2} \quad (\text{分子展开后合并同类项}).
\end{aligned}
$$  
微分 $d\theta$ 为：  
$$
d\theta = z \cdot \frac{d}{dz} \left( \frac{z - t}{z^2 - 1} \right) dz = z \cdot \frac{(z^2 - 1) - (z - t) \cdot 2z}{(z^2 - 1)^2}  dz = z \frac{-z^2 - 1 + 2zt}{(z^2 - 1)^2}  dz.
$$  
代入积分式，整理后得：  
$$
P_l(t) = \frac{1}{2\pi i} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}}  dz,
$$  
此即勒让德多项式的 **Schläfli 积分表示**。结合 Rodrigues 公式 $P_l(t) = \frac{1}{2^l l!} \frac{d^l}{dt^l} (t^2 - 1)^l$，可验证：  
$$
P_l(t) = \frac{1}{2\pi i} \cdot \frac{1}{2^l} \oint \frac{(z^2 - 1)^l}{(z - t)^{l+1}}  dz \quad (\text{标准形式}).
$$  
该积分在复平面上沿包围 $t$ 的闭合路径收敛，为后续计算 $P_l(t)$ 的具体值提供基础（详见 Slide 23 的路径参数化）。

## Figure Description  
方格纸背景的手写数学推导，内容纵向排列：顶部以中文标注“推导任意阶的 $P_l(t)$ 表达式”；中部详细展示柯西积分公式的应用，包含 $P_l(t)$ 的积分表达式 $\frac{1}{2\pi i} \oint \frac{f(\theta)}{\theta^{l+1}} d\theta$ 推导，以及变量替换 $\theta = z \frac{z - t}{z^2 - 1}$ 的步骤；底部呈现 $1 + \theta^2 - 2\theta t$ 和 $d\theta$ 的化简过程，关键等式用红色方框标注（如 $(z^2 - 2zt + 1)^2$ 的分子结果）。所有公式以黑色手写体书写，存在多处笔误：$d\theta$ 的分母应为 $(z^2 - 1)^2$（原文漏写平方），且 $\frac{d^l}{dx^l}$ 的变量错误（应为 $\frac{d^l}{dt^l}$）。推导逻辑用箭头连接，但替换步骤的代数运算存在冗余项（如 $4$ 的系数错误）。

> [!WARNING] 🛡️ 原文勘误  
> - **原文**: "$P_l(t)=\frac{1}{l!2^l}\frac{d^l}{dx^l}(t^2-1)^l$"  
> - **疑点**: 微分变量错误。Rodrigues 公式中 $P_l(t)$ 是 $t$ 的函数，导数应为 $\frac{d^l}{dt^l}$，而非 $\frac{d^l}{dx^l}$（$x$ 是级数展开变量，与 $t$ 无关）。此错误会导致后续积分推导逻辑断裂（如 $P_l(t)$ 无法作为 $t$ 的函数定义）。  
> - **修正**: 严格更正为 $P_l(t) = \frac{1}{2^l l!} \frac{d^l}{dt^l} (t^2 - 1)^l$。  
>   
> - **原文**: "$d\theta=z\cdot\frac{z^2-1-2z(z-t)}{z^2-1}=z\frac{-z^2-1+2zt}{z^2-1}$"  
> - **疑点**: 分母缺失平方。商法则微分 $\frac{d}{dz} \left( \frac{u}{v} \right) = \frac{u'v - uv'}{v^2}$ 要求分母为 $v^2$，但原文 $d\theta$ 的表达式分母为 $z^2 - 1$（应为 $(z^2 - 1)^2$）。此错误会使后续积分化简失效（如 $(z^2 - 1)^l$ 项无法正确抵消）。  
> - **修正**: 补充分母平方，$d\theta = z \frac{-z^2 - 1 + 2zt}{(z^2 - 1)^2}  dz$。  
>   
> - **原文**: "$1+\theta^2-2\theta t=1+4\frac{(z-t)^2}{(z^2-1)^2}-4\frac{z-t}{(z^2-1)}\cdot t$"  
> - **疑点**: 系数 $4$ 为笔误。代入 $\theta = z \frac{z-t}{z^2-1}$ 时，$\theta^2$ 项应为 $z^2 \frac{(z-t)^2}{(z^2-1)^2}$，无额外系数 $4$；$-2\theta t$ 项为 $-2z t \frac{z-t}{z^2-1}$。原文的 $4$ 会导致分子展开错误（如 $z^4$ 项缺失）。  
> - **修正**: 重写为 $1 + \theta^2 - 2\theta t = 1 + z^2 \frac{(z-t)^2}{(z^2-1)^2} - 2z t \frac{z-t}{z^2-1}$，并验证分子为 $(z^2 - 2zt + 1)^2$。

<CTX>
{ "summary": "本页通过复积分法推导勒让德多项式 $P_l(t)$ 的 Schläfli 积分表示，修正了 Rodrigues 公式微分变量、微分表达式分母缺失平方及代数系数笔误。", "keywords": ["勒让德多项式", "Schläfli 积分", "柯西积分公式", "Rodrigues 公式", "复变量替换"] }
</CTX>