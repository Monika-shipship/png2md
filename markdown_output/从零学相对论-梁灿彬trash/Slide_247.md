# Slide 247

A.2 几何单位制

先求长度的几何制单位 $\hat{L}_{\text{几}}$。由速度定义易得量纲关系：
$$
\dim L = (\dim T)(\dim V),
$$
其中 $\dim L$ 代表长度的国际单位制单位与几何单位制单位的比值，即若以 $\hat{L}_{\text{国}}$ 和 $\hat{L}_{\text{几}}$ 分别代表长度的国际单位制和几何单位制单位，则
$$
\dim L \equiv \hat{L}_{\text{国}} / \hat{L}_{\text{几}}.
$$
注意到式 (A-8)，得
$$
\hat{L}_{\text{几}} = \hat{L}_{\text{国}} / (\dim L) = \hat{L}_{\text{国}} (\dim T)^{-1} (\dim V)^{-1}.
$$
而
$$
\dim T = \frac{\hat{T}_{\text{国}}}{\hat{T}_{\text{几}}} = \frac{1\,\text{s}}{1\,\text{s}} = 1, \quad \dim V = \frac{\hat{V}_{\text{国}}}{\hat{V}_{\text{几}}} = \frac{1\,\text{m/s}}{c_{\text{国}}\,\text{m/s}} = \frac{1}{c_{\text{国}}},
$$
其中 $c_{\text{国}} = 3 \times 10^8$ 代表用国际单位制单位测光速所得的数。式 (A-11) 代入式 (A-10) 得出几何单位制长度单位：
$$
\hat{L}_{\text{几}} = c_{\text{国}} \hat{L}_{\text{国}} = (3 \times 10^8) \times 1\,\text{m} = 3 \times 10^8\,\text{m}.
$$

再求质量的几何制单位 $\hat{M}_{\text{几}}$。由 $f = ma$ 及 $f = G m_1 m_2 / r^2$ 可知质量的量纲式为
$$
\dim M = (\dim T)(\dim V)^3 (\dim G)^{-1}.
$$
再由 $\dim M = \hat{M}_{\text{国}} / \hat{M}_{\text{几}}$ 得
$$
\hat{M}_{\text{几}} = \hat{M}_{\text{国}} / (\dim M) = \hat{M}_{\text{国}} (\dim T)^{-1} (\dim V)^{-3} (\dim G).
$$
其中的 $\dim G$ 可求之如下：
$$
\dim G = \frac{\hat{G}_{\text{国}}}{\hat{G}_{\text{几}}} = \frac{G_{\text{几}}}{G_{\text{国}}} = \frac{1}{G_{\text{国}}},
$$
将上式及式 (A-11) 代入式 (A-14) 便得几何单位制质量单位：
$$
\hat{M}_{\text{几}} = \frac{c_{\text{国}}^3}{G_{\text{国}}} \hat{M}_{\text{国}} = \frac{(3 \times 10^8)^3}{6.67 \times 10^{-11}} \times 1\,\text{kg} = 4 \times 10^{35}\,\text{kg}.
$$

A.2.2 几何单位制公式转换为国际单位制公式

本书由于使用几何单位制而使公式大为简化，但如果需要代入具体数值，最好先转换为国际单位制形式。利用量纲分析可以完成这一任务。为此，对几何单位制应该采用第三种看法，这时几何单位制与国际单位制就是同族单位制，区别只来自基本单位的不尽相同。

> [!NOTE] 🖼️ Figure 描述  
> 本页核心计算流程图示：  
> 1. **长度单位推导**：从 $\dim L = (\dim T)(\dim V)$ 出发，结合 $\dim T=1$ 和 $\dim V=1/c_{\text{国}}$，导出 $\hat{L}_{\text{几}} = c_{\text{国}} \hat{L}_{\text{国}}$  
> 2. **质量单位推导**：从牛顿第二定律 $f=ma$ 和万有引力定律 $f=G m_1 m_2 / r^2$ 出发，建立量纲关系 $\dim M = (\dim T)(\dim V)^3 (\dim G)^{-1}$，最终导出 $\hat{M}_{\text{几}} = c_{\text{国}}^3 / G_{\text{国}} \cdot \hat{M}_{\text{国}}$  
> 3. **关键转换因子**：  
>    - $c_{\text{国}} = 3 \times 10^8$（国际单位制下光速数值）  
>    - $G_{\text{国}} = 6.67 \times 10^{-11} \text{m}^3 \text{kg}^{-1} \text{s}^{-2}$（国际单位制下引力常量数值）  
> 建议用分步框图表示量纲传递链：$T \rightarrow L$（通过 $c$）→ $M$（通过 $G$）

> [!WARNING] 🛡️ 原文勘误  
> 1. 符号修正：原文中 "$f = g m_1 m_2 / r^2$" 的 $g$ 应为 $G$（引力常量），与前后文 [P-1] 和 [N+1] 中的 $G$ 保持一致。OCR 误将大写 $G$ 识别为小写 $g$。  
> 2. 公式优化：式 (A-15) 中 "$6.67 \times 10^{-11}$" 应显式替换为 $G_{\text{国}}$，以保持符号一致性（[N+2] 中式 A-26 已使用 $G_{\text{国}}$）。  
> 3. 量纲定义补充：原文 "$\dim G = \frac{G_{\text{几}}}{G_{\text{国}}}$" 需明确 $G_{\text{几}}=1$（几何制定义），故 $\dim G = 1/G_{\text{国}}$，避免歧义。

<CTX>
{ "summary": "本页推导几何单位制的基本单位（长度、质量）与国际单位制的转换关系，核心是通过量纲分析建立 $\hat{L}_{\text{几}} = c_{\text{国}} \hat{L}_{\text{国}}$ 和 $\hat{M}_{\text{几}} = c_{\text{国}}^3 / G_{\text{国}} \hat{M}_{\text{国}}$，为后续公式转换奠定基础。", "keywords": ["量纲分析", "几何单位制", "国际单位制转换", "基本单位推导", "引力常量"] }
</CTX>