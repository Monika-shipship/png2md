# Slide 52

t=0 时相遇；② $\{x',y',z'\}$ 相对于 $\{x,y,z\}$ 系以任意速度 $\mathbf{v} = v_1 \mathbf{e}_1 + v_2 \mathbf{e}_2 + v_3 \mathbf{e}_3$ 做匀速平动，其中 $\mathbf{e}_1, \mathbf{e}_2, \mathbf{e}_3$ 是沿 $K$ 系 $x,y,z$ 轴正向的单位矢；③ 两系空间坐标轴对应同向。这两个系的坐标变换由如下的矩阵等式表出 [证明见梁灿彬, 周彬 (2009) 中册小节 G.9.1]：

$$
\begin{bmatrix}
t' \\
x' \\
y' \\
z'
\end{bmatrix}
=
\begin{bmatrix}
\gamma & -\gamma v_1 & -\gamma v_2 & -\gamma v_3 \\
-\gamma v_1 & 1 + \frac{(\gamma - 1)v_1^2}{v^2} & \frac{(\gamma - 1)v_1 v_2}{v^2} & \frac{(\gamma - 1)v_1 v_3}{v^2} \\
-\gamma v_2 & \frac{(\gamma - 1)v_2 v_1}{v^2} & 1 + \frac{(\gamma - 1)v_2^2}{v^2} & \frac{(\gamma - 1)v_2 v_3}{v^2} \\
-\gamma v_3 & \frac{(\gamma - 1)v_3 v_1}{v^2} & \frac{(\gamma - 1)v_3 v_2}{v^2} & 1 + \frac{(\gamma - 1)v_3^2}{v^2}
\end{bmatrix}
\begin{bmatrix}
t \\
x \\
y \\
z
\end{bmatrix}
\tag{3-6-9}
$$

其中
$$
v \equiv \sqrt{v_1^2 + v_2^2 + v_3^2} < 1, \quad \gamma \equiv 1 / \sqrt{1 - v^2}
\tag{3-6-10}
$$

式 (3-6-9) 称为最一般的洛伦兹变换。为了证明定理 3-2，必须且只需证明式 (3-6-9) 的变换不会导致 $\Delta t$ 变号。

**定理 3-2 的证明** 由式 (3-6-9) 得 $t' = \gamma (t - v_1 x - v_2 y - v_3 z)$，故
$$
\Delta t' = \gamma (\Delta t - v_1 \Delta x - v_2 \Delta y - v_3 \Delta z)
\tag{3-6-11}
$$

注意到 $\mathbf{v} = v_1 \mathbf{e}_1 + v_2 \mathbf{e}_2 + v_3 \mathbf{e}_3$ 是 3 维矢量，再定义 3 维矢量 $\Delta \mathbf{X} \equiv \mathbf{e}_1 \Delta x + \mathbf{e}_2 \Delta y + \mathbf{e}_3 \Delta z$，就可把式 (3-6-11) 表为
$$
\Delta t' = \gamma (\Delta t - \mathbf{v} \cdot \Delta \mathbf{X})
\tag{3-6-11'}
$$

以 $\alpha$ 代表矢量 $\mathbf{v}$ 与 $\Delta \mathbf{X}$ 的夹角，$|\mathbf{v}|$ 和 $|\Delta \mathbf{X}|$ 代表两矢量的长度 [其中 $|\mathbf{v}|$ 即式 (3-6-10) 的 $v$，故 $0 < v < 1$]，则
$$
\mathbf{v} \cdot \Delta \mathbf{X} = |\mathbf{v}| |\Delta \mathbf{X}| \cos \alpha \leq |\mathbf{v}| |\Delta \mathbf{X}| < |\Delta \mathbf{X}|
\tag{3-6-12}
$$

由式 (3-6-7) 又知 $I_{12} \leq 0$ 保证 $|\Delta \mathbf{X}| \leq \Delta t$，代入式 (3-6-12) 给出 $\mathbf{v} \cdot \Delta \mathbf{X} < \Delta t$，再代入式 (3-6-11') 便知 $\Delta t' > 0$。
[证毕]

[选读 3-3]

正文把式 (3-6-9) 称为“最一般的洛伦兹变换”其实不够准确，本选读对此加以准确化。感到不好理解的读者不读也罢。

洛伦兹变换包含两种类型，仍以地面系和火车系为例说明。设 $K \equiv \{t,x,y,z\}$ 是地面参考系内的一个惯性坐标系，让 3 个空间坐标轴 (统一地) 做一个空间转动就得到一个新坐标系 $\hat{K} \equiv \{t, \hat{x}, \hat{y}, \hat{z}\}$，同一事件 $p$ 既可表为 $(t,x,y,z)$ 又可表

> [!NOTE] 🖼️ Figure 描述  
> 当前页未包含新插图。所有图形元素（图3-20至图3-22）已在前页完整描述：  
> - 图3-20：展示$v>0$和$v<0$时改时序的洛伦兹变换时空图，含两组坐标系$\{t,x\}$与$\{t',x'\}$及点$p_1,p_2,q,q'$的位置关系  
> - 图3-21：事件$p_1,p_2$的类时联系示意图，含光锥结构及$\Delta t,\Delta x$标注  
> - 图3-22：中值定理证明曲线类空性的示意图，含曲线$L$、切线斜率及$\Delta t/\Delta x < 1$的几何表示

> [!WARNING] 🛡️ 原文勘误  
> 1. OCR断句修正：前页[P-1]末句"由以下三点表征：① 两系空间坐标原点在 t' ="与本页首句"t=0 时相遇；②"应合并为"① 两系空间坐标原点在 $t'=t=0$ 时相遇"（补全$t'=$部分，添加$t=$以明确时空重合条件）  
> 2. 符号统一：原文"矢量 $\mathbf{v}$ 与 $\Delta \mathbf{X}$ 的夹角"中$\Delta \mathbf{X}$在[P-1]定义为$\Delta \mathbf{X} \equiv \mathbf{e}_1 \Delta x + \mathbf{e}_2 \Delta y + \mathbf{e}_3 \Delta z$，此处保持一致使用粗体矢量符号（非斜体$X$）  
> 3. 逻辑衔接：定理3-2证明中"由式(3-6-7)又知"的引用需明确——式(3-6-7)定义$I_{12} \equiv -\Delta t^2 + \Delta x^2 + \Delta y^2 + \Delta z^2$，故$I_{12} \leq 0$等价于$|\Delta \mathbf{X}| \leq \Delta t$（$\Delta t > 0$前提下）

<CTX>
{ "summary": "本页完成定理3-2的证明：在$I_{12} \\leq 0$条件下，最一般的洛伦兹变换(3-6-9)保证$\\Delta t$不变号，从而维护因果关系。通过矢量点积分析证明$\\Delta t' > 0$，并补充选读说明洛伦兹变换的分类", "keywords": ["洛伦兹变换", "因果关系", "时序不变性", "矢量点积", "闵氏时空"] }
</CTX>