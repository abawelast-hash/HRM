# تحليل شامل لمشروع ACTION-main
## التوجيه نحو نظام التنبؤ بسعر صرف الليرة السورية مقابل الدولار

> **المشروع الحالي**: ACTION-main — نظام بولندي للتنبؤ بأسعار الأسهم  
> **الهدف**: استخدامه كأساس لتطوير منصة ذكاء اقتصادي لسعر صرف الليرة السورية  
> **النموذج الأساسي**: Temporal Fusion Transformer (TFT) عبر pytorch-forecasting  
> **التاريخ**: مارس 2026

---

## القسم 1: تحليل الهيكلية العامة

### 1.1 خريطة المجلدات ودور كل مجلد

```text
ACTION-main/
│
├── app/                        ← طبقة العرض (Presentation Layer)
│   ├── app.py                  ← تطبيق Streamlit الرئيسي (UI + Logic)
│   ├── benchmark_utils.py      ← أدوات الباك تيستينغ والمقارنة
│   ├── config_loader.py        ← تحميل الإعدادات وقائمة التيكرات
│   ├── plot_utils.py           ← دوال رسم المخططات (Plotly)
│   └── __init__.py
│
├── config/                     ← ملفات الإعدادات (Configuration)
│   ├── config.yaml             ← إعدادات النموذج والتدريب والبيانات
│   ├── tickers_with_names.yaml ← قائمة الرموز مع أسمائها (UI)
│   └── benchmark_tickers.yaml ← رموز خاصة بالباك تيستينغ
│
├── models/                     ← النماذج المدربة والمعيّرات
│   ├── Gen4_3x.pth             ← نموذج مخزّن (checkpoint)
│   ├── Gen6_1.pth              ← النموذج النشط حالياً
│   └── normalizers/            ← ملفات المعيّرات (.pkl)
│
├── scripts/                    ← منطق الأعمال (Business Logic)
│   ├── data_fetcher.py         ← جلب البيانات من yfinance (async)
│   ├── preprocessor.py         ← معالجة البيانات وبناء TimeSeriesDataSet
│   ├── model.py                ← تعريف CustomTFT + build_model
│   ├── prediction_engine.py    ← تحميل النموذج وتوليد التنبؤات
│   ├── train.py                ← حلقة التدريب + Optuna
│   ├── config_manager.py       ← إدارة الإعدادات والمعيّرات
│   │
│   ├── utils/
│   │   ├── feature_engineer.py ← حساب المؤشرات الفنية
│   │   ├── model_config.py     ← ModelConfig + HyperparamFactory
│   │   ├── batch_size_estimator.py ← تقدير batch size تلقائياً
│   │   ├── transfer_weights.py ← نقل الأوزان بين نسخ النموذج
│   │   └── validation_utils.py ← أدوات تصحيح الأخطاء والرسم
│   │
│   └── debug/
│       ├── analyze_data.py
│       ├── debug_dataset.py
│       └── feature_importance.py
│
├── docs/images/                ← صور التوثيق
├── start_training.py           ← نقطة دخول التدريب
├── requirements.txt            ← المكتبات المطلوبة
└── config.yaml, STOCK_PREDICTION_V3.md, target.md
```

### 1.2 ملفات الإعدادات وما تحتويه

**config/config.yaml** (الملف الرئيسي):

| القسم | المحتوى | القيم الافتراضية |
|---|---|---|
| `model_name` | اسم الجيل النشط | `Gen6_1` |
| `model.max_prediction_length` | أفق التنبؤ (يوم) | `60` |
| `model.max_encoder_length` | تاريخ المدخلات (يوم) | `180` |
| `model.min_encoder_length` | حد أدنى للمدخلات | `50` |
| `model.hidden_size` | حجم الطبقة الخفية | `128` |
| `model.attention_head_size` | عدد رؤوس الانتباه | `4` |
| `model.dropout` | معدل Dropout | `0.3` |
| `model.lstm_layers` | طبقات LSTM | `2` |
| `model.use_quantile_loss` | تفعيل Quantile Loss | `true` |
| `model.quantiles` | كميات التوقع | `[0.1, 0.5, 0.9]` |
| `model.sectors` | قائمة القطاعات | 12 قطاعاً |
| `training.max_epochs` | أقصى دورات تدريب | `100` |
| `training.optuna_trials` | عدد تجارب Optuna | `5` |

### 1.3 خريطة تدفق البيانات

