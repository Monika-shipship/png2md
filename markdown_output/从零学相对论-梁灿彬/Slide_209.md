# Slide 209

对式(8-7-6)积分便知函数 $r_*(r)$ 可取如下形式：
$$
r_*(r) = r + 2M \ln\left( \frac{r}{2M} - 1 \right) \quad (8-7-8)
$$
刚才无非是做了一次坐标变换——从 2 维史瓦西系 $\{ t, r \}$ 变换到新系 $\{ t, r_* \}$，其中的 $r_*$ 称为乌龟坐标。式(8-7-7)就是 2 维史瓦西线元在新坐标系 $\{ t, r_* \}$ 的表达式（请记住：看任何线元时都应注意它是在哪一个坐标系的表达式）。由式(8-7-8)和式(8-7-4)可知 $t, r_*$ 的取值范围是
$$
-\infty < t < \infty, \quad -\infty < r_* < \infty \quad (8-7-9)
$$
用下式定义两个新坐标 $v$ 和 $u$：
$$
v \equiv t + r_*, \quad u \equiv t - r_* \quad (8-7-10a)
$$
其逆变换为
$$
t = \frac{v + u}{2}, \quad r_* = \frac{v - u}{2} \quad (8-7-10b)
$$
则
$$
-\mathrm{d}t^2 + \mathrm{d}r_*^2 = -\mathrm{d}v \, \mathrm{d}u \quad (8-7-11)
$$
故线元(8-7-7)成为
$$
\mathrm{d}\hat{s}^2 = -\left(1 - \frac{2M}{r}\right) \mathrm{d}v \, \mathrm{d}u \quad (8-7-12)
$$
读者对这一线元形式也许不熟悉。此处要补充一点有关线元的知识，仅以 2 维线元和坐标系 $(v, u)$ 为例，其最一般的形式为
$$
\mathrm{d}s^2 = g_{vv} \mathrm{d}v^2 + g_{vu} \mathrm{d}v \, \mathrm{d}u + g_{uv} \mathrm{d}u \, \mathrm{d}v + g_{uu} \mathrm{d}u^2 \quad (8-7-13)
$$
其中各项的系数 $g_{vv}, g_{vu}, g_{uv}$ 和 $g_{uu}$ 都可以是坐标 $v, u$ 的函数。线元必须满足两点要求（这是包含在线元定义中的，只不过我们一直未曾交代过）：
(1) 对称性，即 $g_{vu} = g_{uv}$，因而式(8-7-13)可简化为三项：
$$
\mathrm{d}s^2 = g_{vv} \mathrm{d}v^2 + 2 g_{vu} \mathrm{d}v \, \mathrm{d}u + g_{uu} \mathrm{d}u^2 \quad (8-7-14)
$$
(2) 可逆性，是指由 4 个系数排成的方阵 $\begin{bmatrix} g_{vv} & g_{vu} \\ g_{uv} & g_{uu} \end{bmatrix}$ 必须有逆，等价于要求这个方阵的行列式 $\begin{vmatrix} g_{vv} & g_{vu} \\ g_{uv} & g_{uu} \end{vmatrix}$ 非零。行列式为零也是一种奇性，以 $g$ 记此行列式，若线元在某处的 $g = 0$，就说它在该处有奇性。
现在回到式(8-7-12)，它无非是式(8-7-14)的特例，其系数行列式
$$
g = \begin{vmatrix} 0 & -\left(1 - \frac{2M}{r}\right)/2 \\ -\left(1 - \frac{2M}{r}\right)/2 & 0 \end{vmatrix} = -\frac{1}{4} \left(1 - \frac{2M}{r}\right)^2
$$
在 $r = 2M$ 处为零，说明线元(8-7-12)在 $r = 2M$ 处仍然奇异，所以还要继续努力。由式(8-7-10a)和式(8-7-9)可知 $v, u$ 的取值范围是
$$
-\infty < v, \ u < \infty \quad (8-7-15)
$$

> [!WARNING] 🛡️ 原文勘误  
> 1. OCR 将微分符号识别为 `dt`/`dr`，但根据 P-1 和 N+1 页的上下文（如 P-1 中的 `\mathrm{d}t^2` 和 N+1 中的 `\mathrm{d}v \, \mathrm{d}u`），所有微分符号应统一为 `\mathrm{d}` 以保持专业性和符号一致性。  
> 2. 式(8-7-10b) 中的除法符号 OCR 识别为 `/`，但 LaTeX 中应规范为 `\frac{v + u}{2}` 以符合数学排版标准。  
> 3. OCR 将取值范围 `(8-7-15)` 截断为不完整句，但根据 N+1 页首行内容完整补全为 `-\infty < v, \ u < \infty \quad (8-7-15)`，确保逻辑连贯。

<CTX>
{ "summary": "本页详细推导史瓦西时空的坐标变换过程，通过引入乌龟坐标 $r_*$ 和新坐标 $v,u$ 消除 $r=2M$ 处的坐标奇性，分析线元行列式在 $r=2M$ 处的奇性表现，并明确 $v,u$ 的取值范围。", "keywords": ["坐标变换", "乌龟坐标", "线元行列式", "坐标奇性", "取值范围"] }
</CTX>