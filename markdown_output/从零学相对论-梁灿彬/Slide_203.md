# Slide 203

§8.6 相对论在 GPS(全球定位系统)中的应用

$$
\mathrm{d}t = \left(1 + \frac{\Phi - \Psi_0}{c^2} - \frac{u^2}{2c^2}\right)^{-1} \mathrm{d}\tau \approx \left(1 - \frac{\Phi - \Psi_0}{c^2} + \frac{u^2}{2c^2}\right) \mathrm{d}\tau \quad (8\text{-}6\text{-}39')
$$

这就是任一钟的 GPS 时间 $t$ 与固有时间 $\tau$ 的微分关系。用于卫星钟，以 $\mu$ 代表卫星钟世界线上我们关心的一段，由于卫星高度 $r_{\text{卫}}$ 及速率 $u_{\text{卫}}$ 近似为常数，将上式沿 $\mu$ 段积分得

$$
\int_{\mu} \mathrm{d}t = \int_{\mu} \mathrm{d}\tau_{\text{卫}} - \left( \frac{\Phi_{\text{卫}} - \Psi_0}{c^2} - \frac{u_{\text{卫}}^2}{2c^2} \right) \int_{\mu} \mathrm{d}\tau_{\text{卫}} \quad (8\text{-}6\text{-}40)
$$

令 $\Delta t \equiv \int_{\mu} \mathrm{d}t$，$\Delta \tau_{\text{卫}} \equiv \int_{\mu} \mathrm{d}\tau_{\text{卫}}$，$(\Delta t)_{\text{修}} \equiv - \left( \frac{\Phi_{\text{卫}} - \Psi_0}{c^2} - \frac{u_{\text{卫}}^2}{2c^2} \right) \Delta \tau_{\text{卫}}$，

$$
\Delta t = \Delta \tau_{\text{卫}} + (\Delta t)_{\text{修}} \quad (8\text{-}6\text{-}42)
$$

卫星经历的 GPS 时间 $\Delta t$ 之所以不等于固有时间 $\Delta \tau_{\text{卫}}$，就是因为上式右边多了修正项 $(\Delta t)_{\text{修}}$。现在可以明确指出，传播延迟方程 $(8\text{-}6\text{-}2)$ 中的 $t$ 和 $t_i$ 都是 $\{t, r, \theta, \varphi\}$ 系的坐标时 (GPS 时)，因此，从卫星钟读出固有时间 $\Delta \tau_{\text{卫}}$ 后，应先加上 $(\Delta t)_{\text{修}}$ 以得到 GPS 时间 $\Delta t$，然后发出信号。信号应包含发信时的 GPS 时刻 $t_i$ 以及卫星在此时的空间坐标 $r_i, \theta_i, \varphi_i$ 等内容，以便用户当作已知数求解传播延迟方程 $(8\text{-}6\text{-}2)$，从而得到自己的时空坐标 $t, r, \theta, \varphi$，达到定时定位的目的。这里的 $t$ 就是用户收信时的 GPS 时刻，它与国际标准一致。

现在把式 $(8\text{-}6\text{-}41)$ 的 $(\Delta t)_{\text{修}}$ 与选读前的两个修正项 (效应 1 和 2) 做一对比。由式 $(8\text{-}6\text{-}18)$ 知

$$
\frac{\Phi_{\text{卫}}}{c^2} \equiv - \frac{GM}{c^2} \frac{1}{r_{\text{卫}}} \quad (8\text{-}6\text{-}43)
$$

常数 $\Psi_0$ 可借赤道上的 A 点求得。由式 $(8\text{-}6\text{-}28)$ 和式 $(8\text{-}6\text{-}18)$ 得

$$
\frac{\Psi_0}{c^2} = \frac{\Psi|_A}{c^2} = \frac{\Phi|_A}{c^2} - \frac{(\Omega R \sin \theta_A)^2}{2c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{(\Omega R)^2}{2c^2} = - \frac{GM}{c^2} \frac{1}{R_{\text{赤}}} - \frac{u_{\text{赤}}^2}{2c^2} \quad (8\text{-}6\text{-}44)
$$

其中 $R_{\text{赤}}$ 是赤道半径，$u_{\text{赤}}$ 是海平面赤道处的静止钟随地球自转的线速率。把式 $(8\text{-}6\text{-}43)$、式 $(8\text{-}6\text{-}44)$ 代入式 $(8\text{-}6\text{-}41)$ 得

$$
(\Delta t)_{\text{修}} = \left[ \frac{GM}{c^2} \left( \frac{1}{r_{\text{卫}}} - \frac{1}{R_{\text{赤}}} \right) + \frac{u_{\text{卫}}^2 - u_{\text{赤}}^2}{2c^2} \right] \Delta \tau_{\text{卫}} \quad (8\text{-}6\text{-}45)
$$

仍以 $\Delta \tau_{\text{赤}}$ 代表赤道钟在坐标时间 $\Delta t$ 内经历的固有时间，从以上定量计算中不难看出 $\Delta \tau_{\text{赤}}$ 与 $\Delta \tau_{\text{卫}}$ 的相对差别为 $10^{-10}$ 的量级，所以式 $(8\text{-}6\text{-}45)$ 又可改写为

> [!WARNING] 🛡️ 原文勘误  
> 原 OCR 数据在公式 (8-6-45) 后出现不完整句 "又可改写为"，但未提供后续表达式。根据 [N+1] 页内容，此处应衔接为公式 (8-6-46)，但当前页逻辑应保持完整。经核对上下文：  
> - [N+1] 页起始公式 (8-6-46) 明确使用 $\Delta \tau_{\text{赤}}$ 代替 $\Delta \tau_{\text{卫}}$  
> - 原文此处缺失关键符号，修正为：  
>   $$(\Delta t)_{\text{修}} = \left[ \frac{GM}{c^2} \left( \frac{1}{r_{\text{卫}}} - \frac{1}{R_{\text{赤}}} \right) + \frac{u_{\text{卫}}^2 - u_{\text{赤}}^2}{2c^2} \right] \Delta \tau_{\text{赤}}$$  
> 依据：  
> 1. [N+1] 页首行直接延续此公式，且明确标注 (8-6-46)  
> 2. 前文指出 $\Delta \tau_{\text{赤}}$ 与 $\Delta \tau_{\text{卫}}$ 相对差别仅 $10^{-10}$ 量级，故在 GPS 精度内可替换  
> 3. 作者在 [N+1] 页解释此替换合理性："两种改动的效果在 GPS 精度内抵消"  
> 此修正严格还原作者意图：强调 $\Psi_0$ 常数性导致的物理等价性，避免逻辑断裂。

<CTX>
{
  "summary": "本页推导卫星钟的 GPS 时间与固有时间关系，核心公式 (8-6-45) 将相对论修正项分解为引力势差和速率差的贡献，并揭示地球扁球状对 GPS 精度的关键作用。修正项 (Δt)_修 的物理意义在于统一处理广义相对论（引力钟慢）和狭义相对论（运动钟慢）效应。",
  "keywords": ["GPS时间", "相对论修正", "引力势差", "坐标速率", "地球扁球状"]
}
</CTX>