# Unified Research Review: Autonomous Mathematical Discovery via Knowledge-Gap-Driven Curiosity

両レビューを統合し、重複を整理、新たに浮上した論点を加えて体系化。

---

## I. Critical Issues（着手前に対処必須）

### 1. 主張の定義・反証可能性が不十分

参照: `:9`, `:43`, `:246`

「first divergent discovery system」「fully autonomous」という中心主張に、操作的定義と検証基準が欠如。

- 「autonomous」の定義が曖昧。Kosmos（FutureHouse）も12時間の自律実行が可能で、autonomyは程度の問題
- 「divergent」の形式的定義がない。「人間が目標を指定しない」だけでは不十分（curiosity functionのα,β,γは人間が設定する）
- 比較表（`:240-248`）は各システムの公式引用が不足し、査読で「主観的比較」と見なされるリスクが高い

**推奨**:
- autonomyの操作的定義を設定（例: "human intervention per N discovery cycles"を定量指標化）
- 比較表の各セルに根拠論文の引用を付与
- 「first」の主張はスコープを限定（"first formally-verified curiosity-driven system"等）

---

### 2. Rediscovery実験のデータ漏洩バイアス

参照: `:259`, `:266`

致命的な問題。Mathlibから定理を除去しても、LLM（DeepSeek-Prover-V2含む）が事前学習でMathlib全体を学習済みの可能性が高い。「独立再発見」ではなく「記憶の再生」になり得る。

**推奨**:
- **盲検化設計**: 削除定理をLLMの学習データカットオフ以降にMathlibに追加された定理に限定
- **対照群**: LLMが学習済みの定理 vs 未学習の定理で再発見率を比較
- **memorization test**: 削除前の定理文をLLMに直接提示し、記憶しているか事前検証
- 実験の limitations として明示的に記載

---

### 3. Curiosity Functionの理論的基盤

参照: `:149-166`

| 問題 | 詳細 |
|------|------|
| novelty | embedding距離 ≠ 数学的新規性。距離大だが自明な命題が存在する |
| tractability | LLMの自信度はcalibrationが不良。過信/過小評価が常態 |
| significance | graph centralityと数学的重要性の相関は未検証 |
| 理論接続 | Schmidhuberのcompression progress等との接続が表面的 |

**推奨**:
- 最低2つの代替定式化を用意（例: information gain-based, count-based exploration bonus）
- ablation studyでα,β,γの感度分析だけでなく、関数形自体の比較を実施
- 理論的正当化を1段落以上追加（なぜ線形結合か、非線形の検討は？）

---

## II. High Priority Issues（Phase 1-2で対処）

### 4. Novelty判定の脆弱性

参照: `:209-218`

| レイヤー | 問題 |
|---------|------|
| Mathlib check | 表面的な文字列/embedding一致では数学的同値性を捉えられない |
| arXiv + LLM | LLMによる数学的同値性判定は信頼性が低い |
| Triviality | 「N行以下 = trivial」は粗い基準。短くても深い結果、冗長でも自明な結果がある |

**推奨**:
- 式変形同値性の判定層を追加（Lean 4のdefEqチェック、または正規化後の比較）
- trivialityは行数だけでなく、使用されるtacticの複雑度・依存lemma数の複合指標に
- Novelty判定のprecision/recallをパイロット実験で定量評価

---

### 5. Staleness Detectionの統計設計

参照: `:220-235`

「3/4指標がN回連続低下」の設計には以下が未定義:
- **N**の決定根拠（恣意的になりやすい）
- 偽陽性率（まだ生産的なのに停止してしまう）
- 偽陰性率（停滞しているのに続行してしまう）
- 各指標間の相関構造（独立でなければ3/4基準の意味が変わる）

**推奨**:
- Change point detectionアルゴリズムの適用を検討（CUSUM, BOCPD等）
- シミュレーションで偽陽性/偽陰性率を事前推定
- Nをハイパーパラメータとして感度分析に含める

---

### 6. Proof Engineの成功率見積もり

参照: `:185-195`

