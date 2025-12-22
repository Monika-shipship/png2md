# Slide 202

## 7. 坐标定义的延拓与角色互换

我们从史瓦西坐标系 $\{t, r, \theta, \varphi\}$ 出发，通过如下的系列坐标变换  
$$\{t, r, \theta, \varphi\} \mapsto \{t, r_*, \theta, \varphi\} \mapsto \{v, u, \theta, \varphi\} \mapsto \{V, U, \theta, \varphi\}$$  
将线元表达式(8-7-25)延拓至 $r=2M$ 处表现良好，从而从 A 区出发得到最大延拓（包含四个区 A, B, W, A' 以及两张 3 维面 $\mathrm{N}_1$, $\mathrm{N}_2$）。由于延拓是借助于坐标 $V$, $U$ 实现的，$V$, $U$ 在全时空均有明确定义。现需重点考察：在除 A 区外的三个区中，坐标 $t$ 和 $r$ 如何定义？

式(8-7-23)中含变量 $r$，前文已明确应将其视为 $V$, $U$ 的函数 $r(V, U)$，其隐表达式为式(8-7-24)。因此，延拓过程自然将式(8-7-24)作为 $r$ 在其他三区的定义式。然而，坐标 $t$ 在其他三区未被明确定义。回顾 A 区中 $V$, $U$ 与 $t$, $r_*$ 的关系：  
$$
V = e^{\frac{r_* + t}{4M}}, \quad U = -e^{\frac{r_* - t}{4M}}, \tag{8-7-32}
$$  
可逆向利用此关系，通过以下约定定义其他三区的 $t$ 坐标：  
$$
\begin{aligned}
\text{B 区} \quad & V = e^{\frac{r_* + t}{4M}}, \quad U = e^{\frac{r_* - t}{4M}}; \\
\text{W 区} \quad & V = -e^{\frac{r_* + t}{4M}}, \quad U = -e^{\frac{r_* - t}{4M}}; \tag{8-7-32'} \\
\text{A'区} \quad & V = -e^{\frac{r_* + t}{4M}}, \quad U = e^{\frac{r_* - t}{4M}}, \\
\end{aligned}
$$  
其中 $r_*$ 由 $r$ 依下式定义：  
$$
r_* \equiv r + 2M \ln \left| \frac{r}{2M} - 1 \right|. \tag{8-7-33}
$$  

将线元(8-7-25)应用于 B, W, A' 区，并借助式(8-7-32')与(8-7-33)改写为以 $t$, $r$ 表出的形式，结果仍为式(8-7-1)，但 $r$ 的取值范围发生分化：  
- B, W 区：$0 < r < 2M$  
- A' 区：$2M < r < \infty$（同 A 区）  

四个区中坐标 $T$, $X$ 与 $t$, $r$ 的关系如下（证明留作习题，$\sinh$ 和 $\cosh$ 分别表示双曲正弦和余弦）：  
$$
\begin{aligned}
\text{A 区} \quad & 
\begin{cases}
T = \sqrt{\dfrac{r}{2M} - 1}  e^{\frac{r}{4M}} \sinh \left( \dfrac{t}{4M} \right), \\
X = \sqrt{\dfrac{r}{2M} - 1}  e^{\frac{r}{4M}} \cosh \left( \dfrac{t}{4M} \right),
\end{cases} \tag{8-7-34} \\
\text{B 区} \quad & 
\begin{cases}
T = \sqrt{1 - \dfrac{r}{2M}}  e^{\frac{r}{4M}} \cosh \left( \dfrac{t}{4M} \right), \\
X = \sqrt{1 - \dfrac{r}{2M}}  e^{\frac{r}{4M}} \sinh \left( \dfrac{t}{4M} \right),
\end{cases} \tag{8-7-35} \\
\text{W 区} \quad & 
\begin{cases}
T = -\sqrt{1 - \dfrac{r}{2M}}  e^{\frac{r}{4M}} \cosh \left( \dfrac{t}{4M} \right), \\
X = -\sqrt{1 - \dfrac{r}{2M}}  e^{\frac{r}{4M}} \sinh \left( \dfrac{t}{4M} \right).
\end{cases} \tag{8-7-36}
\end{aligned}
$$

> [!NOTE] 🖼️ Figure 描述  
> 本页延续图 8-13 的时空结构（见前页），重点展示坐标变换的数学实现。图 8-13(a) 的阴影区外四区划分（A, B, A', W）与坐标关系通过上述公式量化：  
> - **A 区**（$X > 0$, $X^2 > T^2$）：$r > 2M$，$t$ 为时间坐标，$r$ 为空间坐标  
> - **B 区**（$T > 0$, $X^2 < T^2$）：$0 < r < 2M$，$r$ 为时间坐标，$t$ 为空间坐标  
> - **W 区**（$T < 0$, $X^2 < T^2$）：$0 < r < 2M$，$r$ 为时间坐标  
> - **A'区**（$X < 0$, $X^2 > T^2$）：$r > 2M$，$t$ 为时间坐标  
> 公式(8-7-34)至(8-7-36)揭示：当穿越视界 $\mathrm{N}_1$/$\mathrm{N}_2$（$r=2M$）时，$t$ 与 $r$ 的时空角色发生互换——此现象在几何上体现为双曲函数参数的符号与根号内表达式的切换，直接导致 B/W 区线元系数变号（$1-2M/r < 0$），从而否定了静态性假设。

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号统一性修正**：  
>    - 原文公式中使用 `\text{sh}` 和 `\text{ch}`（如式 8-7-34），但根据后文 [N+1] 页及标准微分几何惯例，应统一为 `\sinh` 和 `\cosh`（如式 8-7-37 中的 `\sinh`）。已修正所有相关公式，确保符号一致性。  
> 2. **逻辑衔接优化**：  
>    - 原文“式(8-7-23)中含有变量 $r$”表述模糊，结合 [P-1] 页式(8-7-24)的隐函数关系，明确补充“$r$ 应视为 $V,U$ 的函数 $r(V,U)$”，避免读者误解 $r$ 为独立变量。  
> 3. **术语精确化**：  
>    - 原文“两张 3 维面 $N_1$, $N_2$”中 $N$ 应为正体（非斜体），因代表特定超曲面而非变量。统一修正为 $\mathrm{N}_1$, $\mathrm{N}_2$，与 [P-1] 页“$\mathrm{N}_1^+$”符号体系一致。

<CTX>
{ "summary": "本页系统推导史瓦西时空最大延拓中非 A 区的坐标定义，揭示 $t$ 与 $r$ 在视界两侧的时空角色互换现象，并通过四区坐标变换公式量化该效应。核心结论：B/W 区中 $r$ 为时间坐标，直接导致非静态性。", "keywords": ["坐标延拓", "角色互换", "视界", "双曲函数", "非静态时空"] }
</CTX>