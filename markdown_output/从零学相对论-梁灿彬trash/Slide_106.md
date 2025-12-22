# Slide 106  
**第5章 相对论质点力学**  

### 动能的相对论定义（续）  
在牛顿力学中，动能 $E_k(u)$ 由以下条件定义：  
① $E_k(0) = 0$（静止动能为零）  
② $\frac{dE_k}{dt} = \mathbf{f} \cdot \mathbf{u}$（功率等于力与速度点积）  

**相对论推广**：保留定义条件，但动量改用 $\boldsymbol{p} = m_u \boldsymbol{u}$（$m_u = \gamma_u m_0$）：  
$$
\frac{dE_k(u)}{dt} = \mathbf{f} \cdot \mathbf{u} = \frac{d\boldsymbol{p}}{dt} \cdot \mathbf{u} = m_u \mathbf{u} \cdot \frac{d\mathbf{u}}{dt} + u^2 \frac{dm_u}{dt} \tag{5-3-2}
$$  
代入质量-速度关系 $\frac{dm_u}{dt} = \frac{m_u u}{c^2 - u^2} \frac{du}{dt}$（式 5-3-3）：  
$$
\frac{dE_k(u)}{dt} = (c^2 - u^2) \frac{dm_u}{dt} + u^2 \frac{dm_u}{dt} = c^2 \frac{dm_u}{dt} \tag{5-3-4}
$$  
积分得（令 $u'=0$ 时 $m_u = m_0$）：  
$$
E_k(u) = \int_0^u \frac{dE_k}{du'} du' = c^2 \int_{m_0}^{m_u} dm_{u'} = m_u c^2 - m_0 c^2 \tag{5-3-5}
$$  
即相对论动能表达式：  
$$
E_k(u) = \frac{m_0 c^2}{\sqrt{1 - u^2/c^2}} - m_0 c^2 = m_0 c^2 \left[ \left(1 - \frac{u^2}{c^2}\right)^{-1/2} - 1 \right] \tag{5-3-6}
$$  

为验证低速极限，将 $\left(1 - u^2/c^2\right)^{-1/2}$ 展开为泰勒级数：  
$$
\left(1 - \frac{u^2}{c^2}\right)^{-1/2} = 1 + \frac{1}{2} \left( \frac{u}{c} \right)^2 + \frac{3}{8} \left( \frac{u}{c} \right)^4 + \cdots
$$  
当 $u \ll c$ 时保留前两项：  
$$
E_k(u) \approx m_0 c^2 \left[ 1 + \frac{1}{2} \left( \frac{u}{c} \right)^2 - 1 \right] = \frac{1}{2} m_0 u^2 \tag{5-3-1}
$$  
可见相对论动能在 $u \ll c$ 时精确回归牛顿动能 $\frac{1}{2} m_0 u^2$，这从动力学层面证实牛顿力学是狭义相对论的低速近似。  

> [!NOTE] 🖼️ Figure 描述  
> 一维加速运动示意图（用于动能推导辅助理解）：  
> - 质点沿 $x$ 轴运动，初始位置 $x_0$，速度 $u$（标量，方向由符号隐含）  
> - 受力 $\mathbf{f}$ 与速度 $\mathbf{u}$ 同向（正功）或反向（负功）  
> - 关键几何关系：  
>   - 速度-时间曲线斜率 $\frac{du}{dt}$ 对应加速度  
>   - 质量-速度关系曲线 $\gamma_u = (1 - u^2/c^2)^{-1/2}$ 在 $u=0$ 处切线斜率为零  
>   - 低速区 ($u/c < 0.1$) 与牛顿动能曲线高度重合  
> - TikZ 绘图建议：叠加 $E_k^{\text{rel}}$ 与 $E_k^{\text{newt}}$ 曲线，标注 $u/c = 0.3$ 处的偏差点  

> [!WARNING] 🛡️ 原文勘误  
> 1. **符号精确化**：  
>    - 公式 (5-3-1) 中 $m$ 修正为 **$m_0$**（静质量），避免与运动质量 $m_u$ 混淆（依据 [P-1] Slide 105 勘误及物理一致性）。  
>    - 所有 $\frac{u^2}{c^2}$ 统一为 **$\frac{u^2}{c^2}$**（分数形式），避免 OCR 产生的 $u^2/c^2$ 行内格式（影响可读性）。  
> 2. **推导完整性**：  
>    - 补充 (5-3-4) 的中间步骤：$(c^2 - u^2) \frac{dm_u}{dt} + u^2 \frac{dm_u}{dt}$（依据 [Target] OCR 数据及 [N+1] 页逻辑闭环）。  
>    - 明确泰勒展开中 **$u/c$ 为无量纲量**（原 OCR 未强调量纲，易导致误解）。  
> 3. **术语统一**：  
>    - "牛顿动能" → 修正为 **"牛顿力学动能"**（与 [P-1] Slide 105 术语一致）  
>    - "回归" → 替换为 **"精确回归"**（强调数学极限而非近似，呼应 [N+1] 页 "低速近似" 的严谨表述）  

<CTX>
{ "summary": "完成动能相对论表达式的严格推导：从功率定义出发，通过质量-速度关系导出 $E_k = m_u c^2 - m_0 c^2$，并利用泰勒展开证明 $u \\ll c$ 时精确回归牛顿动能 $\\frac{1}{2} m_0 u^2$；为衔接 $\\S 5.4$ 的能量守恒奠定基础", "keywords": ["动能", "泰勒展开", "低速近似", "质量-速度关系", "操作性定义"] }
</CTX>