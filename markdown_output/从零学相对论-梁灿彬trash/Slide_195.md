# Slide 195

解出 4 个未知数 $t,x,y,z$（用户收信时的时空坐标），从而实现定时和定位。

稍有力学常识的人都能接受式(8-6-2)，从而理解 GPS 的基本原理。然而，由于对 GPS 的精度要求很高，许多附加问题都不得不考虑。原子钟走时率的精度是足够高的，但其表观走时率却会因为相对论效应而受到影响，如果对此不加修正，GPS 所给出的位置误差可达每天 11 km 的程度，这种误差的积累效应将使 GPS 很快就变得毫无用处。GPS 的相对论效应主要表现为两个方面，分述如下。

**效应 1：狭义相对论的动钟变慢效应**

地球上的时间以国际原子时间（International Atomic Time）为标准，它由静止于海平面的原子钟给出。以下称此为海面钟。相对于地心而言，卫星钟以速率 $u_{\text{卫}} = 3.84 \times 10^3  \text{m/s}$ 做高速运动。海面钟虽然也随地球自转而运动，但即使是赤道上的海面钟的速率也不过 $u_{\text{赤}} = 465  \text{m/s}$（下面就以赤道钟作为海面钟的代表）。由于狭义相对论的动钟变慢效应，相对于地心钟而言，卫星钟的变慢比赤道钟要严重得多。既然以赤道钟为时间标准，就应对卫星钟进行修正。地心钟的世界线可画成竖直线，赤道钟和卫星钟的世界线都是螺旋线，但在示意图中不妨画成斜率不同的斜直线（图 8-11）。以 $\Sigma_{t_1}$ 和 $\Sigma_{t_2}$ 代表两个相邻的同时面（等 $t$ 面），令 $\Delta t \equiv t_2 - t_1$，以 $\Delta\tau_{\text{心}}$、$\Delta\tau_{\text{赤}}$ 和 $\Delta\tau_{\text{卫}}$ 依次代表三个钟在这两张同时面之间经历的固有时间，则由狭义相对论的动钟变慢效应可知[见式(4-2-1)]：
$$
\Delta\tau_{\text{卫}} = \gamma_{\text{卫}}^{-1} \Delta t, \quad \Delta\tau_{\text{赤}} = \gamma_{\text{赤}}^{-1} \Delta t, \quad \Delta\tau_{\text{心}} = \Delta t, \tag{8-6-3}
$$
其中
$$
\gamma_{\text{卫}} \equiv [1 - (u_{\text{卫}}/c)^2]^{-1/2}, \quad \gamma_{\text{赤}} \equiv [1 - (u_{\text{赤}}/c)^2]^{-1/2}. \tag{8-6-4}
$$
因为 $(u_{\text{卫}}/c)^2 \ll 1$，$(u_{\text{赤}}/c)^2 \ll 1$，上式可用牛顿二项式定理
$$
(1 - x)^{-1/2} \approx 1 + \frac{x}{2} \tag{8-6-5}
$$
简化为
$$
\gamma_{\text{卫}} \approx 1 + \frac{(u_{\text{卫}}/c)^2}{2}, \quad \gamma_{\text{赤}} \approx 1 + \frac{(u_{\text{赤}}/c)^2}{2},
$$
而式(8-6-3)给出 $\frac{\Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{赤}}}{\gamma_{\text{卫}}}$，因而
$$
\frac{\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{卫}} - \gamma_{\text{赤}}}{\gamma_{\text{卫}}} \approx \frac{[(u_{\text{卫}}/c)^2 - (u_{\text{赤}}/c)^2]/2}{1 + (u_{\text{卫}}/c)^2/2} \approx \frac{1}{2}\left[\left(\frac{u_{\text{卫}}}{c}\right)^2 - \left(\frac{u_{\text{赤}}}{c}\right)^2\right] = \frac{1}{2}\left[\left(\frac{3.84 \times 10^3}{3 \times 10^8}\right)^2 - \left(\frac{465}{3 \times 10^8}\right)^2\right] = \frac{1}{2}(1.64 \times 10^{-10} - 0.024 \times 10^{-10}) = 0.81 \times 10^{-10}.
$$
如果取
$$
\Delta \tau_{\text{赤}} = 1  \text{天} = 24 \times 3600  \text{s} = 8.64 \times 10^{10}  \mu\text{s}, \tag{8-6-6}
$$
则
$$
\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}} = (0.81 \times 10^{-10}) \times 8.64 \times 10^{10}  \mu\text{s} = 7  \mu\text{s}. \tag{8-6-7}
$$
这就表明，由于速率较大，卫星钟比赤道上的海面参考钟每天要慢 $7  \mu\text{s}$。

> [!NOTE] 🖼️ Figure 8-10 描述  
> **空间图 (a)**：地球（中心灰色球体，标注"地球"），用户位置（地表左侧实心点，标注"用户"），四个卫星位置（地球上方按1-4编号的空心圆点），所有卫星至用户的带箭头实线表示信号传输方向。  
> **时空图 (b)**：用户世界线（近似垂直实线，顶部标注"用户"），卫星世界线（右侧弯曲实线，顶部标注"卫星(第i个)"），收信事件 $q$（用户线上实心点），发信事件 $p_i$（卫星线上实心点），光子路径（$q$ 到 $p_i$ 的带箭头实线，标注"光子"）。

<CTX>
{ "summary": "本页核心讨论GPS中狭义相对论效应（动钟变慢）的定量计算：卫星钟因高速运动比海面钟每天慢7μs，并强调相对论修正对GPS精度的必要性。", "keywords": ["GPS", "狭义相对论", "动钟变慢", "时间修正", "原子钟"] }
</CTX>