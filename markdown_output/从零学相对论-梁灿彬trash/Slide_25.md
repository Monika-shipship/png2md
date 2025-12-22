 
# Slide 25  
**第2章 学一点点几何**  

### §2.1 线元与几何：以不变量统摄坐标变换  
承接 Slide 24 习题对几何单位制（$c=1$）的实践应用（"凸显时空几何本质"），本章正式引入微分几何语言重构相对论框架。物理学家面对惯性系间纷繁的坐标变换，采用数学家的"以不变应万变"策略——**抓住坐标变换下的不变量**（invariant，亦称绝对量）。欧氏几何为此提供关键范式：  

设 $L$ 是 2 维欧氏空间中的曲线，$\mathrm{d}L$ 为其微元段（见图 2-1），$\mathrm{d}l$ 为元段长度（元段长），则 $\mathrm{d}l^2$ 定义为**线元**（line element）。元段 $\mathrm{d}L$ 一经给定，$\mathrm{d}l^2$ 即与坐标系无关，是绝对不变量。在直角坐标系 $\{x,y\}$ 中，线元表达式为：  
$$
\mathrm{d}l^2 = \mathrm{d}x^2 + \mathrm{d}y^2 \quad (2\text{-}1\text{-}1)
$$  
若改用极坐标系 $\{r,\varphi\}$，同一线元的表达式变为：  
$$
\mathrm{d}l^2 = \mathrm{d}r^2 + r^2 \mathrm{d}\varphi^2 \quad (2\text{-}1\text{-}2)
$$  
二者等价，坐标变换仅改变表达式而非线元本身。特别地，当新坐标系 $\{x',y'\}$ 由 $\{x,y\}$ 绕原点旋转 $\alpha$ 角（见图 2-1）：  
$$
x' = x \cos\alpha + y \sin\alpha, \quad y' = -x \sin\alpha + y \cos\alpha \quad (2\text{-}1\text{-}3)
$$  
可验证线元表达式形式不变：  
$$
\mathrm{d}x^2 + \mathrm{d}y^2 = \mathrm{d}x'^2 + \mathrm{d}y'^2 \quad \Rightarrow \quad \mathrm{d}l^2 = \mathrm{d}x'^2 + \mathrm{d}y'^2 \quad (2\text{-}1\text{-}4, 2\text{-}1\text{-}5)
$$  
**核心结论**：欧氏线元仅在直角坐标变换（旋转+平移）下保持表达式不变。  

相对论中存在严格类比。在几何单位制（$c=1$）下，设 $p_1, p_2$ 为 2 维时空中的相邻事件，在惯性系 $K$ 和 $K'$ 的坐标分别为：  
$$
p_1 = (t_1, x_1) = (t_1', x_1'), \quad p_2 = (t_2, x_2) = (t_2', x_2')
$$  
定义坐标微分：$\mathrm{d}t \equiv t_2 - t_1$，$\mathrm{d}x \equiv x_2 - x_1$（$K'$ 系同理）。由 Slide 23 洛伦兹变换式 (1-3-9)：  
$$
\mathrm{d}t' = \gamma (\mathrm{d}t - v \mathrm{d}x), \quad \mathrm{d}x' = \gamma (\mathrm{d}x - v \mathrm{d}t) \quad (2\text{-}1\text{-}6)
$$  
可证（见 Slide 24 习题 4）：  
$$
-\mathrm{d}t^2 + \mathrm{d}x^2 = -\mathrm{d}t'^2 + \mathrm{d}x'^2 \quad (2\text{-}1\text{-}7)
$$  
定义**时空间隔**（spacetime interval）为：  
$$
\mathrm{d}s^2 \equiv -\mathrm{d}t^2 + \mathrm{d}x^2 \quad \text{(几何单位制)} \quad (2\text{-}1\text{-}8)
$$  
式 (2-1-7) 表明 $\mathrm{d}s^2$ 在洛伦兹变换下形式不变，类比欧氏线元 $\mathrm{d}l^2$。建立对应关系：  
> 时空间隔 $\mathrm{d}s^2$ $\leftrightarrow$ 欧氏线元 $\mathrm{d}l^2$；  
> 惯性坐标 $t,x$ $\leftrightarrow$ 直角坐标 $x,y$。  

但二者存在本质差异：$\mathrm{d}s^2$ 中 $\mathrm{d}t^2$ 项带负号。如同欧氏几何中引入极坐标，可定义新坐标系 $\{\psi, \eta\}$：  
$$
x = \psi \cosh \eta, \quad t = \psi \sinh \eta \quad (\cosh/\sinh \text{ 为双曲函数}) \quad (2\text{-}1\text{-}9)
$$  
此时同一间隔的表达式变为：  
$$
\mathrm{d}s^2 = \mathrm{d}\psi^2 - \psi^2 \mathrm{d}\eta^2 \quad (2\text{-}1\text{-}10)
$$  

> [!NOTE] 🖼️ Figure 2-1 描述  
> **欧氏线元在直角坐标旋转下形式不变**  
> - 坐标系：原直角系 $\{x,y\}$（$x$ 轴水平向右，$y$ 轴垂直向上）；新系 $\{x',y'\}$ 由原系绕原点逆时针旋转 $\alpha$ 角得到（$x'$ 轴与 $x$ 轴夹角 $\alpha$，$y'$ 轴同理）。  
> - 曲线：平滑曲线 $L$ 从第三象限延伸至第一象限，向右上方弯曲；微元段 $\mathrm{d}L$ 位于第一象限，沿切线方向加粗标注。  
> - 几何细节：角度 $\alpha$ 用细实线弧标记于 $x$ 与 $x'$ 轴间；所有坐标轴为实线，箭头为实心三角形；曲线末端标 $L$，微元段标 $\mathrm{d}L$。  
> *（注：此描述支持 TikZ 精准重绘，需保留坐标轴相对位置、旋转角标记及微元段切向特征）*

> [!WARNING] 🛡️ 原文勘误  
> **术语标准化修正**：OCR 原文 "dl²代表dl的平方[简称为线元]" 易引发歧义（线元本质是 $\mathrm{d}l^2$ 而非 $dl$ 的平方操作），参照 [P-1] Slide 24 **几何单位制规范**（"凸显时空几何本质"）及微分几何惯例，统一表述为：  
> - **线元**（line element）严格定义为 $\mathrm{d}s^2$（欧氏/闵氏），即度规张量的二次型；  
> - **元段长**为 $\mathrm{d}l = \sqrt{|\mathrm{d}s^2|}$（欧氏空间 $\mathrm{d}l = \sqrt{\mathrm{d}s^2}$，闵氏空间需分情况）；  
> **符号一致性修复**：OCR "dy^2 + dx^2" 未对齐 LaTeX 排版规范，参照 [P-2] Slide 23 **公式规范**（"消除冗余常数 $c$"），统一调整为 $\mathrm{d}x^2 + \mathrm{d}y^2$ 以符合张量指标惯例。

<CTX>
{
  "summary": "本页开启第2章，通过欧氏几何线元类比建立相对论时空间隔概念。核心论证：坐标变换下不变量的普适性——欧氏线元在直角坐标旋转下形式不变，类比导出几何单位制（c=1）下时空间隔ds² = -dt² + dx²的洛伦兹不变性。图2-1可视化欧氏线元旋转不变性，为后续闵氏几何铺垫。",
  "keywords": [
    "线元",
    "时空间隔",
    "几何单位制",
    "洛伦兹不变性",
    "欧氏几何类比",
    "微分几何基础"
  ]
}
</CTX>