```text
[يfinance API]
      │
      ▼
[data_fetcher.py]  ────────────────────────────────────────────────────────────
  • fetch_stock_data() (async)                                                │
  • يجلب OHLCV + Sector                                                       │
  • يصحح الفجوات تلقائياً (repair=True)                                        │
  • يحفظ raw_data.csv                                                         │
      │                                                                       │
      ▼                                                                       │
[feature_engineer.py]                                                         │
  • add_features() ─ يحسب المؤشرات الفنية                                      │
  • MA10, MA50, BB_upper, RSI, MACD, ROC, VWAP                               │
  • Momentum_20d, Close_to_MA_ratio, Relative_Returns                         │
      │                                                                       │
      ▼                                                                       │
[preprocessor.py]                                                             │
  • _split_with_gap() ─── Train (80%) │ Gap (10d) │ Val (20%)                 │
  • log1p على: Close, Volume, MA10, MA50, VWAP                                │
  • TorchNormalizer لكل ميزة رقمية                                             │
  • بناء TimeSeriesDataSet                                                    │
  • يحفظ dataset.pt + normalizers.pkl                                         │
      │                                                                       │
      ▼                                                                       │
[train.py]                                                         ────────────┘
  • Optuna (5 trials) → best hyperparams
  • PyTorch Lightning Trainer
  • EarlyStopping (val_loss)
  • CustomModelCheckpoint → model.pth
      │
      ▼
[prediction_engine.py]
  • load_data_and_model() (async)
  • preprocess_data()
  • generate_predictions() → median, lower (Q10), upper (Q90)
      │
      ▼
[app.py / benchmark_utils.py]
  • Streamlit Dashboard
  • مخططات Plotly التفاعلية
  • MAPE, MAE, Directional Accuracy
```

### 1.4 المعمارية البرمجية

المشروع يتبع **Layered Architecture** مع فصل جزئي للمسؤوليات:
- **طبقة البيانات**: `data_fetcher.py` + `feature_engineer.py`
- **طبقة المعالجة**: `preprocessor.py` + `config_manager.py`
- **طبقة النموذج**: `model.py` + `model_config.py`
- **طبقة الاستدلال**: `prediction_engine.py` + `train.py`
- **طبقة العرض**: `app.py` + `benchmark_utils.py` + `plot_utils.py`

**ملاحظة**: لا يتبع MVC بشكل صارم — `app.py` يحتوي على منطق أعمال داخله (`StockPredictor`).

---

## القسم 2: تحليل طبقة البيانات

### 2.1 مصادر البيانات

**data\_fetcher.py** يعتمد على `yfinance` بنمط **async**:

```python
# الدوال المستخدمة من yfinance:
yf.Ticker(ticker)          # إنشاء كائن Ticker
stock.info                 # معلومات الشركة (Sector، firstTradeDateEpochUtc)
stock.history(
    start=start_date,
    end=end_date,
    repair=True,           # ← تصليح تلقائي للفجوات
    auto_adjust=True       # ← تعديل الأسعار للأرباح والانشقاقات
)
```

**ميزات بارزة**:
- تنفيذ غير متزامن عبر `ThreadPoolExecutor(max_workers=10)` داخل `asyncio`
- جلب 50 يوماً إضافياً قبل `start_date` كـ buffer (لحساب المؤشرات)
- إذا كانت البيانات أقل من 60% من الأيام المتوقعة → يمتد العام سنةً للخلف
- يُسجَّل ويُحفظ كـ CSV في `raw_data.csv`

### 2.2 معالجة البيانات (preprocessor.py)

#### التقسيم مع الفجوة الزمنية:
```python
# _split_with_gap():
# • يُقسَّم حسب ticker (لكل سهم بشكل منفرد)
# • 80% → train | 10 أيام gap | الباقي → validation
# • gap_days = 10 (ثابتة في الكود)
# • الهدف: منع تسرب البيانات المستقبلية
split_date = min_date + Timedelta(days=0.8 * total_days)
val_start = split_date + Timedelta(days=gap_days + 1)
```

#### التطبيع:
```python
# 1. Log1p Transform (قبل التطبيع):
df[feature] = np.log1p(df[feature].clip(lower=0))  # Close, Volume, MA10, MA50, VWAP

# 2. TorchNormalizer (من pytorch-forecasting):
normalizers[feature] = TorchNormalizer()
train[feature] = normalizers[feature].fit_transform(train[feature].values)
val[feature]   = normalizers[feature].transform(val[feature].values)
```

#### المتغير الهدف:
```python
# Relative_Returns = العائد النسبي اليومي:
group['Relative_Returns'] = group['Close'].pct_change()
# النموذج يتنبأ بالعائد النسبي وليس بالسعر المطلق
```

