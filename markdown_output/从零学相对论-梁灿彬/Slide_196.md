# Slide 196

第8章 史瓦西时空

效应 1 狭义相对论的动钟变慢效应（续）  
由式(8-6-3)和式(8-6-4)，利用牛顿二项式定理 $(1 - x)^{-1/2} \approx 1 + x/2$（其中 $x \ll 1$），可得：  
\[
\gamma_{\text{卫}} = 1 + \frac{(u_{\text{卫}}/c)^2}{2}, \quad \gamma_{\text{赤}} = 1 + \frac{(u_{\text{赤}}/c)^2}{2},
\]  
其中 $u_{\text{卫}} = 3.84 \times 10^3  \text{m/s}$，$u_{\text{赤}} = 465  \text{m/s}$，$c = 3 \times 10^8  \text{m/s}$。代入式(8-6-3)：  
\[
\frac{\Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{赤}}}{\gamma_{\text{卫}}}, \quad \text{故} \quad \frac{\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{卫}} - \gamma_{\text{赤}}}{\gamma_{\text{卫}}} \approx \frac{1}{2} \left[ \left( \frac{u_{\text{卫}}}{c} \right)^2 - \left( \frac{u_{\text{赤}}}{c} \right)^2 \right] = \frac{1}{2} \left[ \left( \frac{3.84 \times 10^3}{3 \times 10^8} \right)^2 - \left( \frac{465}{3 \times 10^8} \right)^2 \right] = 0.81 \times 10^{-10}.
\]  
取 $\Delta \tau_{\text{赤}} = 1$ 天 $= 8.64 \times 10^{10}  \mu\text{s}$，则：  
\[
\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}} = (0.81 \times 10^{-10}) \times (8.64 \times 10^{10}  \mu\text{s}) = 7  \mu\text{s}. \tag{8-6-7}
\]  
这表明，由于速率较大，卫星钟比赤道上的海面参考钟每天要慢 $7  \mu\text{s}$。

