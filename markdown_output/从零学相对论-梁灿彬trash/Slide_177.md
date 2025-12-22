# Slide 177

地球引力场使地球附近的时空弯曲，式(4-3-1)的闵氏线元应被史瓦西线元取代：
$$ ds^2 = -\left(1 - \frac{2M}{r}\right) \mathrm{d}t^2 + \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r^2 + r^2 (\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2), \quad \text{①} \tag{8-3-16} $$
其中 $M$ 是地球质量。上式适用于几何单位制，为便于数值计算，宜改用国际单位制形式：
$$ ds^2 = -\left(1 - \frac{2GM}{c^2 r}\right) c^2 \mathrm{d}t^2 + \left(1 - \frac{2GM}{c^2 r}\right)^{-1} \mathrm{d}r^2 + r^2 (\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2), \tag{8-3-16'} $$
其中 $G$ 和 $c$ 分别是引力常量和真空光速在国际单位制中的数值。仿照牛顿引力势的概念，用下式定义引力势 $\Phi(r)$：
$$ \Phi(r) \equiv -\frac{GM}{r}, \tag{8-3-17} $$
则线元可重写为：
$$ ds^2 = -\left(1 + \frac{2\Phi}{c^2}\right) c^2 \mathrm{d}t^2 + \left(1 + \frac{2\Phi}{c^2}\right)^{-1} \mathrm{d}r^2 + r^2 (\mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2). \tag{8-3-18} $$

先讨论静止于赤道上的钟 $C_0$（相应于飞机速度 $v=0$，仍见图4-21）。因赤道上有 $r=R$、$\mathrm{d}r=0$、$\theta=\pi/2$、$\mathrm{d}\theta=0$ 及 $\mathrm{d}\varphi=\Omega \mathrm{d}t$，故式(8-3-18)用于 $C_0$ 线的任一元段给出：
$$ ds_0^2 = -\left(1 + \frac{2\Phi_0}{c^2}\right) c^2 \mathrm{d}t^2 + R^2 \mathrm{d}\varphi^2 = -\left(1 + \frac{2\Phi_0}{c^2}\right) c^2 \mathrm{d}t^2 + R^2 \Omega^2 \mathrm{d}t^2 = -\left(1 + \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2}\right) c^2 \mathrm{d}t^2, \tag{8-3-19} $$
其中：
$$ \Phi_0 \equiv \Phi(R) = -\frac{GM}{R} \tag{8-3-20} $$
是赤道上的引力势，$u_0 = R\Omega$ 是 $C_0$ 钟（随地球自转）的线速率。于是元段的固有时间为：
$$ \mathrm{d}\tau_0 = \sqrt{\frac{-ds_0^2}{c^2}} = \left(1 + \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2}\right)^{1/2} \mathrm{d}t. \tag{8-3-21} $$

> [!NOTE] 🖼️ Figure 描述  
> 本页涉及图4-21（原子钟环球飞行实验示意图）：  
> - 地球赤道剖面图，中心为地心 $O$  
> - 地面钟 $C_0$ 位于赤道表面（径向坐标 $r=R$），随地球自转角速度 $\Omega$ 运动  
> - 飞行钟 $C$ 位于赤道上空高度 $h$ 处（径向坐标 $r=R+h$），以相对速度 $v$ 向东飞行  
> - 世界线 $C_0$ 与 $C$ 在环球飞行起点和终点相交  
> - 坐标轴指向远方固定恒星（非旋转坐标系），满足 $r=0$ 于地心且不随地球自转

① 所选的史瓦西坐标需满足：①在地心有 $r=0$；②不随地球自转而转动（相应的 $x,y,z$ 轴分别指向远方固定恒星）。

> [!WARNING] 🛡️ 原文勘误  
> - OCR 识别错误：原文 "相应于 $v=0$" 中的 $v$ 易与后文飞机速度混淆，根据 [P-1] 页式(8-3-15)上下文，$v$ 特指飞机相对地面的东飞速度（非线速率），此处明确标注为"飞机速度"以避免歧义  
> - 符号统一：[P-1] 页使用 $v$ 表示飞机速度（如式(8-3-15)），而 [Target] 页误用 $v$ 描述钟状态；已修正为"相应于飞机速度 $v=0$"，并严格区分线速率 $u$ 与相对速度 $v$（[N+1] 页 $u = (R+h)\Omega + v$）  
> - 公式编号修正：式(8-3-18)后缺失标签，根据 [N+1] 页推导流程补充完整标签  

<CTX>
{ "summary": "本页核心为推导原子钟环球飞行实验的广义相对论修正项，通过史瓦西线元在地球引力场的应用，建立引力势与固有时间的关系，为证明式(8-3-15)奠定基础。关键步骤包括：坐标系选择、线元转换、地面钟固有时间计算。", "keywords": ["史瓦西线元", "引力势", "固有时间", "非旋转坐标系", "原子钟实验"] }
</CTX>