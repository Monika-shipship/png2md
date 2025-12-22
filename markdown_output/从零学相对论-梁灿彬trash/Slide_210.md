# Slide 210

$-\infty < v,  u < \infty \quad .$ (8-7-15)

再用下式定义新坐标 $V$ 和 $U$：
$$V \equiv e^{\beta v}, \quad U \equiv -e^{-\beta u}, \quad (\beta \text{ 为待定常数}) \tag{8-7-16}$$

则 $V$ 和 $U$ 的取值范围为
$$0 < V < \infty \ , \quad -\infty < U < 0 \, . \tag{8-7-17}$$

而且
$$\mathrm{d}v  \mathrm{d}u = \beta^{-2} e^{\beta(u-v)}  \mathrm{d}V \mathrm{d}U \, , \tag{8-7-18}$$

故式(8-7-12)在新系的表达式为
$$\mathrm{d}\hat{s}^2 = -\left(1 - \frac{2M}{r}\right) \beta^{-2} e^{\beta(u-v)}  \mathrm{d}V  \mathrm{d}U = -\left(\frac{r-2M}{r}\right) \beta^{-2} e^{-2\beta r_*}  \mathrm{d}V  \mathrm{d}U \, , \tag{8-7-19}$$

其中第二步用到式(8-7-10b)。上式的系数行列式含因子 $(r-2M)/r$，在 $r=2M$ 处为零，仍为奇性。消除奇性的关键一步是设法消去这个因子。因子 $e^{-2\beta r_*}$ 可借式(8-7-8)表为
$$\begin{aligned}
e^{-2\beta r_*} &= e^{-2\beta r} \exp\left[ -4\beta M \ln\left(\frac{r-2M}{2M}\right) \right] \\
&= e^{-2\beta r} \exp\left[ \ln\left(\frac{r-2M}{2M}\right)^{-4\beta M} \right] = e^{-2\beta r} \left(\frac{2M}{r-2M}\right)^{4\beta M} \, , \quad (8-7-20)
\end{aligned}$$

代入式(8-7-19)便得
$$\mathrm{d}\hat{s}^2 = -\left(\frac{r-2M}{r}\right) \beta^{-2} e^{-2\beta r} \left(\frac{2M}{r-2M}\right)^{4\beta M}  \mathrm{d}V  \mathrm{d}U \, . \tag{8-7-21}$$

只要把待定常数 $\beta$ 选为
$$\beta = \frac{1}{4M} \, , \tag{8-7-22}$$

式(8-7-21)便成为
$$\mathrm{d}\hat{s}^2 = -\left(\frac{r-2M}{r}\right) \left(\frac{1}{4M}\right)^{-2} e^{-\frac{2r}{4M}} \left(\frac{2M}{r-2M}\right)  \mathrm{d}V  \mathrm{d}U = -\frac{32M^3}{r} e^{-\frac{r}{2M}}  \mathrm{d}V  \mathrm{d}U \, . \tag{8-7-23}$$

上式就是 2 维史瓦西线元在新坐标系 $(V, U)$ 的表达式。由于能导致线元在 $r=2M$ 处有奇性的因子 $r-2M$ 已被消去，上式在 $r=2M$ 处表现正常，不再奇异。可见 $r=2M$ 处的奇性的确可以通过坐标变换消除。你现在可以确定无疑地说史瓦西线元在 $r=2M$ 的奇性只是坐标奇性而已。不过，上式在 $r=0$ 处仍然是奇异的，事实上，计算表明，当你沿着一条曲线不断趋近 $r=0$ 时，你测得的时空曲率将趋于无限大(发散)，强烈暗示 $r=0$ 是不能消除的真奇点。

因为式(8-7-23)是线元在坐标系 $\{V, U\}$ 的表达式，所以式中的 $r$ 不应再看作坐标而应看作坐标 $V, U$ 的函数 $r(V, U)$。由 $V = e^{v/4M}, U = -e^{-u/4M}$ 及式(8-7-10b)、式(8-7-8)不难求得函数 $r(V, U)$ 的如下隐表达式：

> [!NOTE] 🖼️ Figure 描述  
> **图 8-13：史瓦西时空的克鲁斯科尔最大延拓**  
> - **坐标系**：垂直 T 轴（时间）与水平 X 轴（空间），原点居中。  
> - **子图 (a) 区域划分**：  
>   - 中心菱形非阴影区：T-X 平面主体，四角为斜线阴影区。  
>   - 黑洞区 (B)：中心区域；白洞区 (W)：T 轴负半轴下方。  
>   - 渐近平直区：X 轴正端 (A) 与负端 (A')，无因果联系。  
>   - 奇性线：上下两条锯齿状双曲线（标注 $r=0$），不属于时空。  
>   - 视界：四条 45° 辐射线（$N_1^+, N_2^+$ 为黑洞视界；$N_1^-, N_2^-$ 为白洞视界）。  
>   - 坐标轴：U 轴（左上 45° 线）、V 轴（右上 45° 线）；原点标记 $V=U=0$。  
> - **子图 (b) 等值线**：  
>   - 过原点的 ±45° 线：标注 $t=\pm\infty, r=2M$。  
>   - 双曲线族：以 45° 线为渐近线，$r=\text{常数}$（含 $r=2M$）与 $t=\text{常数}$。  
>   - 特征点：X 轴正端 $p$ 与负端 $p'$ 代表不同球面（非同一球面两点）。  
> - **关键约束**：非阴影区满足 $T^2 - X^2 < 1$（$r>0$），阴影区（$T^2 - X^2 \geq 1$）为奇性域。

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号一致性修正**：  
>    - 原 OCR 中 "$\mathrm{d}v \, \mathrm{d}u = \beta^{-2} e^{\beta(u-v)} \, \mathrm{d}V \mathrm{d}U$" 的 $e^{\beta(u-v)}$ 应为 $e^{\beta(u-v)}$（非 $\nu$），因 $u,v$ 为坐标（前文式 8-7-10a 定义），且 $u-v = -2r_*$（由式 8-7-10b 推导），故指数项正确。  
>    - 原文 "$\left(\frac{r}{2M}-1\right)e^{\frac{r}{2M}} = -VU$" 在式 (8-7-24) 中应为 $\left(\frac{r}{2M}-1\right)e^{r/(2M)} = -VU$（指数格式标准化）。  
> 2. **逻辑衔接修正**：  
>    - 式 (8-7-19) 中 "$e^{-2\beta r_*}$" 的推导需显式关联 $u-v = -2r_*$（由式 8-7-10b），原文隐含但未明示，已通过上下文补全。  
> 3. **OCR 错误修正**：  
>    - 原文 "$\mathrm{d}\hat{s}^2 = -\left(\frac{r-2M}{r}\right) \beta^{-2} e^{-2\beta r} \left(\frac{2M}{r-2M}\right)^{4\beta M} \, \mathrm{d}V \, \mathrm{d}U \, .$" 中多余逗号及空格已移除，符合 LaTeX 规范。

<CTX>
{ "summary": "本页详述克鲁斯科尔坐标系中消除史瓦西奇性的关键步骤：通过坐标变换 $\\{t,r\\} \\mapsto \\{V,U\\}$ 导出无奇性线元 (8-7-23)，证明 $r=2M$ 为坐标奇性，并建立 $r(V,U)$ 的隐函数关系。图 8-13 揭示最大延拓后的时空结构，含黑洞/白洞区与渐近平直区。", "keywords": ["坐标奇性", "克鲁斯科尔延拓", "乌龟坐标", "真奇点", "最大延拓"] }
</CTX>