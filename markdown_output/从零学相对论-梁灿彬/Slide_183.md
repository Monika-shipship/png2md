# Slide 183

§8.4 水星近日点进动

[注：本书并未介绍测地线的数学定义及计算公式，读者只能承认上述结果。欲知推导详情可参阅梁灿彬，周彬（2006）小节9.2.2。] 与牛顿引力论的微分方程 $\frac{d^{2}\mu}{d\varphi^{2}} + \mu = \frac{M}{L^{2}}$ 对比，广义相对论方程净多一项 $3M\mu^{2}$（广义相对论修正项），因而难于求解。幸好水星的 $r$ 比太阳的 $M$ 大得多，即 $M/r \ll 1$<sup>①</sup>，故修正项
$$
3M\mu^{2} = \frac{3M}{r}\mu \ll \mu,
$$
（其中第一步用到 $\mu \equiv r^{-1}$）可设法求近似解。牛顿引力论的解
$$
\mu_{0}(\varphi) = \frac{M}{L^{2}}(1 + e \cos \varphi)
$$
可看作零级近似。把这零级近似代入式 (8-4-10) 右边第二项后所得方程可看作一级近似解 $\mu_{1}(\varphi)$ 所应满足的方程，即
$$
\frac{d^{2}\mu_{1}}{d\varphi^{2}} + \mu_{1} = \frac{M}{L^{2}} + 3M\mu_{0}^{2} = \frac{M}{L^{2}} + \frac{3M^{3}}{L^{4}}(1 + 2e \cos \varphi + e^{2} \cos^{2} \varphi).
$$
不难验证其解为
$$
\mu_{1}(\varphi) = \mu_{0}(\varphi) + \frac{3M^{3}}{L^{4}} \left[1 + e\varphi \sin \varphi + e^{2} \left(\frac{1}{2} - \frac{1}{6} \cos 2\varphi\right)\right].
$$
令
$$
\varepsilon \equiv 3M^{2} / L^{2},
$$
再与式 (8-4-12) 一同代入式 (8-4-14)，整理后得
$$
\mu_{1}(\varphi) = \frac{M}{L^{2}} \left\{1 + \varepsilon \left[1 + e^{2} \left(\frac{1}{2} - \frac{1}{6} \cos 2\varphi\right)\right] + e (\cos \varphi + \varepsilon \varphi \sin \varphi) \right\}.
$$
由式 (8-4-12) 可知 $M/L^{2}$ 与 $\mu$ 有相同量级（记作 $M/L^{2} \sim \mu$），故 $\varepsilon \equiv 3M^{2}/L^{2} \sim 3M\mu = 3M/r$，改为国际单位制并利用式 (8-4-11) 脚注的数据，得
$$
\varepsilon \sim \frac{3GM}{c^{2} r} \approx \frac{3 \times 1.5 \text{ km}}{5 \times 10^{7} \text{ km}} \approx 10^{-7} \ll 1,
$$
于是式 (8-4-16) 右边花括号内第二项（含 $\varepsilon$ 的项）与第一项（即 1）相较可以略去，再利用三角公式 $\cos(\alpha - \beta) = \cos \alpha \cos \beta + \sin \alpha \sin \beta$ 以及 $\cos \varepsilon \varphi \approx 1$，$\sin \varepsilon \varphi \approx \varepsilon \varphi$ 改写第三项便得
$$
\frac{1}{r(\varphi)} \approx \mu_{1}(\varphi) \approx \frac{M}{L^{2}} \left[1 + e \cos(\varphi - \varepsilon \varphi) \right].
$$

> [!NOTE] 🖼️ Figure 描述  
> 图8-6：水星近日点进动示意图。中心点代表太阳，周围有多条实线绘制的椭圆轨道，共享中心点但长轴方向逐周期逆时针旋转，形成玫瑰花状进动图案。每个椭圆闭合，相邻轨道的近日点位置沿逆时针方向偏移。背景有一条虚线大椭圆作为无进动参考轨迹。顶部有双向箭头标注"Δφ<sub>进</sub>"，横跨两个相邻轨道的近日点位置，表示每周期进动角度。进动效果被明显夸大以清晰展示（实际角度极小）。轨道线为黑色实线，参考轨迹为黑色虚线，箭头为黑色实线带箭头。整体呈环形对称布局，但因进动具有旋转特征。

<sup>①</sup> 做数量计算时最好改回国际单位制，即补上物理常数 $G$ 和 $c$。由附录 A 例 3 可知 $M/r$ 实为 $(GM/c^{2})/r$。太阳质量 $M$ 对应的 $GM/c^{2} \approx 1.5$ km，水星近日点与太阳的距离约为 $5 \times 10^{7}$ km，故 $(GM/c^{2})/r \ll 1$。

> [!WARNING] 🛡️ 原文勘误  
> 1. 标题原文“水星近点进动”应为“水星近日点进动”：根据 [P-2] 页标题“§ 8.4 水星近日点进动”及全章内容，此处“近点”系OCR识别错误，正确术语应为“近日点”（perihelion）。  
> 2. 公式 (8-4-10) 上下文修正：[P-1] 页末明确给出广义相对论方程为 $\frac{d^{2}\mu}{d\varphi^{2}} + \mu = \frac{M}{L^{2}} + 3M\mu^{2}$，故 [Target] 中“与式（8-4-6）对比”应修正为“与牛顿引力论的微分方程对比”。式 (8-4-6) 在 [P-1] 为平方形式 $\left( \frac{d\mu}{d\varphi} \right)^{2} + \mu^{2} = \frac{2A}{mL^{2}} + \frac{2M}{L^{2}}\mu$，而对比对象实为微分方程形式，此系作者笔误。  
> 3. 符号统一：原文中“$u_{\varphi}$”在 [P-1] 页定义为切向速度分量，此处保持 $u_{\varphi}$ 符号（非 $\nu$）；所有 $\varphi$ 统一为斜体（非正体），符合物理惯例。

<CTX>
{ "summary": "本页推导广义相对论对水星近日点进动的修正：通过一级近似解法，从史瓦西度规下的测地线方程导出进动角公式，解释43角秒/世纪观测值。关键步骤包括引入小参数ε、忽略高阶项、三角恒等式简化，最终得到进动轨道方程。", "keywords": ["近日点进动", "史瓦西度规", "测地线方程", "一级近似解", "小参数展开"] }
</CTX>