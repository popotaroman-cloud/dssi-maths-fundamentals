# Textbook Reference Notes — Derivative
> เอกสารอ้างอิงภายใน สำหรับเตรียม/ปรับปรุง `week_03_derivatives/notes/note_03.md` และสไลด์ที่เกี่ยวข้อง — ไม่ใช่เอกสารแจกนักศึกษา

---

## ⚠️ หมายเหตุเรื่องลิขสิทธิ์ (สำคัญ — อ่านก่อนใช้)

ไฟล์ PDF ทั้งสามอยู่ใน `textbook/` แต่**สถานะลิขสิทธิ์ต่างกัน**:

| แหล่ง | สถานะ | ใช้อะไรได้บ้าง |
|---|---|---|
| **Calculus Volume 1 (OpenStax)** | CC BY 4.0 — เปิดให้ดัดแปลง/แจกซ้ำได้โดยให้เครดิต | ✅ สรุป/ถอดความ/ดัดแปลงลงในเอกสารคอร์สได้ตามปกติ |
| **Mathematics for Machine Learning** (Deisenroth, Faisal, Ong) | หน้าทุกหน้าระบุชัดเจนว่า **"free to view and download for personal use only. Not for re-distribution, re-sale, or use in derivative works."** | ❌ **ห้ามถอดความ/สรุปลงเอกสารคอร์ส** — อ่านเพื่อเตรียมตัวสอนเองได้เท่านั้น ด้านล่างมีแค่หัวข้อสารบัญ (ข้อเท็จจริง ไม่ติดลิขสิทธิ์) ไม่มีเนื้อหาถอดมา |
| **The Matrix Calculus You Need For Deep Learning** (arXiv 1802.01528) | ไม่พบข้อความอนุญาตสิทธิ์ชัดเจนในตัวเอกสาร | ⚠️ ถือว่ายังไม่ยืนยันสิทธิ์ — ปฏิบัติแบบเดียวกับ MML คือใช้อ่านเตรียมตัวเองเท่านั้น ด้านล่างมีแค่หัวข้อสารบัญ |

**ข้อสรุปสำหรับใช้ปรับปรุง week 3:** เนื้อหาที่นำไปปรับ/เขียนเพิ่มใน `note_03.md` และสไลด์ **อ้างอิงจาก OpenStax เท่านั้น** (ถอดความเป็นภาษาของเราเอง ไม่ใช่คัดลอก) ส่วนสูตร/นิยามทางคณิตศาสตร์ที่เป็นข้อเท็จจริงทั่วไป (เช่น chain rule คืออะไร) ไม่ติดลิขสิทธิ์อยู่แล้วไม่ว่าจะมาจากตำราเล่มไหน

---

## 1. Calculus Volume 1 (OpenStax) — Chapter 3 "Derivatives" (หน้า 194–301 ในไฟล์ PDF)

ใช้สรุป/ถอดความได้เต็มที่ (CC BY 4.0) — สรุปเป็นภาษาของเราเอง ไม่ใช่คำต่อคำจากต้นฉบับ

### 3.1 Defining the Derivative (หน้า 195–202)
- นิยาม derivative ผ่าน difference quotient สองรูปแบบ: $f'(a) = \lim_{h\to0}\frac{f(a+h)-f(a)}{h}$ และ $f'(a) = \lim_{x\to a}\frac{f(x)-f(a)}{x-a}$ — สองรูปแบบนี้เทียบเท่ากัน ต่างกันแค่ตัวแปรที่เข้าใกล้ศูนย์
- tangent line = ค่าลิมิตของ secant line เมื่อจุดที่สองเข้าใกล้จุดแรก
- ตัวอย่างการประมาณ derivative จากตาราง (ก่อนคำนวณจริง) — เทคนิคนี้มีประโยชน์สำหรับสอนสัญชาตญาณก่อนเข้าสูตร
- เชื่อมกับ velocity/rate of change: อัตราเร็วขณะหนึ่ง = derivative ของตำแหน่งเทียบเวลา

