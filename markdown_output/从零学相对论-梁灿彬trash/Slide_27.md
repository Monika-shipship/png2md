# Slide 27  
**第2章 学一点点几何**  

### §2.2 闵氏几何  
承接 Slide 26 对闵氏空间（Minkowski space）的定义及 Figure 2-2 三类曲线的几何特征，本节系统阐释闵氏几何的核心性质。为统一符号体系，**今后用 $\mathrm{d}s^2$ 代表线元**（但元段长仍记作 $\mathrm{d}l$），故欧氏线元 $\mathrm{d}l^2 = \mathrm{d}x^2 + \mathrm{d}y^2$ 改记为 $\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2$。  

以上讨论虽以 2 维为例，但可自然推广至高维空间。3 维欧氏线元在直角坐标系中的表达式为：  
$$
\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 \quad (2\text{-}1\text{-}11)
$$  
若改用球坐标系 $\{r,\theta,\varphi\}$（坐标变换关系为 $x = r\sin\theta\cos\varphi$, $y = r\sin\theta\sin\varphi$, $z = r\cos\theta$），经微分运算得线元表达式：  
$$
\mathrm{d}s^2 = \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2) \quad (2\text{-}1\text{-}13)
$$  
需强调：**坐标变换仅改变线元表达式形式，而非线元本身**，故有连等式：  
$$
\mathrm{d}s^2 = \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 = \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2)
$$  
欧氏线元仅在直角坐标系中取最简形式 $\mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2$。类似地，补入第 4 维直角坐标 $w$，可得 4 维欧氏线元：  
$$
\mathrm{d}s^2 = \mathrm{d}w^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 \quad (2\text{-}1\text{-}14)
$$  
其与 4 维闵氏线元的严格对应关系为：  
$$
\mathrm{d}s^2 = -\mathrm{d}t^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2 \quad (2\text{-}1\text{-}15)
$$  
**关键差异**：$\mathrm{d}t^2$ 项的负号导致几何结构根本不同。当在闵氏时空中选用非惯性坐标系时（如 4 维球坐标系 $\{t,r,\theta,\varphi\}$），线元表达式变为：  
$$
\mathrm{d}s^2 = -\mathrm{d}t^2 + \mathrm{d}r^2 + r^2(\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2) \quad (2\text{-}1\text{-}16)
$$  
**核心结论**：闵氏线元仅在惯性坐标系中取最简形式 $-\mathrm{d}t^2 + \mathrm{d}x^2 + \mathrm{d}y^2 + \mathrm{d}z^2$。  

回归 2 维情况（$\mathrm{d}s^2 \equiv -\mathrm{d}t^2 + \mathrm{d}x^2$），$\mathrm{d}t^2$ 项的负号导致 $\mathrm{d}s^2$ 正负不定，引发几何本质变化：  
- **类空曲线**（如 Figure 2-2 中 $L_1$）：元段满足 $\mathrm{d}s^2 > 0$，元段长定义为 $\mathrm{d}l \equiv \sqrt{\mathrm{d}s^2}$，曲线段 $a_1b_1$ 长度为 $l_{a_1b_1} = \int_{a_1}^{b_1} \sqrt{\mathrm{d}s^2}$。  
- **类时曲线**（如 $L_2$）：元段满足 $\mathrm{d}s^2 < 0$。此处需澄清概念：$\mathrm{d}s^2$ 仅为符号 $\mathrm{d}s^2$（非实数 $\mathrm{d}s$ 的平方），故定义元段长 $\mathrm{d}l \equiv \sqrt{-\mathrm{d}s^2}$（因 $-\mathrm{d}s^2 > 0$），曲线段 $a_2b_2$ 长度为 $l_{a_2b_2} = \int_{a_2}^{b_2} \sqrt{-\mathrm{d}s^2}$。  
- **类光曲线**（如 $L_3$）：元段满足 $\mathrm{d}s^2 = 0$，元段长定义为零，故任意线段长度均为零——这体现了闵氏几何与欧氏几何的根本区别（欧氏视角下 $L_3$ 有长度，但闵氏度规下长度为零）。  

综上，任意曲线段 $ab$ 的长度可统一表示为：  
$$
l_{ab} = \int_a^b \sqrt{|\mathrm{d}s^2|} \quad (2\text{-}2\text{-}3)
$$  
此式兼容三类曲线：  
- 类空曲线：$\mathrm{d}s^2 > 0$，退化为 $l_{ab} = \int_a^b \sqrt{\mathrm{d}s^2}$；  
- 类时曲线：$\mathrm{d}s^2 < 0$，退化为 $l_{ab} = \int_a^b \sqrt{-\mathrm{d}s^2}$；  
- 类光曲线：$\mathrm{d}s^2 = 0$，直接得 $l_{ab} = 0$。  

> [!NOTE] 🖼️ Figure 2-2 描述  
> **闵氏空间的三类曲线（2维时空）**  
> - **坐标系**：水平轴为 $x$（空间轴，箭头向右），垂直轴为 $t$（时间轴，箭头向上；国际单位制中应为 $ct$ 轴）；  
> - **曲线 $L_1$（类空）**：平缓上凸曲线（开口向下），位于右下区域；元段 $\mathrm{d}s^2 > 0$；标注点 $a_1$（左）、$b_1$（右）；  
> - **曲线 $L_2$（类时）**：陡峭上凸曲线（开口向下），位于左上区域；元段 $\mathrm{d}s^2 < 0$；标注点 $a_2$（左下）、$b_2$（右上）；  
> - **曲线 $L_3$（类光）**：过原点的直线（斜率 $=1$），位于 $L_1$ 与 $L_2$ 之间；元段 $\mathrm{d}s^2 = 0$；  
> - **关键几何特征**：  
>   - $L_3$ 与 $L_1$ 在 $a_1$ 附近相交，与 $L_2$ 在 $b_2$ 附近相交；  
>   - 所有曲线从第三象限延伸至第一象限；  
>   - 坐标轴与曲线为黑色实线，标注点为实心黑点。  
> *注：TikZ 绘图需严格保持坐标轴比例（1:1）及曲线相对位置（$L_1$ 最平缓、$L_2$ 最陡峭、$L_3$ 为 45° 直线）。*

> [!WARNING] 🛡️ 原文勘误  
> - **符号修正**：原文 "$ds^2$" 统一规范为 "$\mathrm{d}s^2$"（微分符号需用正体），"$dl$" 修正为 "$\mathrm{d}l$"；  
> - **逻辑衔接**：原文 "space)。" 补全为 "闵氏空间（Minkowski space）。" 以承接 Slide 26 结论；  
> - **公式编号**：(2-1-12) 为坐标变换关系式，(2-1-13) 为对应线元表达式（原文缺失 (2-1-12) 编号，已按逻辑补充）。

<CTX>
{ 
  "summary": "本页系统阐释闵氏几何的核心性质：统一线元符号 $\mathrm{d}s^2$，推广至高维欧氏/闵氏线元，重点解析 $\mathrm{d}t^2$ 项负号导致的几何本质差异。基于 Figure 2-2 严格定义三类曲线（类空/类时/类光）的元段长与积分长度公式，强调闵氏度规下类光曲线长度为零的非欧特性。", 
  "keywords": ["闵氏几何", "线元", "类空曲线", "类时曲线", "类光曲线", "度规", "非欧几何"] 
}
</CTX>