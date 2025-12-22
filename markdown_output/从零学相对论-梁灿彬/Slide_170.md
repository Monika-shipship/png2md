 
# Slide 170

可以证明（直观上也不难相信），图8-1中$a,b$之间的径向线$\gamma$正是测地线，所以$\gamma$的线长$l_{ab}$就是$a,b$之间的距离。由线长公式(2-2-3)得
\begin{equation}
a,b\text{ 的距离 } = l_{ab} = \int_a^b \sqrt{\mathrm{d}\hat{s}^2|_\gamma} \,,
\tag{8-1-4}
\end{equation}
把式(8-1-3)用于$\gamma$的任一元段，注意到$\gamma$线上有$\theta=\text{常数}$及$\varphi=\text{常数}$（因而$\mathrm{d}\theta=0,\mathrm{d}\varphi=0$），便得
\begin{equation}
\mathrm{d}\hat{s}^2|_\gamma = \left(1 - \frac{2M}{r}\right)^{-1} \mathrm{d}r^2 \,,
\tag{8-1-5}
\end{equation}
代入式(8-1-4)给出
\begin{equation}
a,b\text{ 的距离 } = l_{ab} = \int_a^b \left(1 - \frac{2M}{r}\right)^{-1/2} \mathrm{d}r > r_B - r_A \,.
\quad (\text{除非 } M = 0)
\tag{8-1-6}
\end{equation}
可见$a,b$的距离大于$a,b$的径向坐标差（亦称坐标距离）$r_B - r_A$，除非$M=0$。（当$M=0$时$l_{ab} = r_B - r_A$，这正是人们熟知的欧氏情况。）为了强调与坐标距离的区别，也常把距离$l_{ab}$称为固有距离（proper distance）。固有距离不等于坐标距离是空间弯曲性的重要表现。物理上更应重视的是固有距离而不是坐标距离。

**注记1** 在欧氏空间中，球面的半径$r$有两个性质：①等于球面与球心的距离；②与球面积$A$的关系为$A=4\pi r^2$，即$r=\sqrt{A/4\pi}$。但在弯曲空间中这两个性质互不等价：若以$r$代表球面与球心的距离，则$r=\sqrt{A/4\pi}$不再成立。一种方便的做法是用球面积定义半径，即把半径定义为$\sqrt{A/4\pi}$，代价是半径不再等于球面与球心的距离。这就是“径向坐标距离$r_B - r_A$不等于固有距离”的原因。

与此类似，在史瓦西时空中还应分清坐标时间$\Delta t$和固有时间$\Delta \tau$。设$\Sigma_{\hat{t}}$是另一张等$t$面，我们来关心静态观者$A,B$的世界线上介于$\Sigma_{\hat{t}}$和$\Sigma_{\hat{t}'}$之间的两条线段，分别记作$\mu_A$和$\mu_B$，见图8-2。以$\Delta t_A$和$\Delta t_B$分别代表两段所经历的坐标时间，因$\Sigma_{\hat{t}}$和$\Sigma_{\hat{t}'}$都是等$t$面，当然有
\begin{equation}
\Delta t_A = \hat{t}' - \hat{t} = \Delta t_B \,.
\tag{8-1-7}
\end{equation}
问题在于这两段所经历的固有时间$\Delta \tau_A$和$\Delta \tau_B$是否也相同。注意到$r,\theta,\varphi$在每条线上都是常数，把式(8-1-1)用于每条线的任一元段得

> [!NOTE] 🖼️ Figure 描述  
> 二维物理示意图：左侧为垂直圆柱体（代表天体表面），右侧有两个平行水平平面（下方标注$\Sigma_{\hat{t}}$，上方标注$\Sigma_{\hat{t}'}$）。两条竖直细实线贯穿平面：左侧线标记为$A$（世界线），右侧线标记为$B$（世界线）。两线间区域中，$A$线上介于平面之间的线段标注为$\mu_A$，$B$线上对应线段标注为$\mu_B$。所有标签为黑色文字，无线条箭头。图注："图8-2 静态观者世界线介于两个等$t$面之间的两段有不同固有时间"。

> [!WARNING] 🛡️ 原文勘误  
> 1. 原OCR中"Σ_{\hat{τ}}"应为"Σ_{\hat{t}'}"：固有时符号$\tau$与坐标时$t$混淆，前文[P-1]及后文[N+1]均用$\hat{t}$表示坐标时刻（如$\Sigma_{\hat{t}}$），此处"τ"系OCR识别错误。  
> 2. 原公式中"d\hat{s}^2"和"dr"统一修正为"\mathrm{d}\hat{s}^2"和"\mathrm{d}r"：前文[P-1]式(8-1-3)使用\mathrm{d}规范微分符号，需保持全文一致性。  
> 3. 原"r=√(A/4π)"修正为"r=\sqrt{A/4\pi}"：√符号应转为LaTeX \sqrt{}，且$\pi$需用斜体。

<CTX>
{ "summary": "本页推导史瓦西时空中静态观者间固有距离的计算公式，揭示坐标距离与固有距离的差异，并引入坐标时间与固有时间的区分，为后续固有时间计算做铺垫", "keywords": ["固有距离", "坐标距离", "静态观者", "等t面", "弯曲空间"] }
</CTX>