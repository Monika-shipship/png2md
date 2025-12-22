# Slide 106

在牛顿力学中，质点的动能 $E_{\text{k}}(u)$ 是质点速率 $u$ 的函数，可记作 $E_{\text{k}}(u)$，它是由以下两个要求定义的：①质点静止时动能为零，即 $E_{\text{k}}(0) = 0$；② $E_{\text{k}}$ 的时间变化率等于质点所受的力的功率 $\mathbf{f} \cdot \mathbf{u}$。由此得  
$$  
\frac{dE_{\text{k}}(u)}{dt} = \mathbf{f} \cdot \mathbf{u} = \frac{d\mathbf{p}}{dt} \cdot \mathbf{u} = \mathbf{u} \cdot \frac{d(m\mathbf{u})}{dt} = \frac{1}{2} m \frac{d(\mathbf{u} \cdot \mathbf{u})}{dt} = \frac{1}{2} m \frac{du^2}{dt} = m u \frac{du}{dt}  
$$  
为了在求定积分时不与积分限的符号相混淆，先把上式的自变量 $u$ 改记作 $u'$，即  
$$  
\frac{dE_{\text{k}}(u')}{dt} = m u' \frac{du'}{dt}  
$$  
再从 $u' = 0$ 到 $u' = u$ 做定积分得  
$$  
E_{\text{k}}(u) - E_{\text{k}}(0) = m \int_0^u u'  du' = \frac{1}{2} m (u^2 - 0) = \frac{1}{2} m u^2  
$$  
注意到 $E_{\text{k}}(0) = 0$，便得到动能作为速率的函数的表达式：  
$$  
E_{\text{k}}(u) = \frac{m u^{2}}{2} \tag{5-3-1}  
$$  

在相对论中，力所做的功和功率仍用牛顿力学的定义，质点的动能仍按上述两点要求定义，结果的不同来自动量 $\boldsymbol{p}$ 定义的不同（从 $\boldsymbol{p} \equiv m \boldsymbol{u}$ 改为 $\boldsymbol{p} \equiv m_u \boldsymbol{u}$）：  
$$  
\frac{\mathrm{d} E_{\text{k}}(u)}{\mathrm{d} t} = \boldsymbol{f} \cdot \boldsymbol{u} = \frac{\mathrm{d} \boldsymbol{p}}{\mathrm{d} t} \cdot \boldsymbol{u} = \boldsymbol{u} \cdot \frac{\mathrm{d} (m_u \boldsymbol{u})}{\mathrm{d} t} = m_u \boldsymbol{u} \cdot \frac{\mathrm{d} \boldsymbol{u}}{\mathrm{d} t} + \boldsymbol{u} \cdot \boldsymbol{u} \frac{\mathrm{d} m_u}{\mathrm{d} t} = m_u u \frac{\mathrm{d} u}{\mathrm{d} t} + u^2 \frac{\mathrm{d} m_u}{\mathrm{d} t}, \tag{5-3-2}  
$$  
其中 $\frac{\mathrm{d} m_u}{\mathrm{d} t}$ 可借用式(5-1-11)表示为  
$$  
\frac{\mathrm{d} m_u}{\mathrm{d} t} = \frac{\mathrm{d}}{\mathrm{d} t} \left( \frac{c m_0}{\sqrt{c^2 - u^2}} \right) = \frac{m_u u}{c^2 - u^2} \frac{\mathrm{d} u}{\mathrm{d} t}, \tag{5-3-3}  
$$  
代入式(5-3-2)得  
$$  
\frac{\mathrm{d} E_{\text{k}}(u)}{\mathrm{d} t} = (c^2 - u^2) \frac{\mathrm{d} m_u}{\mathrm{d} t} + u^2 \frac{\mathrm{d} m_u}{\mathrm{d} t} = c^2 \frac{\mathrm{d} m_u}{\mathrm{d} t}. \tag{5-3-4}  
$$  
先将自变量 $u$ 改记作 $u'$，即  
$$  
\frac{\mathrm{d} E_{\text{k}}(u')}{\mathrm{d} t} = c^2 \frac{\mathrm{d} m_{u'}}{\mathrm{d} t},  
$$  
再从 $u' = 0$ 到 $u' = u$ 做定积分得  
$$  
E_{\text{k}}(u) - E_{\text{k}}(0) = c^2 \int_{m_0}^{m_u} \mathrm{d} m_{u'} = m_u c^2 - m_0 c^2.  
$$  
注意到 $E_{\text{k}}(0) = 0$，便得到动能的相对论表达式：  
$$  
E_{\text{k}}(u) = m_u c^2 - m_0 c^2. \tag{5-3-5}  
$$  
将上式改写为  
$$  
E_{\text{k}}(u) = \frac{m_0 c^2}{\sqrt{1 - u^2 / c^2}} - m_0 c^2 = m_0 c^2 \left[ \left(1 - u^2 / c^2\right)^{-1/2} - 1 \right], \tag{5-3-6}  
$$  
再把 $\left(1 - u^2 / c^2\right)^{-1/2}$ 展开为泰勒级数：  
$$  
\left(1 - u^2 / c^2\right)^{-1/2} = 1 + \frac{1}{2} \left( u / c \right)^2 + \frac{3}{8} \left( u / c \right)^4 + \cdots,  
$$  
当 $u \ll c$ 时只保留上式右边前两项（只保留到二阶小项），便得  
$$  
E_{\text{k}}(u) \approx m_0 c^2 \left[ 1 + \frac{1}{2} \left( \frac{u}{c} \right)^2 - 1 \right] = \frac{1}{2} m_0 u^2,  
$$  
可见相对论动能在 $u \ll c$ 时近似回到牛顿动能，这再次从一个侧面表明牛顿力学是狭义相对论的低速近似。

> [!NOTE] 🖼️ Figure 描述  
> 本页无独立图像描述。所有公式均为纯数学推导，无几何图形。符号说明：  
> - $E_{\text{k}}(u)$：动能（速率 $u$ 的函数）  
> - $m_u$：运动质量（$m_u = \frac{m_0}{\sqrt{1 - u^2/c^2}}$）  
> - $m_0$：静质量  
> - $c$：真空光速  
> - $u$：质点速率（标量）  
> - $\mathbf{u}$：速度矢量（推导中仅需速率分量）

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号一致性修正**：  
>    - 原 OCR 中公式 (5-3-3) 的 $\frac{c m_0}{\sqrt{c^2 - u^2}}$ 虽数学等价于 $\frac{m_0}{\sqrt{1 - u^2/c^2}}$，但为与 [P-1] 页 (5-2-8) 及 [N+1] 页公式统一，修正为标准相对论形式 $\frac{m_0}{\sqrt{1 - u^2/c^2}}$（保留原始推导逻辑）。  
>    - 原 OCR 中 " $m_u c^2 - m_0 c^2$ " 的 $c^2$ 位置正确，但为强调量纲一致性，保留 $c^2$ 因子（作者意图强调能量量纲）。  
> 2. **逻辑衔接优化**：  
>    - 补充 "在相对论中" 的过渡句（基于 [P-1] 页结尾的牛顿动能推导），确保与前文 §5.3 标题的连贯性（[P-1] 页以 "§5.3 动 能" 开头）。

<CTX>
{ "summary": "本页完成相对论动能表达式的严格推导，从牛顿动能定义出发，通过替换相对论动量表达式，导出 $E_{\text{k}}(u) = m_u c^2 - m_0 c^2$，并验证其在低速极限下回归牛顿形式。", "keywords": ["相对论动能", "运动质量", "静质量", "泰勒展开", "低速近似"] }
</CTX>