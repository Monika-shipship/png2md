# Slide 50

# 薛定谔方程-方程的建立

另：

$$ \mathbf{p} \cdot \mathbf{r} = (p_x \hat{\mathbf{i}} + p_y \hat{\mathbf{j}} + p_z \hat{\mathbf{k}}) \cdot (x \hat{\mathbf{i}} + y \hat{\mathbf{j}} + z \hat{\mathbf{k}}) = x p_x + y p_y + z p_z $$

有：

$$ \frac{\partial^2 \psi}{\partial x^2} = \frac{\partial}{\partial x} \left[ \frac{i}{\hbar} p_x \psi_0 \exp \frac{i}{\hbar} (\mathbf{p} \cdot \mathbf{r} - Et) \right] = \frac{\partial}{\partial x} \left[ \frac{i p_x}{\hbar} \psi \right] = \left( \frac{i p_x}{\hbar} \right)^2 \psi = -\frac{p_x^2}{\hbar^2} \psi $$

同理，有：

$$ \frac{\partial^2 \psi}{\partial y^2} = -\frac{p_y^2}{\hbar^2} \psi \quad \frac{\partial^2 \psi}{\partial z^2} = -\frac{p_z^2}{\hbar^2} \psi $$

于是：

$$ \frac{\partial^2 \psi}{\partial x^2} + \frac{\partial^2 \psi}{\partial y^2} + \frac{\partial^2 \psi}{\partial z^2} = -\frac{p_x^2 + p_y^2 + p_z^2}{\hbar^2} \psi = -\frac{p^2}{\hbar^2} \psi $$

即：

$$ \nabla^2 \psi = -\frac{p^2}{\hbar^2} \psi $$

## Figure & Layout Description
该幻灯片为纯白色背景的学术型PPT页面。顶部有黑色加粗标题"薛定谔方程-方程的建立"，标题下方有一条深灰色细横线作为分隔。正文内容采用黑色标准字体，按逻辑推导顺序垂直排列，分为"另："、"有："、"同理，有："、"于是："、"即："五个推导阶段。每个阶段包含数学公式，公式使用标准LaTeX排版，符号清晰规范，包括向量符号（$\hat{\mathbf{i}}, \hat{\mathbf{j}}, \hat{\mathbf{k}}$）、偏导符号（$\partial$）、拉普拉斯算符（$\nabla^2$）和约化普朗克常数（$\hbar$）。公式与文字说明交替出现，关键推导步骤用等号连接展示演算过程。整体布局简洁严谨，符合物理学术推导的规范排版，无多余装饰元素。

<CTX>
{
   "topic": "薛定谔方程空间部分的推导",
   "keywords": ["薛定谔方程", "自由粒子", "平面单色波", "波函数", "拉普拉斯算符", "动量算符", "ħ", "∇²"],
   "summary": "通过自由粒子平面波函数的二阶空间偏导数推导出空间部分薛定谔方程，建立拉普拉斯算符与动量平方算符的对应关系",
   "pending_concepts": ["时间部分的推导过程", "势场中粒子的完整方程形式", "算符化过程的物理本质", "方程与经典力学的对应原理"]
}
</CTX>