miniF2Fの88.9%はbenchmark数値。未知の予想への適用では大幅に低下する見込み。

**推奨**:
- 「予想の難易度」と「証明成功率」の関係をパイロット実験で推定
- 成功率を前提とした探索効率のシミュレーション（例: 成功率10%なら1つの新規定理に平均何cycle必要か）
- compute budgetの具体的数値（トークン数/時間/GPU時間）を明記

---

## III. Medium Priority Issues（Phase 2-3で対処）

### 7. 計算コスト・再現性

参照: `:185`, `:292`, `:435`

| 未定義項目 | 影響 |
|-----------|------|
| 671Bモデルの推論コスト/cycle | 8ヶ月のfeasibility判断不能 |
| 10K+ iterationの所要GPU時間 | 実験計画の信頼性低下 |
| LLMの非決定性 | 再現性の議論が欠如 |

**推奨**: Phase 1で小規模パイロットを実施し、1 cycleあたりのコスト・時間を実測。それを基にスケーリング計画を策定。

---

### 8. 成功基準の統計的厳密化

参照: `:266`, `:277`

「再発見率がランダムより有意に高い」「少なくとも1件の新規定理」はいずれも統計的検出力の議論が不足。

**推奨**:
- 再発見率: ベースラインとの差に対する検定方法・サンプルサイズ設計を事前に記述
- 新規定理: 定量目標を追加（例: "N件以上のnovel結果, うちM件が人間評価でnon-trivial"）
- 効果量（effect size）の事前推定

---

### 9. Gap DetectionのスケーラビリティとFalse Positive

参照: `:95-143`

210K+定理に対するO(S² × T)の計算量問題と、gap候補のfalse positive制御の議論が欠如。

---

### 10. Auto-formalizationの精度

参照: `:169-181`

自然言語→Lean 4の変換精度が未検証。well-typed ≠ 意味のある命題。

---

## IV. Low Priority Issues

### 11. 文書品質

- `:11` "until it stales" → "until it stagnates"が適切
- 比較表のトーンをより中立的に改訂

---

## 統合推奨アクションリスト

| 優先度 | アクション | 対応Issue | Phase |
|--------|-----------|-----------|-------|
| **P0** | 「autonomous」「divergent」「first」の操作的定義を策定 | #1 | 着手前 |
| **P0** | Rediscovery実験の盲検化・データ漏洩対策を設計 | #2 | 着手前 |
| **P0** | Curiosity functionの代替定式化を2つ以上用意 | #3 | 着手前 |
| **P0** | Go/no-goの「non-trivial」を定量基準化（例: 数学者3名の盲検評価で2/3以上が"interesting"） | #1,#8 | 着手前 |
| **P1** | Novelty判定にdefEqベースの同値性チェック層を追加 | #4 | Phase 1 |
| **P1** | Staleness detectionにchange point detectionを導入 | #5 | Phase 1 |
| **P1** | 小規模パイロットで1 cycleあたりのコスト・時間を実測 | #7 | Phase 1 |
| **P1** | Auto-formalization精度のpilot study | #10 | Phase 1 |
| **P2** | 成功基準の統計設計（検定方法、サンプルサイズ、効果量） | #8 | Phase 2 |
| **P2** | 比較表に引用付与・トーン改訂 | #1 | Phase 2 |
| **P3** | 文書表現の修正 | #11 | 随時 |

---

## 総合評価

**アイデアの強さ**: 高い。Problem-findingの自動化 × 形式検証という組み合わせは、タイムリーかつ独自性がある。

**最大の3リスク** (両レビュー合意):
1. **Gap detectorの品質** — 全体の成否を決める。Phase 1のgo/no-goが生命線
2. **実験のバイアス制御** — 特にRediscovery実験のデータ漏洩問題。これを解決しないと主結果の信頼性が崩壊
3. **評価の統計設計** — 成功基準・staleness判定ともに統計的裏付けが必要

**判定: 条件付きGo。** P0アクション4件を着手前に完了し、Phase 1のgo/no-goを厳格に実施した上で継続判断を行うことを推奨。
