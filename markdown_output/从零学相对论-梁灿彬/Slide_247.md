# Slide 247

A.2 几何单位制  

先求长度的几何制单位 $\hat{L}_{\text{几}}$。由速度定义易得量纲关系：  
\[
\dim L = (\dim T)(\dim V), \tag{A-8}
\]  
其中 $\dim L$ 代表长度的国际单位制单位与几何单位制单位的比值，即若以 $\hat{L}_{\text{国}}$ 和 $\hat{L}_{\text{几}}$ 分别代表长度的国际单位制和几何单位制单位，则  
\[
\dim L \equiv \hat{L}_{\text{国}} / \hat{L}_{\text{几}}. \tag{A-9}
\]  
注意到式 (A-8)，得  
\[
\hat{L}_{\text{几}} = \hat{L}_{\text{国}} / (\dim L) = \hat{L}_{\text{国}} (\dim T)^{-1} (\dim V)^{-1}. \tag{A-10}
\]  
而  
\[
\dim T = \frac{\hat{T}_{\text{国}}}{\hat{T}_{\text{几}}} = \frac{1\,\text{s}}{1\,\text{s}} = 1, \quad \dim V = \frac{\hat{V}_{\text{国}}}{\hat{V}_{\text{几}}} = \frac{1\,\text{m/s}}{c_{\text{国}}\,\text{m/s}} = \frac{1}{c_{\text{国}}}, \tag{A-11}
\]  
其中 $c_{\text{国}} = 3 \times 10^8$ 代表用国际单位制单位测光速所得的数。将式 (A-11) 代入式 (A-10) 得出几何单位制长度单位  
\[
\hat{L}_{\text{几}} = c_{\text{国}} \hat{L}_{\text{国}} = (3 \times 10^8) \times 1\,\text{m} = 3 \times 10^8\,\text{m}. \tag{A-12}
\]  

再求质量的几何制单位 $\hat{M}_{\text{几}}$。由 $f = ma$ 及 $f = G m_1 m_2 / r^2$ 可知质量的量纲式为  
\[
\dim M = (\dim T)(\dim V)^3 (\dim G)^{-1}. \tag{A-13}
\]  
再由 $\dim M = \hat{M}_{\text{国}} / \hat{M}_{\text{几}}$ 得  
\[
\hat{M}_{\text{几}} = \hat{M}_{\text{国}} / (\dim M) = \hat{M}_{\text{国}} (\dim T)^{-1} (\dim V)^{-3} (\dim G). \tag{A-14}
\]  
其中的 $\dim G$ 可求之如下：  
\[
\dim G = \frac{\hat{G}_{\text{国}}}{\hat{G}_{\text{几}}} = \frac{G_{\text{几}}}{G_{\text{国}}} = \frac{1}{G_{\text{国}}}, \tag{A-15}
\]  
此处 $G_{\text{国}} = 6.67 \times 10^{-11}$ 为国际单位制下引力常量的数值。将上式及式 (A-11) 代入式 (A-14) 便得几何单位制质量单位  
\[
\hat{M}_{\text{几}} = \frac{c_{\text{国}}^3}{G_{\text{国}}} \hat{M}_{\text{国}} = \frac{(3 \times 10^8)^3}{6.67 \times 10^{-11}} \times 1\,\text{kg} = 4 \times 10^{35}\,\text{kg}. \tag{A-16}
\]  

A.2.2 几何单位制公式转换为国际单位制公式  

本书由于使用几何单位制而使公式大为简化，但如果需要代入具体数值，最好先转换为国际单位制形式。利用量纲分析可以完成这一任务。为此，对几何单位制应该采用第三种看法，这时几何单位制与国际单位制就是同族单位制，区别只来自基本单位的不尽相同：  

> [!NOTE] 🖼️ Figure 描述  
> 本页无独立插图，但公式 (A-8) 至 (A-16) 构成逻辑推导链：  
> 1. 从速度定义导出长度量纲关系 (A-8)  
> 2. 结合单位比值定义 (A-9) 推导几何长度单位 (A-12)  
> 3. 从牛顿定律导出质量量纲关系 (A-13)  
> 4. 结合引力常量约束推导几何质量单位 (A-16)  
> 关键转换点：$\dim V = 1/c_{\text{国}}$ 建立光速桥梁，$\dim G = 1/G_{\text{国}}$ 体现引力常量归一化  

<CTX>  
{ "summary": "本页详细推导几何单位制基本单位（长度、质量）与国际单位制的转换关系，基于量纲分析建立 $\hat{L}_{\text{几}} = c_{\text{国}} \hat{L}_{\text{国}}$ 和 $\hat{M}_{\text{几}} = c_{\text{国}}^3 / G_{\text{国}} \cdot \hat{M}_{\text{国}}$ 的核心公式，为后续公式转换奠定基础。", "keywords": ["量纲分析", "几何单位制", "国际单位制转换", "基本单位推导", "引力常量"] }  
</CTX>