#### معالجة القيم المفقودة:
- `ffill()` ثم `bfill()` للمؤشرات الفنية
- `fillna(0)` لـ `Relative_Returns`
- `allow_missing_timesteps=True` في `TimeSeriesDataSet`

### 2.3 هندسة الميزات (feature\_engineer.py)

#### المؤشرات الفنية:

| المؤشر | المعادلة | المعلمات |
|---|---|---|
| **MA10** | $\bar{P}_{10} = \frac{1}{10}\sum_{i=0}^{9} P_{t-i}$ | period=10 |
| **MA50** | $\bar{P}_{50} = \frac{1}{50}\sum_{i=0}^{49} P_{t-i}$ | period=50 |
| **BB\_upper** | $\bar{P}_{20} + 2\sigma_{20}$ | period=20 |
| **Close\_to\_BB\_upper** | $\frac{P_t}{BB_{upper}}$ | نسبة السعر للشريط |
| **RSI** | $100 - \frac{100}{1 + RS}$، $RS = \frac{avg\_gain}{avg\_loss}$ | period=14 |
| **MACD** | $EMA_{12} - EMA_{26}$ | spans: 12, 26 |
| **ROC** | $100 \times \frac{P_t - P_{t-20}}{P_{t-20}}$ | period=20 |
| **VWAP** | $\frac{\sum(P_{typical} \times V)}{\sum V}$ حيث $P_{typical} = \frac{C+C+C}{3}$ | تراكمي |
| **Momentum\_20d** | $P_t - P_{t-20}$ | period=20 |
| **Close\_to\_MA\_ratio** | $\frac{P_t}{MA_{50}}$ | نسبة |
| **Relative\_Returns** | $\frac{P_t - P_{t-1}}{P_{t-1}}$ | هو المتغير الهدف |

#### الميزات الزمنية:
```python
group['Month']       = group['Date'].dt.month.astype(str)      # 1..12
group['Day_of_Week'] = group['Date'].dt.dayofweek.astype(str)  # 0..6
```

#### الميزات الفئوية الثابتة:
```python
df['Sector']  # قطاع الشركة (12 فئة) — static categorical
```

---

## القسم 3: تحليل النموذج

### 3.1 بنية TFT (model.py)

**`CustomTemporalFusionTransformer`** هو غلاف (wrapper) فوق `TFT` من `pytorch-forecasting`:

```text
CustomTemporalFusionTransformer (LightningModule)
│
└── self.model = TFTWithTransfer (TemporalFusionTransformer)
    │
    ├── Variable Selection Network (VSN)
    │   • يُحدِّد أهمية كل متغير ديناميكياً
    │   • مدخلات: الميزات المشفَّرة
    │   • مخرجات: متجهات مرجَّحة + أوزان الاختيار
    │
    ├── Gated Residual Networks (GRN)
    │   • يُضخِّم المعلومات مع بوابات تُتحكم في التدفق
    │   • يُقلِّل مخاطر Vanishing Gradient
    │   • يُضاف Residual Connection مع LayerNorm
    │
    ├── LSTM Encoder-Decoder
    │   • lstm_layers: 2 (افتراضي)
    │   • يعالج السلاسل الزمنية
    │
    └── Multi-Head Attention
        • attention_head_size: 4
        • يُحدِّد الفترات الزمنية الأكثر تأثيراً في التنبؤ
        • يُوفِّر قابلية تفسيرية مدمجة
```

**متغيرات الإدخال**:

| النوع | المتغيرات |
|---|---|
| `time_varying_unknown_reals` | Close, Volume, MA10, MA50, RSI, MACD, ROC, VWAP, Momentum_20d, Close_to_MA_ratio, Close_to_BB_upper, Relative_Returns |
| `time_varying_known_categoricals` | Day_of_Week (0-6), Month (1-12) |
| `static_categoricals` | Sector (12 فئة) |
| `target` | Relative_Returns |

**المعلمات الافتراضية**:
```yaml
hidden_size: 128
lstm_layers: 2
attention_head_size: 4
dropout: 0.3
hidden_continuous_size: 64  # = hidden_size // 2
learning_rate: 0.001
```

### 3.2 دوال الخسارة (model\_config.py)

#### Quantile Loss:

$$\mathcal{L}_q(y, \hat{y}) = \begin{cases} q \cdot (y - \hat{y}) & \text{if } y \geq \hat{y} \\ (q - 1) \cdot (y - \hat{y}) & \text{if } y < \hat{y} \end{cases}$$

