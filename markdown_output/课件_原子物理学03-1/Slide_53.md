# Slide 53

# 薛定谔方程-概率流密度和概率守恒

设粒子的波函数为：$\psi(\mathbf{r}, t)$，则粒子在空间 $\mathbf{r}$ 处的概率密度为  
$$\rho(\mathbf{r}, t) = |\psi(\mathbf{r}, t)|^2 = \psi^*(\mathbf{r}, t)\psi(\mathbf{r}, t)$$

对时间求导  
$$\frac{\partial \rho(\mathbf{r}, t)}{\partial t} = \frac{\partial \psi^*}{\partial t}\psi + \psi^*\frac{\partial \psi}{\partial t}$$

由薛定谔方程得  
$$\frac{\partial \psi}{\partial t} = \frac{1}{i\hbar}\left[-\frac{\hbar^2}{2m}\nabla^2 + V(\mathbf{r}, t)\right]\psi$$  
$$\frac{\partial \psi^*}{\partial t} = -\frac{1}{i\hbar}\left[-\frac{\hbar^2}{2m}\nabla^2 + V(\mathbf{r}, t)\right]\psi^*$$  

$$\frac{\partial \rho}{\partial t} = -\nabla \cdot \left[\frac{\hbar}{2mi}\left(\psi^*\nabla\psi - \psi\nabla\psi^*\right)\right]$$

## Figure & Layout Description

页面顶部为黑色粗体一级标题"薛定谔方程-概率流密度和概率守恒"，标题下方有一条深蓝色水平分割线（长度约页面宽度的95%）。正文内容采用黑色标准字体，分为四个逻辑段落：  
1. 第一段文字说明波函数与概率密度的关系，其下方居中排列概率密度定义公式  
2. 第二段"对时间求导"文字说明后接时间导数公式  
3. 第三段"由薛定谔方程得"引导两个共轭薛定谔方程的时间导数表达式  
4. 最终公式左侧有一个蓝色右向箭头（填充色#1E88E5，宽度约3cm，高度约1.5cm）指向连续性方程  

所有数学公式均居中显示，使用标准数学字体。页面背景为纯白色，无其他装饰元素。公式中向量符号$\mathbf{r}$使用粗体表示，复共轭符号$^*$位于波函数右上角，拉普拉斯算符$\nabla^2$清晰显示。

<CTX>
{
   "topic": "薛定谔方程的概率流密度与概率守恒",
   "keywords": ["薛定谔方程", "概率密度", "概率流密度", "概率守恒", "连续性方程", "波函数共轭", "拉普拉斯算符", "概率流矢量"],
   "summary": "通过波函数时间导数推导出概率密度的时间演化方程，揭示量子力学中概率守恒的连续性方程形式",
   "pending_concepts": ["概率流密度的物理意义", "与经典流体力学连续性方程的类比", "概率流矢量的物理诠释"]
}
</CTX>