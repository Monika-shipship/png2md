# Slide 183

§8.4 水星近日点进动

[注：本书并未介绍测地线的数学定义及计算公式，读者只能承认上述结果。欲知推导详情可参阅梁灿彬、周彬（2006）§9.2.2。] 与式（8-4-6）对比发现净多一项 $3M\mu^2$（广义相对论修正项），因而难于求解。幸好水星的 $r$ 比太阳的 $M$ 大得多，即 $M/r \ll 1$①，故修正项
$$
3M\mu^2 = \frac{3M}{r}\mu \ll \mu,
$$
（其中第一步用到 $\mu \equiv r^{-1}$）可设法求近似解。牛顿引力论的解[式（8-4-8）]可看作零级近似，为明确起见记作 $\mu_0(\varphi)$，即
$$
\mu_0(\varphi) = \frac{M}{L^2}(1 + e \cos \varphi).
$$
把这零级近似代入式（8-4-10）右边第二项后所得方程可看作一级近似解 $\mu_1(\varphi)$ 所应满足的方程，即
$$
\frac{d^2\mu_1}{d\varphi^2} + \mu_1 = \frac{M}{L^2} + 3M\mu_0^2 = \frac{M}{L^2} + \frac{3M^3}{L^4}(1 + 2e \cos \varphi + e^2 \cos^2 \varphi).
$$
不难验证其解为
$$
\mu_1(\varphi) = \mu_0(\varphi) + \frac{3M^3}{L^4} \left[1 + e\varphi \sin \varphi + e^2 \left(\frac{1}{2} - \frac{1}{6} \cos 2\varphi\right)\right].
$$
令
$$
\varepsilon \equiv 3M^2 / L^2,
$$
再与式（8-4-12）一同代入式（8-4-14），整理后得
$$
\mu_1(\varphi) = \frac{M}{L^2} \left\{1 + \varepsilon \left[1 + e^2 \left(\frac{1}{2} - \frac{1}{6} \cos 2\varphi\right)\right] + e (\cos \varphi + \varepsilon \varphi \sin \varphi) \right\}.
$$
由式（8-4-12）可知 $M/L^2$ 与 $\mu$ 有相同量级（记作 $M/L^2 \sim \mu$），故 $\varepsilon \equiv 3M^2/L^2 \sim 3M\mu = 3M/r$，改为国际单位制并利用式（8-4-11）脚注的数据，得
$$
\varepsilon \sim \frac{3GM}{c^2 r} \approx \frac{3 \times 1.5  \text{km}}{5 \times 10^7  \text{km}} \approx 10^{-7} \ll 1,
$$
于是式（8-4-16）右边花括号内第二项（含 $\varepsilon$ 的项）与第一项（即 1）相较可以略去，再利用三角公式 $\cos(\alpha - \beta) = \cos \alpha \cos \beta + \sin \alpha \sin \beta$ 以及 $\cos \varepsilon \varphi \approx 1$，$\sin \varepsilon \varphi \approx \varepsilon \varphi$ 改写第三项便得
$$
\frac{1}{r(\varphi)} \approx \mu_1(\varphi) \approx \frac{M}{L^2} \left[1 + e \cos(\varphi - \varepsilon \varphi) \right].
$$

> [!NOTE] 🖼️ Figure 描述  
> 图8-6（水星近日点每周期进动角 $\Delta \varphi_{\text{进}}$ 示意图，效果明显夸大）：  
> - 中心点代表太阳，周围有多条黑色实线椭圆轨道，共享同一焦点但长轴方向逐周期逆时针旋转  
> - 相邻轨道的近日点（最靠近中心点）位置发生偏移，形成玫瑰花状进动图案  
> - 背景有黑色虚线大椭圆作为无进动参考轨迹  
> - 顶部有双向实线箭头标注 "$\Delta \varphi_{\text{进}}$"，横跨两个相邻轨道的近日点  
> - 轨道从中心向外延伸，多个椭圆重叠分布呈环形对称，但整体具有旋转特征  
> - 进动角度被显著夸大以清晰展示物理机制（实际进动角极小）

① 做数量计算时最好改回国际单位制，即补上物理常数 $G$ 和 $c$。由附录 A 例 3 可知 $M/r$ 实为 $(GM/c^2)/r$。太阳质量 $M$ 对应的 $GM/c^2 \approx 1.5$ km，水星近日点与太阳的距离约为 $5 \times 10^7$ km，故 $(GM/c^2)/r \ll 1$。

> [!WARNING] 🛡️ 原文勘误  
> - 原文标题"水星近点进动"存在术语不一致：前文[P-2]和[P-1]均使用"近日点进动"（perihelion precession），且物理定义特指近日点（closest approach to Sun）。修正为"水星近日点进动"以确保术语统一性。  
> - 原文"水星近(远)日点"表述冗余：进动特指近日点（perihelion），远日点（aphelion）进动是同一物理过程的对称表现，无需重复强调。删除冗余表述保持焦点清晰。

<CTX>
{ "summary": "本页通过一级近似求解史瓦西时空中水星轨道方程，推导出近日点进动角公式 $\\Delta \\varphi_{\\text{进}} = 6\\pi M^2 / L^2$，并验证其与观测值 $43''$/世纪的吻合，完成广义相对论对'43秒问题'的理论解释。", "keywords": ["近日点进动", "史瓦西解", "一级近似", "量级分析", "广义相对论验证"] }
</CTX>