### 3.2 The Derivative as a Function (หน้า 210–222)
- derivative เป็นฟังก์ชันใหม่ $f'(x)$ ที่นิยามบนโดเมนย่อยของ $f$
- สัญกรณ์ 4 แบบที่เทียบเท่ากัน: $f'(x)$, $y'$, $\dfrac{dy}{dx}$, $\dfrac{df}{dx}$ (Leibniz notation)
- **Theorem 3.1 (Differentiability ⟹ Continuity):** ต่อเนื่อง ณ จุดหนึ่งเป็นเงื่อนไขจำเป็นของการหาอนุพันธ์ได้ — แต่ไม่ใช่เงื่อนไขพอเพียง (ตัวอย่างค้าน: $|x|$ ต่อเนื่องที่ 0 แต่หาอนุพันธ์ไม่ได้เพราะมีมุมหัก)
- สามเหตุผลหลักที่ทำให้หาอนุพันธ์ไม่ได้ ณ จุดหนึ่ง: (1) มุมหัก/แหลม (2) เส้นสัมผัสแนวตั้ง (3) ความชันแกว่งไม่นิ่ง (เช่น $x\sin(1/x)$)
- higher-order derivatives: $f''$, $f'''$, $f^{(n)}$

### 3.3 Differentiation Rules (หน้า 223–236)
กฎพื้นฐานที่ต้องมีครบในสไลด์ week 3:
- **Constant rule:** $\frac{d}{dx}[c]=0$
- **Power rule:** $\frac{d}{dx}[x^n]=nx^{n-1}$ (ขยายไปเลขชี้กำลังลบได้ด้วย quotient rule)
- **Sum/Difference/Constant-multiple rule:** เชิงเส้นตรงไปตรงมา
- **Product rule:** $(fg)' = f'g+fg'$ — เน้นย้ำว่า **ไม่ใช่** $f'g'$
- **Quotient rule:** $\left(\frac{f}{g}\right)' = \frac{f'g-fg'}{g^2}$
- แนวทางสอน: "combining rules" — ตัวอย่างที่ผสมหลายกฎในสมการเดียว (เช่น sum + product) ควรมีอย่างน้อย 1 ตัวอย่างใน note

### 3.6 The Chain Rule (หน้า 257–265) — **หัวข้อที่ week 3 เน้นหนักที่สุด**
- ที่มาเชิงสัญชาตญาณ: มองเป็น "chain reaction" — $x$ เปลี่ยน → $u=g(x)$ เปลี่ยน → $y=f(u)$ เปลี่ยน
- สูตร: ถ้า $h(x)=f(g(x))$ แล้ว $h'(x)=f'(g(x))\cdot g'(x)$ — เทียบเท่ากับ Leibniz form $\frac{dy}{dx}=\frac{dy}{du}\cdot\frac{du}{dx}$
- **Problem-Solving Strategy 4 ขั้น** (ใช้ได้ดีมากสำหรับสไลด์สอน):
  1. ระบุ outer function $f$ และ inner function $g$
  2. หา $f'$ แล้วแทนค่าด้วย $g(x)$
  3. หา $g'(x)$
  4. คูณสองอย่างเข้าด้วยกัน
- **Power rule for composition:** $\frac{d}{dx}[g(x)]^n = n[g(x)]^{n-1}g'(x)$ — กรณีพิเศษที่ใช้บ่อยที่สุด ควรมีตัวอย่างแยกต่างหาก
- **Chain rule ซ้อนสามชั้น:** $\frac{d}{dx}f(g(h(x))) = f'(g(h(x)))\cdot g'(h(x))\cdot h'(x)$ — ควรมี 1 ตัวอย่างซ้อน 3 ชั้นใน note (สอดคล้องกับที่ week 4 จะขยายเป็น multivariable chain rule ต่อ)
- ข้อควรระวังที่ระบุไว้ชัดเจนในต้นฉบับ: "we never evaluate a derivative at a derivative" — เตือนไม่ให้สับสนลำดับการแทนค่า

### 3.9 Derivatives of Exponential and Logarithmic Functions (หน้า 282–294)
- $\frac{d}{dx}[e^x] = e^x$ (สืบเนื่องจากสมมติฐาน $\lim_{h\to0}\frac{e^h-1}{h}=1$ ซึ่งเป็นนิยามของ $e$)
- $\frac{d}{dx}[e^{g(x)}] = e^{g(x)}g'(x)$ (chain rule + exponential)
- $\frac{d}{dx}[\ln x] = \frac{1}{x}$ พิสูจน์ด้วย implicit differentiation จาก $e^y=x$
- $\frac{d}{dx}[\ln(g(x))] = \frac{g'(x)}{g(x)}$
- เทคนิค **logarithmic differentiation**: ใช้ตัดปัญหาฟังก์ชันซับซ้อน (เช่น $x^x$ หรือผลคูณ/ผลหารยาว ๆ) — อาจเป็นตัวอย่างที่ 3 (แบบ "surprising") ของหัวข้อ chain rule ใน note ได้ เพราะไม่มีใครคาดว่าต้อง log ทั้งสองข้างก่อน

---

## 2. Mathematics for Machine Learning — Chapter 5 "Vector Calculus" (หน้า 144–176 ในไฟล์ PDF)

**ไม่ถอดเนื้อหา** (ดูเหตุผลด้านบน) — มีแค่หัวข้อสารบัญเพื่อให้รู้ว่ามีอะไรอยู่ตรงไหน หากต้องอ่านเองเพื่อเตรียมสอน:

- 5.1 Differentiation of Univariate Functions (รวม Taylor series/polynomial)
- 5.2 Partial Differentiation and Gradients
- 5.3 Gradients of Vector-Valued Functions
- 5.4 Gradients of Matrices
- 5.5 Useful Identities for Computing Gradients
- 5.6 Backpropagation and Automatic Differentiation
- 5.7 Higher-Order Derivatives
- 5.8 Linearization and Multivariate Taylor Series

> เนื้อหาบทนี้ตรงกับ **week 4** (partial derivatives/gradient) มากกว่า week 3 — ถ้าต้องการอ้างอิงสำหรับ week 4 ให้เปิดอ่านจากไฟล์ PDF โดยตรงเพื่อเตรียมตัวสอน แต่ห้ามคัดลอก/ถอดความลงเอกสารคอร์ส

## 3. The Matrix Calculus You Need For Deep Learning (arXiv 1802.01528)

**ไม่ถอดเนื้อหา** (สิทธิ์การใช้ไม่ชัดเจน) — สารบัญเพื่ออ้างอิงตำแหน่งเท่านั้น:

- 2. Review: Scalar derivative rules
- 3. Introduction to vector calculus and partial derivatives
- 4. Matrix calculus (Jacobian, element-wise ops, chain rules)
- 5. The gradient of neuron activation
- 6. The gradient of the neural network loss function

> ส่วนนี้เกี่ยวข้องกับ **week 4 หัวข้อ single-neuron backprop** มากที่สุด — อ่านเพื่อเตรียมตัวสอนเองได้ แต่ห้ามคัดลอกลงเอกสารคอร์ส

---

## สรุป: จะเอาไปใช้ปรับ week 3 อย่างไร

จุดที่ note_03.md/สไลด์ปัจจุบันสามารถแข็งแรงขึ้นได้ โดยอิงแนวทางจาก OpenStax §3.6 (chain rule) และ §3.3 (differentiation rules) ข้างต้น:
1. เพิ่ม **4-step problem-solving strategy** สำหรับ chain rule แบบมีโครงตายตัว (identify outer/inner → หา f' แทนค่า g(x) → หา g' → คูณ) ถ้ายังไม่มีในสไลด์ปัจจุบัน
2. ตรวจว่ามีตัวอย่าง **chain rule ซ้อน 3 ชั้น** อย่างน้อย 1 ข้อ (เตรียมทางไป week 4 multivariable chain rule)
2. ตรวจว่ามีคำเตือนชัดเจนเรื่อง **product rule ≠ f'g'** (เป็นจุดพลาดที่พบบ่อยที่สุดตามข้อสังเกตของ OpenStax)
4. พิจารณาใช้ **logarithmic differentiation** เป็นตัวอย่างที่ 3 (แบบ surprising) ของ chain rule ถ้ายังไม่มี — ตรงกับหลักเกณฑ์ NT-4a (ตัวอย่างที่ 3 ต้อง unexpected)
