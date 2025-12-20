# Slide 13

## 黑体辐射与Planck的量子假说-**黑体辐射**

### 能量分布函数  
$E = n\varepsilon$  
$f_n = Ce^{-E_n/k_B T} = Ce^{-n\varepsilon/k_B T}$

### 归一化常数 $C$  
$\sum_{n=0}^{\infty} Ce^{-n\varepsilon/k_B T} = 1 \quad \rightarrow \quad C = 1 - e^{-\varepsilon/k_B T}$

### 振子(振荡模式)的平均能量  
$\varepsilon = h\nu$  
$\bar{E} = \sum_{n=0}^{\infty} E_n f_n = \sum_{n=0}^{\infty} E_n Ce^{-E_n/k_B T} = \frac{h\nu}{e^{h\nu/k_B T} - 1}$

### 能量密度  
$$u(\lambda) = n(\lambda)\bar{E} = 8\pi\lambda^{-4} \frac{hc\lambda^{-1}}{e^{hc/\lambda k_B T} - 1} = \frac{8\pi hc\lambda^{-5}}{e^{hc/\lambda k_B T} - 1}$$

### 经验公式  
$u(\lambda) = \frac{c_1 \lambda^{-5}}{e^{c_2/\lambda} - 1}$

## Figure & Layout Description  
页面顶部为一级标题“黑体辐射与Planck的量子假说-黑体辐射”，其中“黑体辐射”以红色加粗字体显示，其余标题文字为黑色。标题下方有一条灰色水平分割线。内容区域分为五个逻辑区块：  
1. **能量分布函数**区块：左侧为黑色小标题，右侧并列显示公式 $E = n\varepsilon$；主体公式 $f_n = Ce^{-E_n/k_B T} = Ce^{-n\varepsilon/k_B T}$ 居中显示，使用标准数学字体。  
2. **归一化常数 $C$** 区块：左侧为黑色小标题，右侧为求和公式 $\sum_{n=0}^{\infty} Ce^{-n\varepsilon/k_B T} = 1$，其右侧有一个蓝色右向箭头指向结果 $C = 1 - e^{-\varepsilon/k_B T}$。  
3. **振子平均能量**区块：左侧为黑色小标题，右侧顶部标注 $\varepsilon = h\nu$；主体公式 $\bar{E} = \sum_{n=0}^{\infty} E_n f_n = \cdots$ 占据主要区域。  
4. **能量密度**区块：左侧为黑色小标题，主体公式被黄色圆角矩形边框包围，公式内部使用分式结构，分子分母清晰分层。  
5. **经验公式**区块：位于页面底部，左侧为黑色小标题，右侧显示经验公式 $u(\lambda) = \frac{c_1 \lambda^{-5}}{e^{c_2/\lambda} - 1}$。  
整体布局为纵向层级结构，公式与文字说明严格对齐，关键推导步骤通过箭头和颜色框突出显示。

<CTX>
{
   "topic": "黑体辐射的能量分布函数与普朗克量子假说的数学推导",
   "keywords": ["黑体辐射", "普朗克量子假说", "能量量子化", "能量分布函数", "归一化常数", "振子平均能量", "能量密度", "经验公式"],
   "summary": "本页通过能量分布函数、归一化常数、振子平均能量及能量密度公式的严格推导，建立了普朗克量子假说与黑体辐射实验数据的数学联系",
   "pending_concepts": ["能量密度公式的物理意义", "经验公式中参数 $c_1$ 和 $c_2$ 的具体确定方法"]
}
</CTX>