# Slide 97

§4.5 用几何语言导出洛伦兹变换[选读]

$$ \mathrm{d}\tau = \sqrt{-\mathrm{d}s^2} = \sqrt{\mathrm{d}t^2 - \mathrm{d}x^2} = \mathrm{d}t $$

选 $q$ 点为 $\tau$ 的零点（选 $\tau_q = 0$），则 G 线有 $\tau = t$，故式(4-5-3)可改写为
$$ \tau_a = t_p - x_p \quad (4-5-4a) $$

类似地，以 $b$ 代表 B 线与 G 线的交点，注意到 B 线的斜率为 $-1$，又有
$$ \tau_b = t_p + x_p \quad (4-5-4b) $$

由上两式易得
$$ t_p = (\tau_b + \tau_a)/2, \quad x_p = (\tau_b - \tau_a)/2 \quad (4-5-5a) $$

若改用 $\{t', x'\}$ 系为基准画时空图，则光子世界线 A 和 B 仍是斜率为 $\pm 1$ 的直线。以 $a'$ 和 $b'$ 分别代表 A 线和 B 线与 G' 线的交点，以 $\tau'$ 代表 G' 线的固有时（选 $q$ 为零点，即 $\tau'_q = 0$），仿照前面的推导又得
$$ t'_p = (\tau'_{b'} + \tau'_{a'})/2, \quad x'_p = (\tau'_{b'} - \tau'_{a'})/2 \quad (4-5-5b) $$

如果能再证明（稍后将补证）
$$ \text{(a) } \tau'_{a'} = \tau_a / \gamma(1 - v), \quad \text{(b) } \tau'_{b'} = \tau_b / \gamma(1 + v) \quad (4-5-6) $$
代入式(4-5-5b)便得待证等式(4-5-2)：
$$ t'_p = \frac{1}{2} \left[ \frac{\tau_b}{\gamma(1+v)} + \frac{\tau_a}{\gamma(1-v)} \right] = \frac{1}{\gamma} \frac{1}{1-v^2} \left[ \frac{1}{2} (\tau_b + \tau_a) - \frac{1}{2} v (\tau_b - \tau_a) \right] = \gamma (t_p - v x_p) \quad (4-5-7a) $$
$$ x'_p = \frac{1}{2} \left[ \frac{\tau_b}{\gamma(1+v)} - \frac{\tau_a}{\gamma(1-v)} \right] = \frac{1}{\gamma} \frac{1}{1-v^2} \left[ \frac{1}{2} (\tau_b - \tau_a) - \frac{1}{2} v (\tau_b + \tau_a) \right] = \gamma (x_p - v t_p) \quad (4-5-7b) $$

其中末步用到式(4-5-5a)以及 $\gamma \equiv 1 / \sqrt{1 - v^2}$。

下面补证式(4-5-6)。G' 线的 $a'q$ 段的线长等于
$$ \tau'_q - \tau'_{a'} = \int_{a'}^q \sqrt{-\mathrm{d}s^2} $$

线长是几何量（绝对量），可借任一坐标系计算。借 $\{t, x\}$ 系的计算给出
$$ \tau'_q - \tau'_{a'} = \int_{a'}^q \sqrt{\mathrm{d}t^2 - \mathrm{d}x^2} = \int_{a'}^q \sqrt{\mathrm{d}t^2 - (v \mathrm{d}t)^2} = \sqrt{1 - v^2} \ (t_q - t_{a'}) $$

其中第二步是因为 G' 线满足 $t = v^{-1} x$。利用 $t_q = 0$ 及 $\tau'_q = 0$ 便得
$$ \tau'_{a'} = \sqrt{1 - v^2} \ t_{a'} = \gamma^{-1} t_{a'} \quad (4-5-8) $$

$a$ 及 $a'$ 都在 A 线上，由 A 线的"两点式"得
$$ t_a = t_{a'} - (x_{a'} - x_a) = t_{a'} - v t_{a'} = (1 - v) t_{a'} $$

其中第二步用到 $x_{a'} = v t_{a'}$ 及 $x_a = 0$。再代回式(4-5-8)，利用 $t_a = \tau_a$ 便得待证式(4-5-6a)。

> [!NOTE] 🖼️ Figure 描述
> 二维闵氏时空图，垂直轴为时间 $t$，水平轴为空间 $x$。包含：
> - G线：垂直实线（$x=0$），代表静止惯性系原点世界线
> - G'线：从原点q向右上方倾斜的实线（斜率 $>1$，满足 $t = v^{-1}x$）
> - A线：斜率为 $+1$ 的实线（45°向上），代表正斜率光子世界线
> - B线：斜率为 $-1$ 的实线（45°向下），代表负斜率光子世界线
> - 关键点：$q$（原点）、$a$（A线与G线交点）、$b$（B线与G线交点）、$a'$（A线与G'线交点）、$b'$（B线与G'线交点）、$p$（A线与B线交点）
> - 所有线条均为实线，无箭头但隐含时间向上方向

> [!WARNING] 🛡️ 原文勘误
> 1. 原文"$$ \mathrm{d}\tau = \sqrt{-\mathrm{d}s^2} = \sqrt{\mathrm{d}t^2 - \mathrm{d}x^2} = \mathrm{d}t $$" 中最后等号应为近似，但根据上下文（类时曲线）且 $x$ 方向运动，实际应为 $\mathrm{d}\tau = \sqrt{\mathrm{d}t^2 - \mathrm{d}x^2}$，此处保留原公式因后文推导正确。
> 2. 原文"便得待证"不完整，根据 N+1 页内容补全为"便得待证式(4-5-6a)"，符合逻辑流向。

<CTX>
{ "summary": "本页继续§4.5洛伦兹变换的几何推导，通过固有时参数化证明关键关系式(4-5-6)，最终导出洛伦兹变换公式。核心是利用光子世界线（斜率±1）与惯性观者世界线的交点建立时空坐标转换。", "keywords": ["洛伦兹变换", "闵氏几何", "固有时", "光子世界线", "时空图"] }
</CTX>