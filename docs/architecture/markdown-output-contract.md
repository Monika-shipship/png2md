# Markdown 输出契约

## 用户可见产物

最终用户主要使用：

```text
markdown_output/{doc_name}/
  Slide_01.md
  Slide_02.md
  {doc_name}_FULL.md
```

内部审计和排错材料：

```text
run_report.json
assets/
  crops/
  pages/
ir/
mineru_raw/
cache/
```

IR、report、缓存、原始模型响应都不是最终阅读产物。

## 页面 Markdown

每个页面必须以固定标题开始：

```markdown
# Slide N
```

正文标题从 `##` 开始。不得把内部 JSON、validator 诊断、coverage 解释、API 错误堆栈或模型思考过程写入正文。

## 图示输出

图示必须优先保留 MinerU crop 图片，路径使用输出目录内相对路径：

```markdown
![page 1 figure 3](assets/crops/page_001_p0001_b003_xxx.jpg)

<details>
<summary>图示识别内容</summary>

- 类型：coordinate_plot
- 说明：...
- 可见标签：...
- 主要关系：...
- 不确定点：...

</details>
```

图示说明默认折叠，避免大段解释污染正文。为兼容 Typora，`<details>` 和 `<summary>` 必须分行，且不要加 `open` 属性。视觉模型不能确定时，仍保留图片，折叠内容写明“不确定”，不得编造标签。

## 公式输出

公式要优先可复制、可渲染。`aligned` 内不得放 `\tag{}`：

```markdown
$$
\begin{aligned}
...
\end{aligned}
\tag{3}
$$
```

必须检测：

- `$`、`$$`、`\[`、`\]` 配对。
- `{}`、`()`, `[]` 基础平衡。
- `\left...\right` 基础平衡。
- `aligned`、`array`、`cases` 闭合。
- 重复 tag、嵌套 tag、`\tag{\tag{3}}`。

无法安全修复时，保留原始公式或 crop 证据，详细原因写入 `run_report.json`。

正文 text/paragraph block 中如果混有公式，也必须转成 LaTeX 片段。最终 Markdown 不应保留裸 Unicode 数学符号，例如 `φ`、`θ`、`ω`、`α`、`β`、`≤`、`≥`、`→`；应写成 `$\phi$`、`$\theta$`、`$\omega$`、`$\alpha$`、`$\beta$`、`$\leq$`、`$\geq$`、`$\to$` 等可渲染形式。validator 会对数学分隔符外的裸 Unicode 数学符号产生 `unicode_math_symbol_outside_latex` warning。

## 表格输出

表格宁可保守，不输出看似整齐但错列的假表格。

- 可靠 Markdown table：正常输出。
- 可靠 HTML table：保留 HTML 或转稳定 Markdown。
- aligned text：通过结构检查后转 Markdown。
- 不可靠表格：保留 crop 或 raw fenced text，原因写入 report。

表格标题被识别成独立段落时，应通过受限 refiner 挂到表格 block，而不是丢失。

## 失败页

失败页保持最小可读，不输出堆栈：

```markdown
# Slide 7

> 本页识别失败，已保留页面图片供查看。

![Page 7](assets/pages/page_007.png)
```

详细失败原因只写入 `run_report.json`。

## FULL 合并

`{doc_name}_FULL.md` 不得静默跳过失败页。成功页和 fail-open 页可以合并；失败页必须保留最小提示或在 report 中明确说明未合并原因。

## 禁止写入正文的内容

- 模型思考过程。
- API 错误详情。
- Python 堆栈。
- validator 明细。
- OCR 覆盖率解释。
- 内部 JSON。
- cache hit/miss 明细。

这些内容只能进入 `run_report.json`、`.meta.json`、`.error.json` 或日志。
