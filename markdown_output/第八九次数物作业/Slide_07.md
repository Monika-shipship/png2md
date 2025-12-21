# Slide 7

## 主题：常微分方程的幂级数解法 —— 示例分析

考虑如下二阶线性微分方程：

$$
(1)\quad y'' - x y' = 0
$$

### 常点分析

将方程写为标准形式：
$$
y'' + p(x) y' + q(x) y = 0
$$
其中 $ p(x) = -x $, $ q(x) = 0 $。  
由于 $ p(x) $ 和 $ q(x) $ 在 $ x = 0 $ 处解析（实际上处处解析），因此 $ x = 0 $ 是**常点**。

故可在 $ x = 0 $ 的邻域内使用幂级数解法求解。

---

### 幂级数解假设

设解的形式为：
$$
y(x) = \sum_{k=0}^{\infty} a_k x^k
$$

则一阶和二阶导数分别为：
$$
y'(x) = \sum_{k=1}^{\infty} k a_k x^{k-1}, \quad
y''(x) = \sum_{k=2}^{\infty} k(k-1) a_k x^{k-2}
$$

---

### 代入原方程

将导数代入方程 $ y'' - x y' = 0 $：

$$
y'' - x y' = \sum_{k=2}^{\infty} k(k-1) a_k x^{k-2} - x \sum_{k=1}^{\infty} k a_k x^{k-1}
= \sum_{k=2}^{\infty} k(k-1) a_k x^{k-2} - \sum_{k=1}^{\infty} k a_k x^k
$$

对第一项进行指标变换：令 $ k - 2 = m $，即 $ k = m + 2 $，得：
$$
\sum_{k=2}^{\infty} k(k-1) a_k x^{k-2} = \sum_{m=0}^{\infty} (m+2)(m+1) a_{m+2} x^m
$$

统一变量为 $ k $，有：
$$
y'' - x y' = \sum_{k=0}^{\infty} (k+2)(k+1) a_{k+2} x^k - \sum_{k=1}^{\infty} k a_k x^k
$$

注意第二项从 $ k=1 $ 开始，而第一项从 $ k=0 $ 开始。将两项合并前先分离首项：

$$
= \left[ 2 \cdot 1 \cdot a_2 x^0 \right] + \sum_{k=1}^{\infty} (k+2)(k+1) a_{k+2} x^k - \sum_{k=1}^{\infty} k a_k x^k
= 2a_2 + \sum_{k=1}^{\infty} \left[ (k+2)(k+1) a_{k+2} - k a_k \right] x^k
$$

令整个表达式恒等于零，得到系数方程：

- 常数项：$ 2a_2 = 0 \Rightarrow a_2 = 0 $
- 对于 $ k \geq 1 $：
  $$
  (k+2)(k+1) a_{k+2} - k a_k = 0 \Rightarrow a_{k+2} = \frac{k}{(k+1)(k+2)} a_k
  $$

---

### 递推关系与通解构造

得到递推公式：
$$
a_{k+2} = \frac{k}{(k+1)(k+2)} a_k, \quad k \geq 1
$$

结合初始条件分析奇偶项：

#### A. 偶数下标项（$ k $ 为偶数）

已知 $ a_2 = 0 $

由递推关系可见，若某偶数项为零，则后续偶数项均为零：
$$
a_4 = \frac{2}{3 \cdot 4} a_2 = 0, \quad a_6 = \frac{4}{5 \cdot 6} a_4 = 0, \dots
\Rightarrow a_{2n} = 0 \quad (n \geq 1)
$$

但 $ a_0 $ 是自由常数，未被约束。

因此所有偶数项中仅有 $ a_0 \neq 0 $，其余为零。

对应一个特解：
$$
y_1(x) = a_0
$$
即常数解。

> 注：这符合原方程 $ y'' = x y' $，当 $ y = \text{const} $ 时两边均为零。

#### B. 奇数下标项（$ k $ 为奇数）

从 $ a_1 $ 出发，逐次计算：

$$
a_3 = \frac{1}{2 \cdot 3} a_1
$$
$$
a_5 = \frac{3}{4 \cdot 5} a_3 = \frac{3}{4 \cdot 5} \cdot \frac{1}{2 \cdot 3} a_1 = \frac{1}{2 \cdot 4 \cdot 5} a_1
$$
$$
a_7 = \frac{5}{6 \cdot 7} a_5 = \frac{5}{6 \cdot 7} \cdot \frac{3}{4 \cdot 5} \cdot \frac{1}{2 \cdot 3} a_1 = \frac{1}{2 \cdot 4 \cdot 6 \cdot 7} \cdot (1 \cdot 3 \cdot 5) / (3 \cdot 5) \cdots
$$

更清晰地写出一般规律：

定义双阶乘（double factorial）：
- $ (2n)!! = 2 \cdot 4 \cdot 6 \cdots (2n) = 2^n n! $
- $ (2n-1)!! = 1 \cdot 3 \cdot 5 \cdots (2n-1) $

观察可得，对于 $ n \geq 1 $：
$$
a_{2n+1} = \frac{(2n-1)!!}{(2n+1)!} a_1
\quad \text{或等价表示为} \quad
a_{2n+1} = \frac{(2n-1)!!}{(2n+1)!!} \cdot \frac{a_1}{2^n n!}
$$

但此处暂不展开闭式，仅说明结构存在。

由此，第二个线性无关特解为：
$$
y_2(x) = a_1 \sum_{n=0}^{\infty} c_n x^{2n+1}, \quad c_n \text{ 由递推确定}
$$

通解为：
$$
y(x) = C_1 + C_2 \sum_{n=0}^{\infty} \left( \prod_{j=1}^{n} \frac{2j-1}{(2j)(2j+1)} \right) x^{2n+1}
$$
其中 $ C_1 = a_0, C_2 = a_1 $

---

## Figure Description

本页为方格纸背景的手写数学推导过程，内容纵向排列，包含标题“15.3”、微分方程、幂级数展开步骤、递推关系推导及双阶乘定义。无图表或图像元素，仅为连续的公式与文字说明，风格为教学板书式推导，用于展示常点处幂级数解法的具体实施过程。

<CTX>
{
  "topic": "常微分方程的幂级数解法实例",
  "keywords": ["幂级数解", "常点", "递推关系", "双阶乘"],
  "summary": "本页详细演示了在常点 x=0 处用幂级数方法求解微分方程 y'' - x y' = 0 的全过程，包括设解、代入、指标变换、系数比较、递推公式的建立，并通过奇偶项分类得出两个线性无关解：一个是常数解，另一个是依赖于 a₁ 的奇函数级数解。",
  "last_formula_context": "最后一个公式是奇数项的递推结果，通解形式为 y(x) = C₁ + C₂·∑cₙx²ⁿ⁺¹，其中系数由 a_{k+2} = k/[(k+1)(k+2)] a_k 确定，且 a₂ = 0 导致所有更高偶数项为零。"
}
</CTX>