# JOB HUNT プロモーション動画

LP（`index.html`）の内容をもとにした、イベント告知用の約36秒の動画です。

| ファイル | 用途 |
| --- | --- |
| `jobhunt_promo_16x9.mp4` | 横長 1920×1080。LPへの埋め込み、YouTube、説明会のスライドなど |
| `jobhunt_promo_9x16.mp4` | 縦長 1080×1920。Instagram リール、TikTok、YouTube ショートなど |

## 構成（36秒・120BPM）

| 時間 | シーン |
| --- | --- |
| 0〜4秒 | ロゴ「JOB HUNT」／28卒向け 就活イベント |
| 4〜8秒 | 会社の"大きさ"じゃなく、「誰と働くか」で選ぶ。 |
| 8〜17秒 | 3つの特徴（社長・役員と直接話せる／NGなしのフリートーク／私服参加＆履歴書不要） |
| 17〜23秒 | EVENT FLOW（12:30 受付 〜 17:00 交流会） |
| 23〜28秒 | 参加者の声（LP掲載の3件） |
| 28〜36秒 | FINAL CALL・応募フォームのQRコード |

## 素材

- 文言・配色・タイムテーブルはすべて LP から取っています。
- BGM と効果音は `src/music.py` で一から合成したオリジナルです。外部の音源やサンプルは使っていないため、著作権の扱いを気にせず使えます。
- フォントは Noto Sans JP（SIL Open Font License）、絵文字は Noto Color Emoji です。
- QRコードの読み取り先は `https://forms.gle/4QCdbr3ucUkjWc278`（LPの応募フォーム）です。

## 編集と再生成

文言やタイミングを変えるときは `src/promo.html` を編集します。各要素の `data-a` / `data-split` に書いた秒数が、動画上の表示タイミングです。

```bash
cd video/src
npm install                      # フォント（初回のみ）
pip install numpy scipy pyloudnorm
./build.sh                       # BGM の合成 → 全フレームの書き出し → mp4 化（横・縦）
```

ブラウザで `src/promo.html` を開き、開発者ツールで `seek(秒数)` を実行すると、任意の時点の画面を確認できます。
