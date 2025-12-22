# Slide 175

§ 8.3 引力钟慢和引力红移

$$ t_1' - t_2' = \int_{r_2}^{r_1} \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r \tag{8-3-8} $$

对比以上两式得 $t_1' - t_2' = t_1 - t_2$，因而 $t_1' - t_1 = t_2' - t_2$，此即 $\Delta t_1/\Delta t_2 = 1$。代入式 $(8-3-4)$ 便有

$$ \frac{\Delta \tau_1}{\Delta \tau_2} = \sqrt{\frac{1 - 2M/r_1}{1 - 2M/r_2}} > 1 \quad (\because r_2 < r_1) \tag{8-3-9} $$

即 $\Delta \tau_1 > \Delta \tau_2$，所以观者 $G_1$ 认为观者 $G_2$ 的钟较慢，就是说：引力场强越大处的钟越慢。由于 $G_1$ 和 $G_2$ 都是静态观者，各自静止于空间点 $(r_1,\theta,\varphi)$ 和 $(r_2,\theta,\varphi)$ 上，可以认为两者之间没有相对运动（哪个也不是"动钟"），所以说这种钟慢效应纯粹起因于引力场，因而称为引力钟慢效应（英语文献也称之为引力场中的时间延缓效应）。我们刚才只就史瓦西时空对此效应给了证明，其实还可证明这一效应对任何静态时空都成立，只不过式 $(8-3-9)$ 要适当修改。

为了对式 $(8-3-9)$ 有一个定量的、联系实际的理解，我们来比较位于地球表面不同高度的两只原子钟的表观走时率。第一只钟保存在美国国家标准局（National Institute of Standards and Technology）里，该局位于美国科罗拉多州的博尔德市（Boulder, Colorado），海拔 5 400 英尺（$\approx$ 1 645.9 m）；第二只钟保存在英国皇家格林尼治天文台（Royal Greenwich Observatory），海拔 80 英尺（$\approx$ 24.4 m）。由于两钟存在高度差 $\Delta h \approx 1\ 621.5$ m，每年读数差竟达 5.6 $\mu$s。下面是求得此值的计算过程。

为便于数值计算，先将式 $(8-3-9)$（在几何单位制中成立）改为国际单位制形式：

$$ \frac{\Delta \tau_1}{\Delta \tau_2} = \sqrt{\frac{1 - 2GM/c^2 r_1}{1 - 2GM/c^2 r_2}} \tag{8-3-9'} $$

其中 $G$ 和 $c$ 分别是引力常量和真空光速在国际单位制的数值。用于刚才的问题，则 $M$ 代表地球质量，$r_1$ 和 $r_2$ 分别代表上述两钟与地心的距离。令

$$ \varepsilon_1 \equiv \frac{GM}{c^2 r_1}, \quad \varepsilon_2 \equiv \frac{GM}{c^2 r_2} \tag{8-3-10} $$

则式 $(8-3-9')$ 成为

$$ \frac{\Delta \tau_1}{\Delta \tau_2} = \sqrt{\frac{1 - 2\varepsilon_1}{1 - 2\varepsilon_2}} = (1 - 2\varepsilon_1)^{1/2} (1 - 2\varepsilon_2)^{-1/2} \tag{8-3-11} $$

由数值估算可知 $2\varepsilon_1 \ll 1$，$2\varepsilon_2 \ll 1$，由牛顿二项式定理得

$$ \frac{\Delta \tau_1}{\Delta \tau_2} \approx (1 - \varepsilon_1)(1 + \varepsilon_2) \approx 1 + \varepsilon_2 - \varepsilon_1 \tag{8-3-12} $$

> [!NOTE] 🖼️ Figure 描述
> 图8-4：静态引力场的钟慢效应示意图。坐标系中横轴为径向坐标 $r$，纵轴为时间坐标 $t$。右侧竖直线 $G_1$ 位于 $r = r_1$ 处，左侧竖直线 $G_2$ 位于 $r = r_2$ 处（$r_2 < r_1$）。$G_1$ 线上有两点 $p_1$（$t = t_1$）和 $p_1'$（$t = t_1'$），$G_2$ 线上有两点 $p_2$（$t = t_2$）和 $p_2'$（$t = t_2'$）。从 $p_1$ 和 $p_1'$ 向左延伸水平虚线至 $t$ 轴，分别标记为 $t_1$ 和 $t_1'$；从 $p_2$ 和 $p_2'$ 向右延伸水平虚线至 $t$ 轴，分别标记为 $t_2$ 和 $t_2'$。曲线 $\gamma$ 从 $p_2$ 到 $p_1$，曲线 $\gamma'$ 从 $p_2'$ 到 $p_1'$，均为向上向右弯曲的类光测地线。$G_1$ 线上 $p_1$ 与 $p_1'$ 间用双向箭头标记 $\Delta\tau_1$，$G_2$ 线上 $p_2$ 与 $p_2'$ 间标记 $\Delta\tau_2$。

> [!WARNING] 🛡️ 原文勘误
> 1. "National Bureau of Standards" 应更新为 "National Institute of Standards and Technology"（该机构1988年更名）
> 2. 公式 (8-3-10) 中符号应统一为 $\varepsilon_1 \equiv \frac{GM}{c^2 r_1}$（原文缺少分式线，已修正）
> 3. 原文"博尔德市（Boul-der，Colorado）"存在断字错误，应为"Boulder, Colorado"

<CTX>
{ "summary": "本页详细推导引力钟慢效应的数学表达式，并通过地球表面不同高度的原子钟实例进行定量验证。核心是证明静态观者间的引力钟慢效应 $\Delta\tau_1/\Delta\tau_2 = \sqrt{(1-2M/r_1)/(1-2M/r_2)}$，并计算出高度差1621.5m导致的年累积时间差5.6μs。", "keywords": ["引力钟慢效应", "静态时空", "史瓦西度规", "原子钟验证", "单位制转换"] }
</CTX>