**الكميات المستخدمة**: `[0.1, 0.5, 0.9]`
- **Q10**: الحد الأدنى لنطاق الثقة (pessimistic scenario)
- **Q50**: التنبؤ المتوسط (الأكثر احتمالاً)
- **Q90**: الحد الأعلى لنطاق الثقة (optimistic scenario)

**لماذا Quantile Loss وليس MSE؟**

| المعيار | MSE | Quantile Loss |
|---|---|---|
| التنبؤ | نقطة واحدة | نطاق ثقة كامل |
| الحساسية للشواذ | عالية (مربع) | منخفضة |
| قابلية التفسير | منخفضة | عالية (نطاقات احتمالية) |
| الأسواق المتقلبة | غير مناسب | مناسب جداً |
| اتخاذ القرار | بسيط | أغنى بالمعلومات |

### 3.3 عملية التدريب (train.py)

#### Optuna (تحسين المعلمات الفائقة):
```python
# المعلمات المُحسَّنة:
hidden_size:           [64, 128]
learning_rate:         [1e-5, 1e-3]  (log scale)
attention_head_size:   [2, 4]
dropout:               [0.1, 0.3]
lstm_layers:           [1, 2]
hidden_continuous_size:[64, 128]

# عدد التجارب: 5 (config: optuna_trials)
# اتجاه التحسين: minimize (val_loss)
```

#### Early Stopping:
```python
EarlyStopping(monitor="val_loss", patience=config['training']['early_stopping_patience'])
# يوقف التدريب عند توقف تحسُّن val_loss لعدد من الدورات
```

#### Checkpointing:
```python
# CustomModelCheckpoint يحفظ عند تحقيق أفضل val_loss:
checkpoint = {
    "state_dict": pl_module.state_dict(),
    "hyperparams": dict(pl_module.hparams)
}
torch.save(checkpoint, save_path)  # → models/Gen6_1.pth
```

#### Automatic Mixed Precision:
```python
precision="16-mixed"  # GPU: bfloat16 للحسابات
# → يُسرِّع التدريب ويُقلِّل استهلاك VRAM
```

#### Batch Size Estimation:
- `batch_size_estimator.py` يقدِّر batch size تلقائياً بناءً على VRAM المتاح
- يمنع OOM (Out of Memory) errors

---

## القسم 4: تحليل التنبؤ والتقييم

### 4.1 محرك التنبؤ (prediction\_engine.py)

**تدفق التنبؤ**:

```python
# 1. جلب البيانات
fetcher.fetch_stock_data(ticker, start, end)  # async

# 2. تحميل dataset وnormalizers
dataset = torch.load("processed_data.pt")
normalizers = config_manager.load_normalizers(model_name)

# 3. تحميل النموذج
checkpoint = torch.load(model_path)
model = build_model(dataset, config, hyperparams=checkpoint["hyperparams"])
model.load_state_dict(checkpoint["state_dict"])
model.to(device)

# 4. المعالجة المسبقة
ticker_data, original_close = preprocessor.process_data(mode='predict', ...)

# 5. التنبؤ
ticker_dataset = TimeSeriesDataSet.from_parameters(dataset.get_parameters(), ticker_data, predict_mode=True)
predictions = model.predict(dataloader, mode="quantiles")

# 6. إلغاء التطبيع (Denormalization)
median       = normalizer.inverse_transform(predictions[:, :, 1])  # Q50
lower_bound  = normalizer.inverse_transform(predictions[:, :, 0])  # Q10
upper_bound  = normalizer.inverse_transform(predictions[:, :, 2])  # Q90
```

**ملاحظة مهمة**: النموذج يتنبأ بـ `Relative_Returns`، ثم يُحوَّل إلى أسعار مطلقة عبر:
$$P_t = P_{t-1} \times (1 + r_t)$$

### 4.2 نظام التقييم (benchmark\_utils.py)

#### المقاييس المستخدمة:

```python
# 1. MAPE (Mean Absolute Percentage Error):
differences   = |median - actual| 
relative_diff = (differences / actual) * 100
MAPE = mean(relative_diff)

# 2. Accuracy = 100 - MAPE

# 3. MAE (Mean Absolute Error):
MAE = mean(|median - actual|)

# 4. Directional Accuracy:
pred_changes   = sign(diff(median))
actual_changes = sign(diff(actual))
DirAcc = mean(pred_changes == actual_changes) * 100
```

