# Slide 186

第8章 史瓦西时空

[选读 8-2]  
本选读准备就相对论在 GPS（全球定位系统）中的应用问题进行更为深入和定量的讨论，特别强调如何从相对论的角度考虑问题。

地球附近的时空弯曲可近似用史瓦西线元描述：

$$
\mathrm{d}s^2 = -\left(1 - \frac{2M}{\hat{r}}\right) \mathrm{d}\hat{t}^2 + \left(1 - \frac{2M}{\hat{r}}\right)^{-1} \mathrm{d}\hat{r}^2 + \hat{r}^2 \left( \mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2 \right),
$$
(8-6-15)

其中 $M$ 代表地球质量。对上式要做四点说明。

(1) 因为后面要涉及若干个坐标系，为使最有用的坐标系有最简单的坐标记号（即 $t$, $r$, $\theta$, $\varphi$），宁愿将此处的史瓦西坐标写成 $\hat{t}$, $\hat{r}$, $\theta$, $\varphi$。

(2) 由于地球有自转（非静态），其外部时空几何与史瓦西线元略有偏离。幸好，量级估算表明，在 GPS 要求的精度内完全可用史瓦西线元讨论。

(3) 虽然地球自转对外部时空几何的影响可以忽略，但海面钟随地球自转的运动速率必须考虑。选择坐标系时要格外留意，上式的空间坐标系 $\{\hat{r}, \theta, \varphi\}$ 必须是不随地球自转的。

(4) 上式是史瓦西线元在几何单位制的表达式。为便于定量计算，下面改用国际单位制表达式（其中 $G$ 为引力常量，$c$ 为真空光速）：

$$
\mathrm{d}s^2 = -\left(1 - \frac{2GM}{c^2 \hat{r}}\right) (c \, \mathrm{d}\hat{t})^2 + \left(1 - \frac{2GM}{c^2 \hat{r}}\right)^{-1} \mathrm{d}\hat{r}^2 + \hat{r}^2 \left( \mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2 \right).
$$
(8-6-15')

用下式引入新的径向坐标 $r$：

$$
\hat{r} = \left(1 + \frac{GM}{2c^2 r}\right)^2 r,
$$
(8-6-16)

则线元 (8-6-15') 在新坐标系 $\{\hat{t}, r, \theta, \varphi\}$ 中取如下形式：

$$
\mathrm{d}s^2 = -\left( \frac{1 - \frac{GM}{2c^2 r}}{1 + \frac{GM}{2c^2 r}} \right)^2 (c \, \mathrm{d}\hat{t})^2 + \left(1 + \frac{GM}{2c^2 r}\right)^4 \left( \mathrm{d}r^2 + r^2 \, \mathrm{d}\theta^2 + r^2 \sin^2\theta \, \mathrm{d}\varphi^2 \right).
$$
(8-6-17)

仿照牛顿引力势的概念，用下式定义引力势 $\Phi(r)$：

$$
\Phi(r) \equiv -\frac{GM}{r},
$$
(8-6-18)

则

> [!NOTE] 🖼️ Figure 描述  
> 图8-11（位于前页）展示了地心钟、赤道钟和卫星钟的世界线示意：三条垂直实线从左至右依次为地心钟、赤道钟和卫星钟的世界线；两条水平实线标记为 $\Sigma_{t_1}$（下）和 $\Sigma_{t_2}$（上），表示等时面；标注包括 $\Delta\tau_{\text{心}} = \Delta t$（地心钟固有时）、$\Delta\tau_{\text{赤}}$（赤道钟固有时）、$\Delta\tau_{\text{卫}}$（卫星钟固有时）及 $\Delta t \equiv t_2 - t_1$（坐标时间间隔）。该图清晰呈现了不同参考系中时间测量的相对性，为本选读的定量讨论提供几何基础。

<CTX>
{ "summary": "本页开启选读部分，从史瓦西线元出发推导GPS相对论效应的统一公式，强调坐标系选择与单位制转换的关键作用", "keywords": ["史瓦西线元", "GPS相对论修正", "坐标变换", "引力势", "国际单位制"] }
</CTX>