效应 2 广义相对论的引力钟慢效应  
根据广义相对论，引力较强处的钟较慢。卫星钟位于高空，所受地球引力比赤道钟较弱，故赤道钟应较慢。下面用式(8-3-9')计算两者的读数差。  
令  
\[
\varepsilon_{\text{卫}} \equiv \frac{GM}{c^2 r_{\text{卫}}}, \quad \varepsilon_{\text{赤}} \equiv \frac{GM}{c^2 R}, \tag{8-6-8}
\]  
其中 $G$ 和 $M$ 分别代表引力常量和地球质量，$r_{\text{卫}}$ 代表卫星与地心的距离，$R$ 代表地球半径。由式(8-3-9')得：  
\[
\frac{\Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \sqrt{\frac{1 - 2\varepsilon_{\text{卫}}}{1 - 2\varepsilon_{\text{赤}}}} = (1 - 2\varepsilon_{\text{卫}})^{1/2}(1 - 2\varepsilon_{\text{赤}})^{-1/2} \approx (1 - \varepsilon_{\text{卫}})(1 + \varepsilon_{\text{赤}}) \approx 1 + \varepsilon_{\text{赤}} - \varepsilon_{\text{卫}}. \tag{8-6-9}
\]

> [!NOTE] 🖼️ Figure 描述  
> 图8-11：地心钟、赤道钟和卫星钟世界线示意  
> - **布局**：三条垂直世界线从左至右排列：左侧为地心钟，中间为赤道钟，右侧为卫星钟。  
> - **世界线**：均为竖直实线，表示在时空图中的轨迹；地心钟世界线标注“Δτ心=Δt”，赤道钟标注“Δτ赤”，卫星钟标注“Δτ卫”。  
> - **等时面**：两条水平实线 Σ_{t1}（下方）和 Σ_{t2}（上方）横穿所有世界线，代表坐标时刻 $t_1$ 和 $t_2$。  
> - **时间标注**：右侧有垂直箭头标注“Δt≡t2-t1”，顶部依次标注“地心钟”、“赤道钟”、“卫星钟”。  
> - **物理含义**：清晰展示不同参考系中固有时（Δτ）与坐标时（Δt）的相对性，用于推导相对论钟慢效应。

[选读 8-2]  
本选读准备就相对论在 GPS 中的应用问题进行更为深入和定量的讨论，特别强调如何从相对论的角度考虑问题。  

地球附近的时空弯曲可近似用史瓦西线元描述：  
\[
\mathrm{d}s^2 = -\left(1 - \frac{2M}{\hat{r}}\right) \mathrm{d}\hat{t}^2 + \left(1 - \frac{2M}{\hat{r}}\right)^{-1} \mathrm{d}\hat{r}^2 + \hat{r}^2 \left( \mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2 \right), \tag{8-6-15}
\]  
其中 $M$ 代表地球质量。对上式要做四点说明：  
(1) 为使核心坐标系符号简洁（$t, r, \theta, \varphi$），此处史瓦西坐标记为 $\hat{t}, \hat{r}, \theta, \varphi$；  
(2) 地球自转导致时空非静态，但其对几何的偏离在 GPS 精度范围内可忽略；  
(3) 坐标系 $\{\hat{r}, \theta, \varphi\}$ 必须固定于不随地球自转的参考系；  
(4) 式(8-6-15)为几何单位制，国际单位制形式为：  
\[
\mathrm{d}s^2 = -\left(1 - \frac{2GM}{c^2 \hat{r}}\right) (c \, \mathrm{d}\hat{t})^2 + \left(1 - \frac{2GM}{c^2 \hat{r}}\right)^{-1} \mathrm{d}\hat{r}^2 + \hat{r}^2 \left( \mathrm{d}\theta^2 + \sin^2\theta \, \mathrm{d}\varphi^2 \right). \tag{8-6-15'}
\]  
引入新径向坐标 $r$：  
\[
\hat{r} = \left(1 + \frac{GM}{2c^2 r}\right)^2 r, \tag{8-6-16}
\]  
则线元在新坐标系 $\{\hat{t}, r, \theta, \varphi\}$ 中为：  
\[
\mathrm{d}s^2 = -\left( \frac{1 - \frac{GM}{2c^2 r}}{1 + \frac{GM}{2c^2 r}} \right)^2 (c \, \mathrm{d}\hat{t})^2 + \left(1 + \frac{GM}{2c^2 r}\right)^4 \left( \mathrm{d}r^2 + r^2 \, \mathrm{d}\theta^2 + r^2 \sin^2\theta \, \mathrm{d}\varphi^2 \right). \tag{8-6-17}
\]  
定义引力势 $\Phi(r)$：  
\[
\Phi(r) \equiv -\frac{GM}{r}, \tag{8-6-18}
\]

> [!WARNING] 🛡️ 原文勘误  
> - **符号修正**：P-1 页中 "$u_卫$" 和 "$u_赤$" 在 OCR 识别时易混淆为希腊字母（如 $\nu$），但根据物理上下文（速率单位 m/s）及 N+1 页公式（如 $u_{\text{卫}}/c$），统一修正为拉丁字母 $u$（表示速率）。  
> - **公式连贯性**：Target 页开头重复 P-1 页的 $\gamma$ 展开式，但为保持逻辑流完整（P-1 被 Figure Analysis 中断），此处保留必要推导以衔接前文，避免读者断层。  
> - **单位标注**：$\mu\text{s}$ 在 OCR 中缺失微秒符号，根据 N+1 页 "8.64 × 10^{10} μs" 补全为 $\mu\text{s}$，确保单位一致性。

<CTX>
{ "summary": "本页延续 GPS 相对论效应分析：完成效应1（动钟变慢）的定量推导（卫星钟日慢7μs），并启动效应2（引力钟慢）的广义相对论计算；引入史瓦西线元进行深入讨论，强调时空弯曲对钟慢的影响。", "keywords": ["GPS相对论修正", "动钟变慢", "引力钟慢", "史瓦西线元", "固有时"] }
</CTX>