#### Backtesting:
```python
# process_ticker():
# 1. يأخذ البيانات حتى trim_date
# 2. يولِّد تنبؤ لـ max_prediction_length أيام قادمة
# 3. يقارن بالأسعار الفعلية التي جرت بعد trim_date
# 4. يحسب كل المقاييس
# 5. يُخزَّن النتيجة في benchmark_history.csv
```

---

## القسم 5: تحليل واجهة المستخدم (app.py)

### 5.1 هيكل التطبيق

```python
class StockPredictor:
    def predict(ticker, start, end)          # توقع مستقبلي
    def predict_historical(ticker, ..., trim_date)  # مقارنة تاريخية
```

**الصفحات الرئيسية** (عبر `st.sidebar.radio`):
1. **صفحة التنبؤ**: اختيار ticker + نطاق تاريخي → رسم بياني مع نطاقات الثقة
2. **صفحة Benchmark**: اختيار تيكرات متعددة → جدول MAPE/MAE/DirAcc + رسوم مقارنة
3. **عرض النتائج**: مخطط Plotly تفاعلي يُظهر:
   - السعر التاريخي (خط أزرق)
   - التنبؤ المتوسط (خط أحمر متقطع)
   - نطاق الثقة 10%-90% (منطقة شفافة)

---

## القسم 6: متطلبات التشغيل

### 6.1 المكتبات الأساسية

```txt
torch>=2.3.0         (مع CUDA 12.8)
pytorch-lightning>=2.2.0
pytorch-forecasting>=1.0.0
pandas>=2.0
yfinance
streamlit
optuna
plotly
PyYAML
nest_asyncio
aiohttp
```

### 6.2 متطلبات GPU

- **مستحسن**: GPU ذو CUDA للتدريب (Mixed Precision 16-bit)
- **يعمل بدون GPU**: على CPU مع `precision="32-true"` (أبطأ بكثير)
- لا يوجد `Dockerfile` في المشروع

---

## القسم 7: نقاط القوة والضعف لمشروع الفوركس

### 7.1 نقاط القوة (ما يمكن استعارته مباشرة)

| المكوِّن | قابلية الاستخدام |
|---|---|
| نموذج TFT الكامل (model.py) | ✅ مباشرة — يدعم multivariate |
| Quantile Loss | ✅ مباشرة — مهم للأسواق المتقلبة |
| Optuna integration | ✅ مباشرة — لضبط المعلمات الفائقة |
| PyTorch Lightning trainer | ✅ مباشرة — الكود نظيف وقابل للتوسع |
| Custom checkpoint system | ✅ مباشرة |
| Streamlit + Plotly UI | ✅ مباشرة مع تعديل بسيط |
| Async data fetching pattern | ✅ مباشرة — يُعاد استخدامه مع مصادر أخرى |
| TorchNormalizer pipeline | ✅ مباشرة |
| Backtesting framework | ✅ مباشرة |
| MAPE/MAE/DirAcc metrics | ✅ مباشرة |

**أفضل 5 ممارسات قابلة للتطبيق فوراً**:
1. **Gap في التقسيم**: 10 أيام بين train/val يمنع Data Leakage
2. **Log1p Transform**: يُحسِّن توزيع الأسعار المائلة قبل التطبيع
3. **Quantile Predictions**: توقع 3 مستويات بدل مستوى واحد
4. **Async fetching**: يُتيح جمع بيانات متوازي من مصادر متعددة
5. **Automatic batch size estimation**: يمنع OOM ويُحسِّن الاستخدام

---

### 7.2 نقاط الضعف (ما يحتاج تعديل)

#### مشاكل البيانات:

**1. الفجوات الزمنية (عطل نهاية الأسبوع)**

المشكلة الحالية في `data_fetcher.py`:
```python
# يعتمد على yfinance الذي يُرجع فقط أيام التداول
# السوق السوري يختلف: جمعة-سبت هي عطلة (وليس سبت-أحد)
# + أيام العطل الرسمية السورية غير متوقعة
```

الحل المطلوب:
```python
# إضافة reindex كامل لجميع الأيام ثم استيفاء:
full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
df = df.reindex(full_index)

# استيفاء تربيعي للبيانات المفقودة (1-3 أيام):
df['Close'] = df['Close'].interpolate(method='quadratic')

# وضع علامة على القيم المستوفاة:
df['is_interpolated'] = df['Close'].isna().shift(1) | df['Close'].isna().shift(-1)
```

**2. دعم البيانات الساعية (Hourly)**

