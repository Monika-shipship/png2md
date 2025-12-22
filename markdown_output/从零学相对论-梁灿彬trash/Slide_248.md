# Slide 248

别只来自基本单位的不尽相同：  
$$ \hat{T}_{\text{国}} = 1  \text{s}, \quad \hat{L}_{\text{国}} = 1  \text{m}, \quad \hat{M}_{\text{国}} = 1  \text{kg}, \tag{A-17a} $$  
$$ \hat{T}_{\text{几}} = 1  \text{s}, \quad \hat{L}_{\text{几}} = 3 \times 10^{8}  \text{m} = c_{\text{国}}  \text{m}, \quad \hat{M}_{\text{几}} = 4 \times 10^{35}  \text{kg}. \tag{A-17b} $$  

（请特别注意上式中的 $c_{\text{国}} = 3 \times 10^{8}$ 是以国际单位制单位测光速所得的数）。下面用三个例子介绍一种简便实用的转换方法 [另一种方法见梁灿彬、周彬 (2006) 附录 A]。

**例 1** 已知洛伦兹变换 (第一式) 的几何单位制形式为 $t' = \gamma (t - vx)$，求其国际单位制形式。  

**解** 为区分起见，给字母补注下标以表明它是用哪个单位制的单位测得的数。例如，$t_{\text{几}}$ 代表用几何单位制单位测时间所得的数。于是已知公式 $t' = \gamma (t - vx)$ 可以更明确地写成  
$$ t'_{\text{几}} = \gamma (t_{\text{几}} - v_{\text{几}} x_{\text{几}}). \tag{A-18} $$  
注意到式 (A-17)，有 $x_{\text{几}} / x_{\text{国}} = \hat{L}_{\text{国}} / \hat{L}_{\text{几}} = 1 / c_{\text{国}}$，故  
$$ x_{\text{几}} = x_{\text{国}} / c_{\text{国}}, \tag{A-19} $$  
再由  
$$ v_{\text{几}} / v_{\text{国}} = \hat{V}_{\text{国}} / \hat{V}_{\text{几}} = 1  \text{m} \cdot \text{s}^{-1} / (3 \times 10^{8}  \text{m} \cdot \text{s}^{-1}) = 1 / c_{\text{国}} \tag{A-20} $$  
又得  
$$ v_{\text{几}} = v_{\text{国}} / c_{\text{国}}, \tag{A-21} $$  
所以  
$$ v_{\text{几}} x_{\text{几}} = v_{\text{国}} x_{\text{国}} / c_{\text{国}}^{2}. \tag{A-22} $$  
另一方面，由 $\hat{T}_{\text{几}} = 1  \text{s} = \hat{T}_{\text{国}}$ 又知 $t_{\text{几}} = t_{\text{国}}$ 及 $t'_{\text{几}} = t'_{\text{国}}$，与式 (A-22) 一同代入式 (A-18) 得 $t'_{\text{国}} = \gamma (t_{\text{国}} - v_{\text{国}} x_{\text{国}} / c_{\text{国}}^{2})$，去掉下标便得洛伦兹变换 (第一式) 的国际单位制形式：  
$$ t' = \gamma (t - vx / c^{2}). \tag{[解毕]} $$  

**例 2** 已知 2 维闵氏线元的几何单位制形式为 $\mathrm{d}s^{2} = -\mathrm{d}t^{2} + \mathrm{d}x^{2}$，求其国际单位制形式。  

**解** 把上式明确写成  
$$ \mathrm{d}s_{\text{几}}^{2} = -\mathrm{d}t_{\text{几}}^{2} + \mathrm{d}x_{\text{几}}^{2}. \tag{A-23} $$  
由 $t_{\text{几}} = t_{\text{国}}$ 及 $x_{\text{几}} = x_{\text{国}} / c_{\text{国}}$ [式 (A-19)] 得  
$$ \mathrm{d}t_{\text{几}}^{2} = \mathrm{d}t_{\text{国}}^{2}, \quad \mathrm{d}x_{\text{几}}^{2} = \mathrm{d}x_{\text{国}}^{2} / c_{\text{国}}^{2}. \tag{A-24} $$  
由式 (2-1-11) 可知 $\mathrm{d}s^{2}$ 与 $\mathrm{d}x^{2}$ 单位相同，故仿照式 (A-24) 又有 $\mathrm{d}s_{\text{几}}^{2} = \mathrm{d}s_{\text{国}}^{2} / c_{\text{国}}^{2}$，与式 (A-24) 一同代入式 (A-23) 得 $\mathrm{d}s_{\text{国}}^{2} / c_{\text{国}}^{2} = -\mathrm{d}t_{\text{国}}^{2} + \mathrm{d}x_{\text{国}}^{2} / c_{\text{国}}^{2}$，去掉下  

> [!NOTE] 🖼️ Figure 描述  
> 本图标注为“3 章题 2 解用图”，但附于附录 A 中，可能为排版错位。几何布局如下：  
> - 底部水平线段，左端点 $b$，右端点 $a$，$a$ 附近标记点 $m$  
> - 从 $b$ 向上延伸：垂直线至 $B$，斜线至 $B'$（$B'$ 位于 $B$ 右侧，更近中心）  
> - 从 $a$ 向上延伸：垂直线至 $A$，斜线至 $A'$（$A'$ 位于 $A$ 左侧，更近中心）  
> - 中央区域：$M$（左）、$M'$（右），$M$ 位于 $b$ 右上方，$M'$ 位于 $a$ 左上方，$M$ 与 $M'$ 间有垂直线段  
> - 附加点：$p$（$M$ 下方偏左）、$q$（$M'$ 下方偏右）  
> - 实线连接：$b \to p$、$p \to q$、$q \to a$、$b \to a$（底部）、$b \to M$、$M \to a$、$b \to B$、$a \to A$、$b \to B'$、$a \to A'$  
> - 所有节点仅字母标注（无填充），线型均为无箭头实线  

<CTX>
{ "summary": "本页详细阐述几何单位制向国际单位制的转换方法，通过洛伦兹变换、闵氏线元和史瓦西线元三个实例演示量纲分析应用，强调单位制转换中下标区分与量纲一致性的关键作用", "keywords": ["几何单位制", "国际单位制转换", "量纲分析", "洛伦兹变换", "史瓦西线元"] }
</CTX>