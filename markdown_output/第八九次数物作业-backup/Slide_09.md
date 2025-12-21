# Slide 9

但由于 $u_2 = a_3 = 0$，后两组解 $k = 3m+2, 3m+3$ 都为 $0$.

对第一组解为 $k = 3m+1$，$(k+2)(k+3)a_{k+3} - ka_k = 0 \ (k \geq 1)$

$$
a_{k+3} = \frac{k}{(k+2)(k+3)} a_k \quad (k \geq 1)
$$

$$
a_4 = \frac{1}{3 \cdot 4} a_1
$$

$$
a_7 = \frac{4}{6 \cdot 7} a_4 = \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 7} = \frac{1}{3^2 \cdot 1 \cdot 2 \cdot 7}
$$

$$
a_{10} = \frac{7}{9 \cdot 10} a_7 = \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 10} = \frac{1}{3^3 \cdot 1 \cdot 2 \cdot 3 \cdot 10}
$$

$$
a_{13} = \frac{10}{12 \cdot 13} a_{10} = \frac{10}{12 \cdot 13} \cdot \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 12 \cdot 13} = \frac{1}{3^4 \cdot 1 \cdot 2 \cdot 3 \cdot 4 \cdot 13}
$$

$$
a_{16} = \frac{13}{15 \cdot 16} a_{13} = \frac{13}{15 \cdot 16} \cdot \frac{10}{12 \cdot 13} \cdot \frac{7}{9 \cdot 10} \cdot \frac{4}{6 \cdot 7} \cdot \frac{1}{3 \cdot 4} a_1 = \frac{1}{3 \cdot 6 \cdot 9 \cdot 12 \cdot 15 \cdot 16} = \frac{1}{3^5 \cdot 1 \cdot 2 \cdot 3 \cdot 4 \cdot 5 \cdot 16}
$$

$$
a_{3m+1} = \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1
$$

$$
y_1 = \sum_{m=0}^{\infty} \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1 x^{3m+1}
$$

$$
y_2 = a_0
$$

$$
y = y_1 + y_2 = a_0 + \sum_{m=0}^{\infty} \frac{1}{3^m \cdot m! \cdot (3m+1)!} a_1 x^{3m+1}
$$

## Figure & Layout Description

手写内容呈现在方格纸背景上，整体为竖向排列的数学推导过程。顶部有结论性语句，中间部分为递推关系的逐步推导，底部为通解表达式。文字和公式全部为黑色手写体，部分中间推导步骤中的错误计算项被红色笔迹划掉（如 $a_7$、$a_{10}$、$a_{13}$、$a_{16}$ 推导中的中间系数）。公式结构清晰，分步骤展示从 $a_4$ 到 $a_{16}$ 的递推过程，每行公式对齐整齐。关键递推关系 $(k+2)(k+3)a_{k+3} - ka_k = 0$ 以较大字体书写，作为推导核心。最后归纳出通项公式 $a_{3m+1}$ 和级数解 $y_1$、$y_2$，并给出完整通解表达式。红色划线部分显示了计算过程中的修正痕迹，体现推导的动态过程。

<CTX>
{
   "topic": "二阶线性微分方程幂级数解的通解构造：第一组解的显式表达式推导",
   "keywords": ["系数递推关系", "三组解结构", "通解构造", "项重组技巧", "显式表达式"],
   "summary": "本页完成第一组非零解的递推关系求解，通过归纳法得到显式通项公式并构造出完整通解形式",
   "pending_concepts": ["解的收敛半径具体计算", "非整数指数幂级数解的处理方法", "三组解中零解的严格证明"]
}
</CTX>