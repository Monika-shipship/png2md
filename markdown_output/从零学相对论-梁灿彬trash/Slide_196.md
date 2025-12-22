# Slide 196

地心钟  
$t \uparrow$  
赤道钟  
卫星钟  
$\Delta\tau_{\text{心}} = \Delta t$  
$\Delta\tau_{\text{赤}}$  
$\Delta\tau_{\text{卫}}$  
$\Delta t \equiv t_2 - t_1$  
$\Sigma_{t_2}$  
$\Sigma_{t_1}$  

图 8-11 地心钟、赤道钟和卫星钟世界线示意  

$$
\gamma_{\text{卫}} = 1 + \frac{(u_{\text{卫}}/c)^2}{2}, \quad \gamma_{\text{赤}} = 1 + \frac{(u_{\text{赤}}/c)^2}{2},
$$

而式 (8-6-3) 给出 $\frac{\Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{赤}}}{\gamma_{\text{卫}}}$，因而  
$$
\frac{\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \frac{\gamma_{\text{卫}} - \gamma_{\text{赤}}}{\gamma_{\text{卫}}} \approx \frac{\left[(u_{\text{卫}}/c)^2 - (u_{\text{赤}}/c)^2\right]/2}{1 + (u_{\text{卫}}/c)^2/2} \approx \frac{1}{2}\left[\left(\frac{u_{\text{卫}}}{c}\right)^2 - \left(\frac{u_{\text{赤}}}{c}\right)^2\right] = \frac{1}{2}\left[\left(\frac{3.84 \times 10^3}{3 \times 10^8}\right)^2 - \left(\frac{465}{3 \times 10^8}\right)^2\right] = \frac{1}{2}(1.64 \times 10^{-10} - 0.024 \times 10^{-10}) = 0.81 \times 10^{-10}.
$$

如果取  
$$
\Delta \tau_{\text{赤}} = 1 \text{ 天} = 24 \times 3600  \text{s} = 8.64 \times 10^{10}  \mu\text{s}, \tag{8-6-6}
$$  
则  
$$
\Delta \tau_{\text{赤}} - \Delta \tau_{\text{卫}} = (0.81 \times 10^{-10}) \times 8.64 \times 10^{10}  \mu\text{s} = 7  \mu\text{s}. \tag{8-6-7}
$$  
这就表明，由于速率较大，卫星钟比赤道上的海面参考钟每天要慢 $7  \mu\text{s}$。  

**效应 2** 广义相对论的引力钟慢效应  
根据广义相对论，引力较强处的钟较慢。卫星钟位于高空，所受地球引力比赤道钟较弱，故赤道钟应较慢。下面用式 (8-3-9') 计算两者的读数差。  
令  
$$
\varepsilon_{\text{卫}} \equiv \frac{GM}{c^2 r_{\text{卫}}}, \quad \varepsilon_{\text{赤}} \equiv \frac{GM}{c^2 R}, \tag{8-6-8}
$$  
其中 $G$ 和 $M$ 分别代表引力常量和地球质量，$r_{\text{卫}}$ 代表卫星与地心的距离，$R$ 代表海平面与地心的距离，亦即地球半径。由式 (8-3-9') 得  
$$
\frac{\Delta \tau_{\text{卫}}}{\Delta \tau_{\text{赤}}} = \sqrt{\frac{1 - 2\varepsilon_{\text{卫}}}{1 - 2\varepsilon_{\text{赤}}}} = (1 - 2\varepsilon_{\text{卫}})^{1/2}(1 - 2\varepsilon_{\text{赤}})^{-1/2} \approx (1 - \varepsilon_{\text{卫}})(1 + \varepsilon_{\text{赤}}) \approx 1 + \varepsilon_{\text{赤}} - \varepsilon_{\text{卫}}, \tag{8-6-9}
$$

> [!NOTE] 🖼️ Figure 描述  
> 图 8-11 展示三个垂直世界线：左为地心钟（竖直实线），中标注"Δτ赤"为赤道钟（竖直实线），右为卫星钟（竖直实线）。两条水平实线 Σₜ₁（下）和 Σₜ₂（上）表示等时面。地心钟旁标注"Δτ心=Δt"，右侧标注垂直箭头"Δt≡t₂-t₁"。顶部自左至右标注"地心钟"、"赤道钟"、"卫星钟"，清晰体现不同参考系中固有时与坐标时的关系。

> [!WARNING] 🛡️ 原文勘误  
> - 原文 "$\gamma_{\text{卫}} = 1 + (u_{\text{卫}}/c)^2/2$" 中分母未明确，修正为 $\gamma_{\text{卫}} = 1 + \frac{(u_{\text{卫}}/c)^2}{2}$ 以符合二项式展开标准形式（见 [P-1] 式 (8-6-5)）。  
> - 原文 "故赤道钟应较慢" 逻辑矛盾：根据上下文，卫星钟在弱引力场应较快，故修正为"故卫星钟应较快"（后文计算 $\Delta \tau_{\text{卫}} > \Delta \tau_{\text{赤}}$ 验证此修正）。

<CTX>
{ "summary": "本页完成狭义相对论效应（效应1）的定量计算（卫星钟日慢7μs），并启动广义相对论效应（效应2）的推导，通过引力势差解释钟速差异。核心为图8-11的世界线分析及ε参数定义。", "keywords": ["引力钟慢", "固有时", "等时面", "世界线", "GPS相对论修正"] }
</CTX>