المشروع الحالي: يومي فقط (`freq='D'`)  
المطلوب: ساعي (`freq='H'`) → تعديل في `TimeSeriesDataSet`:
```yaml
# config.yaml المُعدَّل للفوركس الساعي:
max_encoder_length: 168   # 7 أيام × 24 ساعة
max_prediction_length: 24 # 24 ساعة قادمة
```

**3. التداول 24/5 بدلاً من 5/7**

السوق السوري يتداول 5 أيام/أسبوع (أحد-خميس)، وليس 5/7 مع يومين عطلة ثابتين.

#### مشاكل الميزات:

**المؤشرات غير المناسبة للفوركس**:
- `Volume` — لا يوجد حجم موثوق لسوق الفوركس السوري غير الرسمي
- `VWAP` — يعتمد على Volume → غير دقيق
- `Sector` — لا يوجد مفهوم قطاع في الفوركس
- `BB_upper` فقط — نحتاج الشريط الكامل (وسط + أدنى)

**الميزات الإضافية المطلوبة للفوركس السوري**:
```python
# ميزات جلسات التداول:
df['session_damascus']  = ((df['Hour'] >= 9) & (df['Hour'] < 15)).astype(int)
df['session_london']    = ((df['Hour'] >= 8) & (df['Hour'] < 16)).astype(int)
df['session_newyork']   = ((df['Hour'] >= 13) & (df['Hour'] < 21)).astype(int)

# ميزات أسعار الذهب والنفط والليرة اللبنانية:
df['gold_price_change'] = df['gold_usd'].pct_change()
df['oil_price_change']  = df['brent_usd'].pct_change()
df['lbp_change']        = df['usd_lbp'].pct_change()

# مؤشر الدولار (DXY):
df['dxy_change']        = df['dxy'].pct_change()

# مؤشرات المشاعر (من NLP):
df['sentiment_score']     = ...  # ناتج LSTM + GloVe
df['event_weight']        = ...  # وزن الحدث بعد التلاشي الزمني

# ميزات زمنية سورية:
df['is_friday']         = (df['Day_of_Week'] == '4').astype(int)
df['is_holiday']        = df['date'].isin(SYRIA_HOLIDAYS).astype(int)
df['ramadan_flag']      = ...  # مؤشر رمضان (يؤثر على السوق)
```

#### مشاكل النموذج:

**1. أفق التنبؤ**: 60 يوم مناسب للأسهم، لكن للفوركس السوري 24-72 ساعة أكثر عملية.

**2. التحديث المستمر (Online Learning)**: المشروع لا يدعمه. يحتاج:
```python
# إضافة continue_training=True في train_model() كل أسبوع
# مع نافذة متحركة من آخر N يوم
```

**3. المتغير الهدف**: `Relative_Returns` مناسب بالفعل للفوركس.

---

## القسم 8: خطة التعديل المفصلة للفوركس

### المرحلة 1: تعديل طبقة البيانات

```python
# data_fetcher.py — التعديلات المطلوبة:

# 1. تغيير مصادر البيانات:
FOREX_SOURCES = {
    'sp_today': 'https://sp-today.com/...',  # سعر السوق السوري
    'investing': 'https://investing.com/...',  # سعر رسمي
    'telegram_rates': 'telethon_client...',   # قنوات أسعار
}

# 2. إضافة مؤشرات خارجية من yfinance:
EXTERNAL_TICKERS = {
    'gold':  'GC=F',
    'oil':   'BZ=F',
    'dxy':   'DX-Y.NYB',
    'lbtry': 'USD/TRY=X',
}

# 3. معالجة أيام العطل السورية:
SYRIA_WEEKENDS = [4, 5]  # جمعة=4، سبت=5
```

### المرحلة 2: تعديل طبقة الميزات

```python
# feature_engineer.py — إضافات:
class ForexFeatureEngineer(FeatureEngineer):
    
    def add_forex_features(self, df):
        # حذف Sector (غير منطقي في الفوركس)
        # حذف VWAP (يعتمد على Volume)
        
        # إضافة ATR (Average True Range) — مهم لقياس التقلب:
        df['ATR'] = compute_atr(df['High'], df['Low'], df['Close'])
        
        # إضافة شريط Bollinger كامل:
        sma = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        df['BB_upper']  = sma + 2 * std
        df['BB_middle'] = sma
        df['BB_lower']  = sma - 2 * std
        df['BB_width']  = (df['BB_upper'] - df['BB_lower']) / sma
        
        # إضافة Stochastic Oscillator:
        low_14  = df['Low'].rolling(14).min()
        high_14 = df['High'].rolling(14).max()
        df['Stoch_K'] = 100 * (df['Close'] - low_14) / (high_14 - low_14)
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        return df
```

