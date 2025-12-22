# Slide 52  
**第3章 相对论的几何表述**  

### §3.6 时序和因果关系（续）  

承接 Slide 51 的定理 3-2，现完成其证明。设惯性系 $K \equiv \{t, x, y, z\}$ 与 $K' \equiv \{t', x', y', z'\}$ 满足：① $t'=t=0$ 时两系空间原点重合；② $\{x', y', z'\}$ 相对于 $\{x, y, z\}$ 系以任意速度 $\mathbf{v} = v_1 \mathbf{e}_1 + v_2 \mathbf{e}_2 + v_3 \mathbf{e}_3$ 做匀速平动（$\mathbf{e}_1, \mathbf{e}_2, \mathbf{e}_3$ 为 $K$ 系坐标轴单位矢）；③ 两系空间坐标轴对应同向。坐标变换由下式给出 [证明见梁灿彬, 周彬 (2009) 中册 §G.9.1]：  

\[
\begin{bmatrix}
t' \\
x' \\
y' \\
z'
\end{bmatrix}
=
\begin{bmatrix}
\gamma & -\gamma v_1 & -\gamma v_2 & -\gamma v_3 \\
-\gamma v_1 & 1 + \dfrac{(\gamma - 1)v_1^2}{v^2} & \dfrac{(\gamma - 1)v_1 v_2}{v^2} & \dfrac{(\gamma - 1)v_1 v_3}{v^2} \\
-\gamma v_2 & \dfrac{(\gamma - 1)v_2 v_1}{v^2} & 1 + \dfrac{(\gamma - 1)v_2^2}{v^2} & \dfrac{(\gamma - 1)v_2 v_3}{v^2} \\
-\gamma v_3 & \dfrac{(\gamma - 1)v_3 v_1}{v^2} & \dfrac{(\gamma - 1)v_3 v_2}{v^2} & 1 + \dfrac{(\gamma - 1)v_3^2}{v^2}
\end{bmatrix}
\begin{bmatrix}
t \\
x \\
y \\
z
\end{bmatrix}
\tag{3-6-9}
\]  

其中  
\[
v \equiv \sqrt{v_1^2 + v_2^2 + v_3^2} < 1, \quad \gamma \equiv 1 / \sqrt{1 - v^2}
\tag{3-6-10}
\]  

式 (3-6-9) 称为**最一般的伪转动**（详见选读 3-3）。为证明定理 3-2，需证当 $I_{12} \leq 0$ 且 $\Delta t > 0$ 时，$\Delta t'$ 恒正：  

**定理 3-2 的证明**  
由式 (3-6-9) 得 $t' = \gamma (t - v_1 x - v_2 y - v_3 z)$，故  
\[
\Delta t' = \gamma (\Delta t - v_1 \Delta x - v_2 \Delta y - v_3 \Delta z)
\tag{3-6-11}
\]  

引入 3 维矢量 $\mathbf{v} = v_1 \mathbf{e}_1 + v_2 \mathbf{e}_2 + v_3 \mathbf{e}_3$ 和 $\Delta \mathbf{X} \equiv \mathbf{e}_1 \Delta x + \mathbf{e}_2 \Delta y + \mathbf{e}_3 \Delta z$，式 (3-6-11) 可写为  
\[
\Delta t' = \gamma (\Delta t - \mathbf{v} \cdot \Delta \mathbf{X})
\tag{3-6-11'}
\]  

令 $\alpha$ 为 $\mathbf{v}$ 与 $\Delta \mathbf{X}$ 的夹角，$|\mathbf{v}| = v$（由式 (3-6-10)），则  
\[
\mathbf{v} \cdot \Delta \mathbf{X} = |\mathbf{v}| |\Delta \mathbf{X}| \cos \alpha \leq |\mathbf{v}| |\Delta \mathbf{X}| < |\Delta \mathbf{X}|
\tag{3-6-12}
\]  

由式 (3-6-7) 知 $I_{12} \leq 0$ 保证 $|\Delta \mathbf{X}| \leq \Delta t$，代入式 (3-6-12) 得 $\mathbf{v} \cdot \Delta \mathbf{X} < \Delta t$。再代入式 (3-6-11')，因 $\gamma > 0$，故 $\Delta t' > 0$。  
[证毕]  

> [!NOTE] 🖼️ Figure 3-23 闵氏时空中类时/类光间隔的几何约束  
> **布局与元素**：  
> - **坐标系**：  
>   - 竖直 $t$ 轴（1.0pt 黑色实线，向上箭头）、水平 $\Delta x$ 轴（1.0pt 黑色实线，向右箭头），原点 $O$；  
>   - 未来光锥面：双曲线 $t = \pm \sqrt{(\Delta x)^2 + (\Delta y)^2 + (\Delta z)^2}$（0.7pt 灰色虚线，仅展示 $t>0$ 部分）；  
> - **关键区域**：  
>   - 类时区域：光锥内 $I_{12} < 0$（浅蓝色填充，$|\Delta \mathbf{X}| < \Delta t$）；  
>   - 类光边界：光锥面 $I_{12} = 0$（0.5pt 深灰色实线）；  
> - **矢量表示**：  
>   - $\Delta \mathbf{X}$：从原点指向 $(\Delta x, 0, 0)$ 的箭头（1.2pt 蓝色实线，长度 $|\Delta \mathbf{X}|$）；  
>   - $\mathbf{v}$：单位圆内箭头（1.0pt 橙色实线，长度 $v < 1$）；  
>   - $\mathbf{v} \cdot \Delta \mathbf{X}$：投影标量（虚线垂足至 $\Delta x$ 轴，0.5pt 红色虚线）；  
> - **量度标注**：  
>   - $\Delta t$：$t$ 轴上 $0$ 至 $t_2$ 的线段（8pt 无衬线字体，标注 "$\Delta t$"）；  
>   - $|\Delta \mathbf{X}|$：$\Delta x$ 轴上 $0$ 至 $x_2$ 的线段（8pt 蓝色字体，标注 "$|\Delta \mathbf{X}|$"）；  
>   - 约束关系："$|\Delta \mathbf{X}| \leq \Delta t$"（10pt 深蓝色字体，置于类时区域）；  
> - **标题**：居中于图下方 "图 3-23 类时/类光间隔中 $|\Delta \mathbf{X}| \leq \Delta t$ 的几何意义"（12pt 加粗）。  

> [!WARNING] 🛡️ 原文勘误  
> 1. OCR 原文 "式 (3-6-9) 称为最一般的洛伦兹变换" 表述不准确：根据选读 3-3，应明确为 **"最一般的伪转动"**（转动也属于洛伦兹变换，但伪转动涉及参考系变换）。  
> 2. 证明中 "$I_{12} \leq 0$ 保证 $|\Delta \mathbf{X}| \leq \Delta t$" 需补充 **$\Delta t > 0$ 的前提**（定理 3-2 已限定 $\Delta t > 0$，但 OCR 未显式强调）。  
> 3. 公式 (3-6-12) 的严格性：当 $\cos \alpha = 1$ 且 $v \to 1$ 时 $\mathbf{v} \cdot \Delta \mathbf{X} \to |\Delta \mathbf{X}|$，但 $v < 1$ 保证严格不等式 $\mathbf{v} \cdot \Delta \mathbf{X} < |\Delta \mathbf{X}|$。  

<CTX>
{
  "summary": "完成定理3-2证明：利用最一般伪转动的矩阵形式，通过矢量点积与夹角分析，验证$I_{12} \\leq 0$时$\\Delta t' > 0$的因果一致性；澄清'最一般洛伦兹变换'的术语误用，引入选读3-3区分转动与伪转动",
  "keywords": ["定理3-2证明", "最一般伪转动", "矢量点积", "类时间隔", "因果一致性", "术语勘误"]
}
</CTX>