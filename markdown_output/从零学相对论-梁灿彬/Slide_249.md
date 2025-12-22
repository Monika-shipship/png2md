# Slide 249

标便得闵氏线元的国际单位制形式：  
$$ \mathrm{d}s^2 = -c^2 \mathrm{d}t^2 + \mathrm{d}x^2 $$  
[解毕]  

例 3 已知 2 维史瓦西线元的几何单位制形式为  
$$ \mathrm{d}s^2 = -\left(1 - \frac{2M}{r}\right) \mathrm{d}t^2 + \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r^2, $$  
求其国际单位制形式。  

解 把上式明确写成  
$$ \mathrm{d}s^2_{\text{几}} = -\left(1 - \frac{2M_{\text{几}}}{r_{\text{几}}}\right) \mathrm{d}t^2_{\text{几}} + \left(1 - \frac{2M_{\text{几}}}{r_{\text{几}}}\right)^{-1} \mathrm{d}r^2_{\text{几}}. \tag{A-25} $$  
关键是要将 $ M_{\text{几}} / r_{\text{几}} $ 用 $ M_{\text{国}} / r_{\text{国}} $ 表出。由式 (A-19) 知 $ r_{\text{几}} = r_{\text{国}} / c_{\text{国}} $，而  
$$ \frac{M_{\text{几}}}{M_{\text{国}}} = \frac{\hat{M}_{\text{国}}}{\hat{M}_{\text{几}}} = \dim M = (\dim T) (\dim V)^3 (\dim G)^{-1} = \frac{G_{\text{国}}}{c_{\text{国}}^3}, \tag{A-26} $$  
[其中第三步用到式 (A-13)，第四步用到式 (A-20) 及式 (A-15)。] 故  
$$ M_{\text{几}} = \left( \frac{G_{\text{国}}}{c_{\text{国}}^3} \right) M_{\text{国}}. \tag{A-27} $$  
上式与 $ r_{\text{几}} = r_{\text{国}} / c_{\text{国}} $ 结合给出  
$$ \frac{M_{\text{几}}}{r_{\text{几}}} = \frac{ \left( G_{\text{国}} / c_{\text{国}}^3 \right) M_{\text{国}} }{ r_{\text{国}} / c_{\text{国}} } = \frac{G_{\text{国}}}{c_{\text{国}}^2} \frac{M_{\text{国}}}{r_{\text{国}}}. \tag{A-28} $$  
去掉下标并仿照例 2 的做法，便得史瓦西线元的国际单位制形式：  
$$ \mathrm{d}s^2 = -\left(1 - \frac{2GM}{c^2 r}\right) (c \mathrm{d}t)^2 + \left(1 - \frac{2GM}{c^2 r}\right)^{-1} \mathrm{d}r^2. $$  
[解毕]  

> [!NOTE] 🖼️ Figure 描述  
> 本页无原始插图。提供的 `Figure Analysis` 实际属于后页习题答案（第 3 章题 2），内容为几何示意图：底部水平线段，左端点 b、右端点 a；b 和 a 间近 a 处有 m 点。从 b 延伸垂直线至 B、斜线至 B'（B' 在 B 右侧）；从 a 延伸垂直线至 A、斜线至 A'（A' 在 A 左侧）。图中央 M（左）与 M'（右）由垂直线连接；M 下方偏左有 p 点，M' 下方偏右有 q 点。连线包括：b→p、p→q、q→a、b→a（水平）、b→M、M→a、b→B、a→A、b→B'、a→A'；所有节点为无填充字母标记，线型均为实线。

<CTX>
{ "summary": "本页完成几何单位制向国际单位制的转换示例：先总结例2的闵氏线元转换结果，再通过例3详细演示史瓦西线元的转换过程，核心是利用量纲关系 $ M_{\\text{几}}/r_{\\text{几}} = (G_{\\text{国}}/c_{\\text{国}}^2) \\cdot (M_{\\text{国}}/r_{\\text{国}}) $ 推导国际单位制公式。", "keywords": ["几何单位制", "国际单位制转换", "史瓦西线元", "量纲分析", "闵氏线元"] }
</CTX>