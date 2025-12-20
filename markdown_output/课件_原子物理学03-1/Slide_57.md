# Slide 57

# 薛定谔方程-定态薛定谔方程

假设粒子所处的**外场 $V(\mathbf{r})$**不随时间改变。

例如：在(类)氢原子中，电子所在的库仑场

$$ V(r) = -\frac{Ze^2}{4\pi\varepsilon_0 r} $$

$$ i\hbar \frac{\partial \psi}{\partial t} = \left[ -\frac{\hbar^2}{2m} \nabla^2 + V(\mathbf{r}) \right] \psi $$

分离变量 $\psi(\mathbf{r},t) = u(\mathbf{r}) f(t)$

两边同除以 $\psi(\mathbf{r},t)$，得

$$ \frac{i\hbar}{f(t)} \frac{df}{dt} = \frac{1}{u(\mathbf{r})} \left( -\frac{\hbar^2}{2m} \nabla^2 + V(\mathbf{r}) \right) u(\mathbf{r}) = \text{cons.} \quad \text{设为} E $$

则有

$$
\begin{cases}
\displaystyle \frac{i\hbar}{f(t)} \frac{df}{dt} = E \\
\displaystyle \frac{1}{u(\mathbf{r})} \left( -\frac{\hbar^2}{2m} \nabla^2 + V(\mathbf{r}) \right) u(\mathbf{r}) = E
\end{cases}
$$

## Figure & Layout Description

页面顶部是黑色粗体标题"薛定谔方程-定态薛定谔方程"，下方有一条深灰色水平分割线。正文区域分为左右两部分：左侧为文字和公式内容，右侧为原子结构示意图。文字部分中"外场 $V(\mathbf{r})$"以红色字体突出显示。原子结构示意图包含一个蓝色圆形轨道，轨道中心有一个红色实心圆点代表原子核，标注红色文字"+Ze, M"；轨道边缘标注红色文字"-e, $m_e$"。所有公式均采用标准数学排版，其中薛定谔方程和分离变量后的方程组使用行间公式格式。文字内容从上到下依次为假设条件、类氢原子示例、原始薛定谔方程、分离变量过程及最终得到的两个定态方程。页面整体采用白底黑字配色方案，关键物理量和假设条件用红色强调。

<CTX>
{
   "topic": "定态薛定谔方程",
   "keywords": ["薛定谔方程", "定态", "分离变量法", "库仑场", "类氢原子", "能量本征值"],
   "summary": "推导定态薛定谔方程的分离变量解法，建立时间部分与空间部分的独立方程体系",
   "pending_concepts": ["定态波函数的具体求解步骤", "能级与量子数的对应关系", "空间方程的边界条件应用", "能量本征值的物理意义"]
}
</CTX>