### المرحلة 3: تعديل ملف الإعدادات

```yaml
# config.yaml المُعدَّل لنظام الليرة السورية:
model_name: SYP_USD_V1

model:
  max_prediction_length: 24    # 24 ساعة قادمة
  min_encoder_length: 72       # 3 أيام كحد أدنى
  max_encoder_length: 168      # 7 أيام تاريخ (× 24 ساعة)
  hidden_size: 64              # أصغر بسبب بيانات أقل
  attention_head_size: 2
  dropout: 0.2
  lstm_layers: 2
  use_quantile_loss: true
  quantiles: [0.05, 0.25, 0.5, 0.75, 0.95]  # نطاقات ثقة أوسع للسوق المتقلب

  # بدون sectors — نستبدل بمجموعة مصدر البيانات:
  source_groups:
    - market_rate    # سعر السوق
    - official_rate  # سعر رسمي
    - hawala_rate    # سعر الحوالات

training:
  max_epochs: 50
  optuna_trials: 10    # نزيد لأن النموذج أصغر
  early_stopping_patience: 10

data:
  frequency: 'H'       # ساعي
  gap_days: 3          # 3 أيام بدل 10 (بيانات ساعية أقل تأثراً)
```

---

## القسم 9: استخراج أجزاء الكود القابلة لإعادة الاستخدام

### 9.1 جزء تحميل البيانات (data\_fetcher.py)

```python
# قابل للاستخدام مباشرة - يكفي تغيير المصدر من yfinance إلى scraper:
async def fetch_stock_data(self, ticker, start_date, end_date, session):
    loop = asyncio.get_event_loop()
    # ← استبدل هذا السطر فقط بـ web scraper أو API مخصص:
    df = await loop.run_in_executor(
        self.executor, 
        lambda: yf.Ticker(ticker).history(start=..., end=..., repair=True)
    )
    return df
```

### 9.2 جزء معالجة البيانات مع Gap (preprocessor.py)

```python
def _split_with_gap(self, df):
    """
    قابل للاستخدام مباشرة للفوركس.
    التعديل الوحيد: gap_days=3 بدل 10 للبيانات الساعية.
    """
    def split_group(group):
        group = group.sort_values('Date')
        total_days = (group['Date'].max() - group['Date'].min()).days
        train_days = int(0.8 * total_days)
        split_date = group['Date'].min() + pd.Timedelta(days=train_days)
        train = group[group['Date'] <= split_date]
        val_start_date = split_date + pd.Timedelta(days=self.gap_days + 1)
        val = group[group['Date'] >= val_start_date]
        return train, val
```

### 9.3 جزء بناء TFT (model.py)

```python
# استخدم build_model() مباشرة مع dataset جديد:
model = build_model(
    dataset=forex_dataset,
    config=config,
    hyperparams=best_params  # من Optuna
)
# لا يحتاج أي تعديل — TFT مرن بطبيعته
```

### 9.4 جزء Quantile Loss (model\_config.py)

```python
# زد الكميات للسوق المتقلب:
QuantileLoss(quantiles=[0.05, 0.25, 0.5, 0.75, 0.95])
# Q50 = التوقع الأساسي
# Q05-Q95 = النطاق الواسع للحالات الشاذة
```

### 9.5 جزء Optuna (train.py)

```python
# قابل للاستخدام مباشرة مع توسيع نطاق البحث:
study = optuna.create_study(direction="minimize")
study.optimize(
    lambda trial: objective(trial, train_dataset, val_dataset, config), 
    n_trials=config['training']['optuna_trials'],
    # إضافة للفوركس:
    callbacks=[optuna.callbacks.EarlyStoppingCallback(patience=5)]
)
```

### 9.6 جزء Backtesting (benchmark\_utils.py)

```python
# process_ticker() قابل للاستخدام مع تعديل طريقة جلب الأسعار:
# فقط استبدل:
ticker_data = full_data[full_data['Ticker'] == ticker]
# بـ:
ticker_data = forex_data[forex_data['source'] == rate_source]
```

### 9.7 جزء عرض النتائج (app.py)

```python
# create_stock_plot() من plot_utils.py قابل للاستخدام مباشرة:
# يرسم: تاريخ سعري + توقع + نطاق ثقة
# فقط غيِّر العنوان من "سعر السهم" إلى "سعر الصرف SYP/USD"
```

---

## القسم 10: التوصيات النهائية

