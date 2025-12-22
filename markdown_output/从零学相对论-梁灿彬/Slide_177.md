# Slide 165

地球引力场使地球附近的时空弯曲，式(4-3-1)的闵氏线元应被史瓦西线元取代：
$$
ds^2 = -\left(1 - \frac{2M}{r}\right) dt^2 + \left(1 - \frac{2M}{r}\right)^{-1} dr^2 + r^2 (d\theta^2 + \sin^2\theta \, d\varphi^2), \quad \text{①}
\tag{8-3-16}
$$
其中 $M$ 是地球质量。上式适用于几何单位制，为便于数值计算，宜改用国际单位制形式：
$$
ds^2 = -\left(1 - \frac{2GM}{c^2 r}\right) c^2 dt^2 + \left(1 - \frac{2GM}{c^2 r}\right)^{-1} dr^2 + r^2 (d\theta^2 + \sin^2\theta \, d\varphi^2),
\tag{8-3-16'}
$$
其中 $G$ 和 $c$ 分别是引力常量和真空光速在国际单位制中的数值。仿照牛顿引力势的概念，用下式定义引力势 $\Phi(r)$：
$$
\Phi(r) \equiv -\frac{GM}{r},
\tag{8-3-17}
$$
则
$$
ds^2 = -\left(1 + \frac{2\Phi}{c^2}\right) c^2 dt^2 + \left(1 + \frac{2\Phi}{c^2}\right)^{-1} dr^2 + r^2 (d\theta^2 + \sin^2\theta \, d\varphi^2),
\tag{8-3-18}
$$
先讨论静止于赤道上的钟 $C_0$（相应于 $v=0$，仍见图4-21）。因赤道上有 $r=R$，$dr=0$，$\theta=\pi/2$，$d\theta=0$ 及 $d\varphi=\Omega \, dt$，故式(8-3-18)用于 $C_0$ 线的任一元段给出
$$
ds_0^2 = -\left(1 + \frac{2\Phi_0}{c^2}\right) c^2 dt^2 + R^2 d\varphi^2 = -\left(1 + \frac{2\Phi_0}{c^2}\right) c^2 dt^2 + R^2 \Omega^2 dt^2 = -\left(1 + \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2}\right) c^2 dt^2,
\tag{8-3-19}
$$
其中
$$
\Phi_0 \equiv \Phi(R) = -\frac{GM}{R}
\tag{8-3-20}
$$
是赤道上的引力势，$u_0 = R\Omega$ 是 $C_0$ 钟（随地球自转）的线速率。于是元段的固有时间为
$$
d\tau_0 = \sqrt{\frac{-ds_0^2}{c^2}} = \left(1 + \frac{2\Phi_0}{c^2} - \frac{u_0^2}{c^2}\right)^{1/2} dt.
\tag{8-3-21}
$$

> [!NOTE] 🖼️ Figure 描述  
> ① 所选的史瓦西坐标需满足：(1) 在地心有 $r=0$；(2) 不随地球自转而转动（相应的 $x,y,z$ 坐标轴指向远方固定恒星）。此坐标系为惯性参考系，用于描述地球引力场中的时空几何。

<CTX>
{
  "summary": "本页详细推导地球引力场中赤道静止钟的固有时间表达式，通过史瓦西线元引入国际单位制形式，并定义引力势函数。核心是建立式(8-3-21)的固有时间微分关系，为后续验证原子钟实验提供理论基础。",
  "keywords": ["史瓦西线元", "引力势", "固有时间", "赤道静止钟", "坐标系选择"]
}
</CTX>