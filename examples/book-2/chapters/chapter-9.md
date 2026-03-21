# Heading Level 1 (Top Level)

<!-- ## Heading Level 2 (Sub-section) -->

<!-- ### Heading Level 3 (Sub-sub-section) -->

---

<!-- ## 1. Text Formatting -->

You can use **bold**, _italic_, and **_combined_** styles. Pandoc also supports and ^superscript^ or ~subscript~.

> This is a blockquote. It can span multiple lines and contain other elements.
>
> - Even lists inside quotes.

---

<!-- ## 2. Lists -->

<!-- ### Unordered List -->

- Item one
- Item two
  - Nested item
  - Another nested item
- Item three

<!-- ### Ordered List -->

1.  First numbered item
2.  Second numbered item i. Roman numeral sub-item ii. Another sub-item
3.  Third numbered item

<!-- ### Task Lists -->

- [x] Finished task
- [ ] Unfinished task

<!-- ### Definition Lists -->

Term 1 : Definition for term one.

Term 2 : Definition for term two.

---

<!-- ## 3. Tables -->

| Feature   | Support |                     Note |
| :-------- | :-----: | -----------------------: |
| Tables    |   Yes   | Pipe tables are standard |
| Alignment |   Yes   |      Left, Center, Right |
| Multiline | Partial |        Depends on output |

---

<!-- ## 4. Mathematics (LaTeX) -->

Pandoc handles LaTeX math for various outputs (MathJax for HTML, native for PDF).

**Inline Math:** The area of a circle is $A = \pi r^2$.

**Display Math:** $$e^{i\pi} + 1 = 0$$

---

<!-- ## 5. Code Blocks -->

<!-- ### Inline Code -->

Use `backticks` for code inside sentences.

<!-- ### Fenced Code Blocks -->

```python
def hello_world():
    # This is a syntax highlighting test
    print("Hello, Pandoc!")

```
