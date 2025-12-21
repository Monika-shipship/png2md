# Slide 28

$$
\partial_x G(x,t) = -\frac{1}{2} \frac{2x - 2t}{(1 + x^2 - 2xt)^{\frac{3}{2}}} = \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
-(x - t) \cdot G^3 = \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
(x - t) \cdot G_T = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_l(t) \cdot l x^{l-1}
$$

$$
(x - t) \sum_{l=0}^{\infty} P_l(t) \cdot x^l = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^l \quad \text{（右侧标注：$l \to l+1$）}
$$

$$
\sum_{l=0}^{\infty} P_l(t) \cdot x^{l+1} - \sum_{l=0}^{\infty} t P_l(t) \cdot x^l = \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^l
$$

（橙色波浪线标注：$l \to l-1$）

$$
- \sum_{l=0}^{\infty} 2t P_{l+1}(t)(l+1) x^{l+1} \quad \text{（蓝色下划线标注：$l \to l-1$）}
$$

$$
+ \sum_{l=0}^{\infty} P_{l+1}(t)(l+1) x^{l+2} \quad \text{（红色波浪线标注：$l \to l-2$）}
$$

$$
\text{有} \sum_{l=1}^{\infty} \left( P_{l-1}(t) - t P_l(t) \right) x^l = \sum_{l=1}^{\infty} \left[ P_{l+1}(t)(l+1) - 2t P_l(t) l + P_{l-1}(t)(l-1) \right] x^l
$$

$$
P_{l-1}(t) - t P_l(t) = P_{l+1}(t)(l+1) - 2t P_l(t) l + P_{l-1}(t)(l-1)
$$

（左侧蓝色三角标记，中间橙色波浪线，右侧蓝色箭头）

$$
\boxed{t(2l+1)P_l = (l+1)P_{l+1} + l P_{l-1}} \quad \text{（红色方框标注，右侧红色圆圈①）}
$$

$$
G(x,t) = \frac{1}{\sqrt{1 + x^2 - 2xt}} = \sum_{l=0}^{\infty} P_l(t) \cdot x^l
$$

$$
\partial_t G(x,t) = -\frac{1}{2} \frac{-2x}{(1 + x^2 - 2xt)^{\frac{3}{2}}} = \sum_{l=0}^{\infty} P_l'(t) \cdot x^l
$$

$$
x G_T = (1 + x^2 - 2xt) \sum_{l=0}^{\infty} P_l'(t) \cdot x^l
$$

## Figure & Layout Description

图片背景为标准方格纸，所有内容以黑色手写体垂直排列。公式按逻辑推导顺序自上而下分布，关键步骤通过彩色标记强化：

1. **顶部区域**：包含三个连续的偏微分方程推导，右侧有逗号分隔符和手写注释"l→l+1"（黑色墨水）。
2. **中部区域**：
   - 橙色波浪线横跨第一个求和式下方，标注"l→l-1"（橙色墨水）。
   - 蓝色下划线标记第二个求和项，右侧标注"l→l-1"（蓝色墨水）。
   - 红色波浪线标记第三个求和项，右侧标注"l→l-2"（红色墨水）。
   - 核心递推关系被红色实线方框包围，左侧有蓝色三角标记，右侧有红色圆圈内标"①"。
3. **底部区域**：包含生成函数定义和时间偏导推导，字体稍小但清晰。
4. **颜色系统**：橙色用于指标变换说明，蓝色用于中间推导步骤强调，红色用于关键结论和最终公式标注。所有手写公式保持数学符号的连贯性，部分下标（如$P_{l+1}$）通过上下位置区分。

## Context Update

<CTX>
{
   "topic": "勒让德多项式递推关系的生成函数推导",
   "keywords": ["勒让德多项式", "生成函数", "递推关系", "指标变换", "系数对比"],
   "summary": "通过生成函数微分与级数展开推导出勒让德多项式的三阶递推关系，完成正交性证明的关键中间步骤",
   "pending_concepts": ["生成函数在物理场论中的具体应用", "奇偶性与球谐函数的关联"]
}
</CTX>