### 10.1 هل ACTION-main مناسب كأساس؟

**الإجابة: نعم جزئياً (70%)** — مع تحفظات واضحة.

**ما هو مناسب**:
- البنية المعمارية الكاملة (طبقات، تدفق، أنماط)
- نموذج TFT والكود المرتبط به (استخدام مباشر تقريباً)
- طبقة التدريب (Optuna + Lightning + Checkpointing)
- طبقة التقييم والباك تيستينغ
- واجهة Streamlit

**ما ليس مناسباً مباشرةً ويحتاج إضافة من صفر**:
- مصدر البيانات (scraper سوري بدل yfinance)
- ميزات NLP وتحليل المشاعر العربي
- تكامل مصادر متعددة (تلغرام، أخبار، ذهب، نفط)
- نظام تخزين (InfluxDB/PostgreSQL بدلاً من CSV)
- معالجة خصوصيات السوق السوري

### 10.2 التحديات المتوقعة (أهم 5)

| # | التحدي | الصعوبة | الحل المقترح |
|---|---|---|---|
| 1 | **جمع بيانات الأسعار السورية بشكل موثوق** | عالية جداً | Telethon + multi-source + تحقق متقاطع |
| 2 | **معالجة النصوص العربية (NLP)** | عالية | CAMeL Tools + FastText عربي + AraBERT |
| 3 | **محدودية البيانات التاريخية** | عالية | بناء أرشيف من اليوم الأول + استيفاء تربيعي |
| 4 | **تقلبات حادة وشواذ (Black Swans)** | متوسطة | Quantile Loss موسع + Robust normalization |
| 5 | **تحديث النموذج المستمر ببيانات جديدة** | متوسطة | continue_training + نافذة متحركة |

### 10.3 تقدير الجهد للتعديل

| المرحلة | المهام | التقدير |
|---|---|---|
| **الأساسيات** | Data scraper + معالجة أساسية + baseline | شهر–شهران |
| **NLP الأساسي** | Naïve Bayes + Word Embedding + LSTM sentiment | شهران–3 أشهر |
| **النموذج الهجين** | دمج sentiment + time series + TFT | 2–3 أشهر |
| **MLOps** | MLflow + drift monitoring + auto-retrain | شهر–شهران |
| **الإنتاج الكامل** | API + تنبيهات + تقارير | شهر–شهرين |

---

### 10.4 خريطة التنفيذ المقترحة (بناءً على target.md)

```text
الشهر 1-2: الأساسات
├── Data Collector: sp-today + تلغرام + Investing.com
├── تخزين أولي: SQLite (ثم InfluxDB)
├── Feature Engineering: التعديلات المذكورة في §8
├── Baseline: XGBoost + HLT
└── Dashboard أولي: Streamlit (مُعدَّل من app.py)

الشهر 3-5: التعمق
├── Word Embedding عربي: Word2Vec + GloVe + FastText
├── مصنف المشاعر: LSTM + GloVe (الأفضل في الأدبيات)
├── هندسة ميزات متقدمة: ذهب + نفط + DXY + Mutual Information
└── Optuna لضبط كل النماذج

الشهر 6-9: النموذج الهجين
├── TFT على الميزات الكمية (Action كأساس)
├── دمج sentiment + time series
├── SHAP integration
└── MLflow tracking

الشهر 10+: الإنتاج والنضج
├── FastAPI
├── نظام تنبيهات تلغرام
├── auto-retrain pipeline
└── توسيع للذهب والمحروقات
```

---

## ملخص تنفيذي

| البُعد | التقييم |
|---|---|
| **جودة الكود** | ⭐⭐⭐⭐ — نظيف، موثق، قابل للتوسع |
| **ملاءمة للفوركس المتقدم** | ⭐⭐⭐ — يحتاج تعديلات جوهرية في طبقة البيانات |
| **جاهزية النموذج للاستعارة** | ⭐⭐⭐⭐⭐ — TFT + Quantile + Lightning قابل للاستخدام المباشر |
| **التعقيد المطلوب للتعديل** | متوسط-عالٍ (الصعوبة في البيانات وليس النماذج) |
| **التوصية النهائية** | استخدمه كأساس، لكن أعِد بناء طبقات البيانات والتخزين من صفر |

> **النقطة الأهم**: أصعب جزء في المشروع المستهدف ليس النمذجة (وهي موجودة في ACTION-main)، بل **جمع البيانات الموثوقة** من السوق غير الرسمي السوري وبناء نظام NLP عربي متخصص.
