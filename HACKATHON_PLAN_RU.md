# Build with Gemma: Humor Genome NYC — стратегия проекта и Kaggle write-up

Дата анализа: 11 июля 2026  
Дедлайн по локальному описанию: 19 июля 2026  
Формат: judged hackathon, без leaderboard-метрики  
Основной публичный репозиторий: <https://github.com/qu1nty9/Build-with-Gemma---Humor-Genome>

## 1. Что лежит в исходной папке

В репозитории пока нет кода, датасетов, ноутбуков и экспериментов. Есть два исходных документа:

- `docs/Build with Gemma- ... - description.docx` — условия, критерии, сроки и требования к сабмиту.
- `docs/Room Sense Live - reference.docx` — пример концепта AI-аудитории для комика.

Из условия следует, что валидная заявка должна включать:

1. Kaggle Writeup до 1 500 слов.
2. Публичный репозиторий или публичный Kaggle Notebook.
3. Публичное демо-видео до 2 минут либо публичный live demo / clonable notebook.
4. Ясное объяснение того, как Gemma участвует в основном пользовательском опыте.

Критерии жюри:

| Критерий | Вес | Что должно быть видно в нашей работе |
|---|---:|---|
| Gemma Integration | 30% | Gemma выполняет уникальную центральную задачу; показаны модель, промпты/схемы, альтернативы и ограничения |
| Innovation & Impact | 30% | Необычная, но понятная идея с конкретной аудиторией и полезным feedback loop |
| Functionality | 20% | Стабильный end-to-end сценарий, который легко показать за 45–60 секунд |
| Presentation & Writeup | 20% | Чёткая история, архитектура, реальные результаты, честные ограничения, воспроизводимость |

Главный стратегический вывод: оптимизируем не сложность ML-системы и не количество функций, а произведение четырёх факторов: **оригинальная идея × незаменимая роль Gemma × надёжный wow-demo × доказательства**.

## 2. Что даёт референс Room Sense Live

Референс предлагает три режима: live-реакция аудитории, несколько персон и сравнение реакции двух типов зрителей. Публичный код референса реализован как браузерное приложение на Node/Express и использует Gemini Live, а не Gemma. Кроме того, конфигурационный endpoint отдаёт API-ключ фронтенду — такой паттерн нельзя переносить в наш проект.

Полезные уроки из референса:

- иммерсивный интерфейс и мгновенная обратная связь отлично работают в коротком видео;
- один ясный live-сценарий ценнее большого набора экранов;
- персоны легко превращаются в недоказуемую симуляцию аудитории;
- одних промптов «ты такой-то зритель» недостаточно для сильного технического вклада;
- нам нужно отличаться и концептуально, и технически: измерять юмористические механизмы, а не притворяться реальным залом.

## 3. Выбор идеи

### Кандидаты

Оценка по шкале 1–5; в колонке «Риск» 5 означает высокий риск не успеть.

| Идея | Gemma | Новизна | Demo | Доказуемость | Риск | Вывод |
|---|---:|---:|---:|---:|---:|---|
| Симулируемая AI-аудитория | 3 | 2 | 5 | 2 | 3 | Слишком близко к референсу |
| Кросс-культурный переводчик шуток | 4 | 5 | 4 | 4 | 3 | Сильный запасной вариант |
| Live improv partner | 4 | 3 | 5 | 2 | 5 | Сложный real-time и слабая оценка качества |
| Meme/caption generator | 3 | 2 | 4 | 3 | 2 | Реализуемо, но слишком типично |
| **Humor Genome Lab** | **5** | **5** | **4** | **5** | **3** | **Рекомендуемый проект** |

### Рекомендуемый проект

Рабочее название: **Humor Genome Lab**  
Альтернативное короткое имя продукта: **PunchLab**  
Подзаголовок: **Edit one comedy gene at a time—and see why the joke changes.**

Одно предложение:

> Humor Genome Lab превращает шутку или короткий фрагмент выступления в управляемую «карту механизмов», создаёт контрфактические версии с изменением ровно одного элемента и помогает автору понять, какая версия и почему работает лучше.

Целевая аудитория: начинающие и практикующие комики, сценаристы, преподаватели creative writing, исследователи computational humor.

Рекомендуемый трек: **Track 2 — Humor Understanding**. Генерация вариантов — способ исследовать механизм, а не самоцель. Если платформа позволяет прикрепить только один тематический трек, выбираем Understanding.

## 4. Пользовательский сценарий MVP

Один основной сценарий должен занимать меньше минуты:

1. Пользователь вставляет шутку или загружает/записывает аудио до 30 секунд.
2. Указывает контекст: аудитория, формат, желаемый тон и допустимый уровень риска.
3. Gemma строит **Humor Genome**:
   - premise;
   - setup;
   - audience assumption;
   - turn / incongruity;
   - punchline;
   - mechanism: misdirection, specificity, exaggeration, reversal, wordplay, callback и т. п.;
   - timing/verbosity signals;
   - cultural dependencies;
   - confidence и альтернативные интерпретации.
4. Пользователь выбирает один «ген» для редактирования: короче setup, сильнее misdirection, конкретнее образ, другой callback, меньше культурной зависимости.
5. Gemma генерирует 2–3 версии, меняя только выбранный механизм и сохраняя premise/voice.
6. Пользователь слепо сравнивает A/B, выбирает лучшую версию и видит объяснение различий.
7. Результат сохраняется как компактная карточка эксперимента: исходник, изменение, выбор человека, объяснение Gemma.

### Что не входит в MVP

- бесконечный чат;
- полноценная социальная сеть;
- live-симуляция смеха толпы;
- fine-tuning «ради галочки»;
- генерация видео/аватаров;
- сложная авторизация и биллинг;
- обещание предсказать реакцию реальной аудитории.

## 5. Почему Gemma здесь незаменима

Gemma должна использоваться минимум в трёх связанных шагах:

1. **Structured analysis** — разбор неоднозначного текста/аудио в валидируемую JSON-схему HumorGenome.
2. **Controlled counterfactual generation** — генерация версий при жёстких инвариантах: сохранить premise, voice и длину; изменить только выбранный механизм.
3. **Comparative explanation** — объяснение наблюдаемой разницы между A/B без заявления, что модель знает, что объективно смешнее.

Опционально:

4. **Preference memory** — краткое резюме реальных выборов пользователя, которое влияет на следующие предложения.
5. **Safety/context check** — выделение культурно зависимых предпосылок, punch-down риска и неоднозначных трактовок.

После локального latency spike зафиксирован следующий model split: **Gemma 4 E2B** — основной интерактивный runtime, **Gemma 4 12B instruction-tuned** — offline quality benchmark. На 16-ГБ M1 Pro E2B выполнила warm `analyze` за 15,6 секунды, тогда как 12B потребовалось 58,4 секунды на том же примере. После уточнения one-gene constraint E2B успешно завершила полный `analyze → mutate → compare` flow за 45,8 секунды; 12B остаётся эталонным «teacher/judge» вариантом.

До реализации необходимо подтвердить на странице соревнования, что выбранная версия Gemma допустима, и зафиксировать точное имя checkpoint, лицензию и runtime в README.

## 6. Архитектура

```text
Browser UI
  ├─ text / short audio input
  ├─ context controls
  ├─ genome visualization
  └─ blind A/B comparison
          │
          ▼
Python API (FastAPI)
  ├─ validation and rate limits
  ├─ session state
  ├─ prompt/version registry
  ├─ JSON schema validation + repair
  ├─ cache for deterministic demo cases
  └─ experiment logging (no secrets/client keys)
          │
          ▼
Gemma inference adapter
  ├─ analyze()
  ├─ mutate_one_gene()
  ├─ compare()
  └─ summarize_preferences()
          │
          ├─ Gemma 4 E2B: primary interactive path
          └─ Gemma 4 12B: offline quality comparison
```

Рекомендуемый стек:

- Frontend: Gradio для самого быстрого надёжного MVP либо React/Vite, только если polished UI можно собрать без задержки backend.
- Backend: FastAPI + Pydantic.
- Inference: Hugging Face Transformers / официальный Gemma runtime; абстракция адаптера обязательна.
- Storage: локальный JSONL/SQLite для анонимных сессий и результатов экспериментов.
- Tests: pytest для схем и пайплайна; Playwright или минимальный smoke test для главного UI-сценария.
- Deployment: Hugging Face Space, Cloud Run или другой публичный endpoint; модель и стоимость проверяются отдельным spike.

### Ключевые схемы данных

```text
HumorGenome
  input_text
  context
  premise
  setup
  assumptions[]
  turn
  punchline
  mechanisms[]
  timing_notes[]
  cultural_dependencies[]
  risks[]
  confidence
  alternative_readings[]

MutationRequest
  source_genome
  target_gene
  invariants[]
  number_of_variants

ExperimentResult
  source
  variants[]
  blind_order
  human_choice
  model_comparison
  latency_ms
  model_version
  prompt_version
```

## 7. Экспериментальная программа

### Исследовательский вопрос

> Может ли structured multi-pass pipeline на Gemma давать авторам более управляемые и объяснимые правки юмора, чем обычный one-shot prompt «сделай смешнее»?

### Baselines

1. One-shot: «Make this joke funnier».
2. One-shot + audience context.
3. Наш pipeline: parse genome → change one gene → compare.
4. Stretch: наш pipeline с preference memory.

### Набор оценки

Собрать 30–50 примеров из:

- собственных коротких шуток и безопасных тестовых строк;
- примеров с разрешающей лицензией / public domain;
- намеренно созданных контрфактических пар.

Не включать длинные защищённые авторским правом стендап-фрагменты в публичный репозиторий.

Для части примеров создать контролируемые ухудшения:

- punchline раскрыт в setup;
- удалён turn;
- добавлена лишняя длина;
- потерян callback;
- конкретный образ заменён абстрактным;
- культурная предпосылка сделана непонятной;
- изменено несколько механизмов сразу вопреки инструкции.

### Автоматические метрики

- JSON validity rate.
- Schema repair rate.
- Target-gene compliance: изменён ли выбранный механизм.
- Invariant preservation: сохранены ли premise, voice и ограничения длины.
- Defect identification accuracy на контролируемых ухудшениях.
- Pairwise ranking accuracy: распознаёт ли модель намеренно ухудшенную версию.
- Latency p50/p95.
- Repeatability при фиксированном seed/config.
- Failure rate и доля пустых/небезопасных ответов.

### Human evaluation

Минимально полезный тест: 5–10 участников × 10–15 слепых пар.

Вопросы по каждой паре:

1. Какая версия смешнее?
2. Какая лучше сохраняет голос автора?
3. Насколько полезно объяснение правки? 1–5.
4. Стало ли понятнее, какой механизм был изменён? 1–5.

Главная метрика для write-up: предпочтение нашего controlled pipeline относительно one-shot baseline. Отдельно показывать число оценщиков и доверительный интервал/разброс; не выдавать маленький пользовательский тест за научное доказательство.

### Ablations

- без audience context vs с контекстом;
- one-shot vs structured multi-pass;
- без инвариантов vs с инвариантами;
- E2B vs 12B на одном и том же наборе;
- text-only vs audio input для небольшой подвыборки.

### Три обязательных публичных кейса

1. Success: механизм найден, одно изменение улучшает результат.
2. Disagreement: пользователь предпочитает вариант, который Gemma ранжировала ниже.
3. Failure: wordplay/культурная зависимость разобраны неверно; показано, как система сообщает uncertainty.

## 8. План разработки по дням

### 11 июля — решение и de-risking

- зафиксировать problem statement, трек и одну hero-story;
- подтвердить точное время дедлайна и eligibility Gemma 4;
- проверить доступ к checkpoint и запуск E2B на целевой среде;
- получить один валидный HumorGenome JSON;
- сделать один controlled mutation;
- принять решение Gradio vs React по результатам spike.

Definition of done: один пример проходит через CLI/notebook от входа до A/B вариантов менее чем за 60 секунд.

### 12 июля — вертикальный backend slice

- Pydantic-схемы;
- Gemma adapter;
- analyze/mutate/compare endpoints;
- prompt versioning;
- JSON validation, retry и graceful error;
- 10 seed examples.

Definition of done: API стабильно прогоняет 10 примеров, не теряет модель/промпт metadata.

### 13 июля — главный интерфейс

- ввод текста и контекста;
- genome visualization;
- выбор одного гена;
- blind A/B cards;
- сохранение человеческого выбора;
- 2–3 визуально сильных demo cases.

Definition of done: новый пользователь проходит hero-flow без объяснений разработчика.

### 14 июля — данные и baseline

- 30–50 лицензированных/собственных примеров;
- генератор контролируемых ухудшений;
- one-shot baselines;
- evaluation script/notebook;
- автоматические метрики и таблица ошибок.

Definition of done: воспроизводимый evaluation run создаёт CSV/JSON результатов и минимум два графика/таблицы.

### 15 июля — human evaluation и model comparison

- слепая форма/режим оценки;
- собрать реальные оценки;
- сравнить E2B и 12B на подвыборке;
- провести ablations;
- выбрать финальный prompt/model config.

Definition of done: есть честная таблица результатов с n, baseline и минимум одним failure case.

### Фактический статус после calibration run 14 июля

- Собран и автоматически валидируется seed-набор из 10 project-original CC0 примеров; цель 30–50 ещё не достигнута.
- Готовы one-shot no-genome baseline, E2B pipeline runner, offline 12B teacher rubric и Markdown/JSON summaries.
- На четырёх brevity-кейсах pipeline завершил 3/4 записей и получил 5/6 passing variants по teacher rubric; baseline завершил 4/4, но получил 4/8 passing variants.
- Полностью прошли rubric 2/4 pipeline records против 1/4 baseline records. Это engineering calibration, не статистическое доказательство.
- `misdirection` возвращена в revalidation после изменения поведения локального Ollama structured runtime; `specificity` остаётся documented failure.
- Human blind A/B, held-out split, ablation и финальный prompt freeze ещё не выполнены и являются следующим обязательным рубежом.

### 16 июля — hardening и deployment

- публичный deployment;
- секреты только на сервере;
- rate limit, таймауты, retries;
- pre-warm и cache разрешённых demo cases;
- тест с чистого браузера без логина;
- README quickstart до 5 минут.

Definition of done: три последовательных end-to-end прогона на публичном URL без ручного вмешательства.

### 17 июля — write-up и видео

- заморозить scope;
- сделать архитектурную схему и скриншоты;
- написать черновик до 1 500 слов;
- записать видео по сценарию ниже;
- проверить, что в видео видны Gemma, продукт и измеримые результаты.

Definition of done: готов полный draft submission и video v1 длительностью не более 2 минут.

### 18 июля — submission freeze

- только bug fixes уровня demo-blocker;
- отредактировать write-up;
- добавить все публичные ссылки;
- проверить лицензии, attribution, отсутствие ключей и персональных данных;
- загрузить видео и отправить Writeup, не оставлять его draft;
- сохранить подтверждение сабмита.

Definition of done: валидный submitted Writeup за сутки до формального дедлайна.

### 19 июля — буфер

- проверить доступность ссылок в режиме инкогнито;
- исправлять только критические проблемы;
- повторно submit после изменений;
- не добавлять новые функции.

## 9. Структура публичного репозитория

Рабочая папка связана с репозиторием <https://github.com/qu1nty9/Build-with-Gemma---Humor-Genome>; основная ветка — `main`.

```text
humor-genome-lab/
  README.md
  LICENSE
  SECURITY.md
  .env.example
  pyproject.toml / requirements.txt
  app/
    api.py
    schemas.py
    config.py
    gemma_adapter.py
    prompts/
      analyze_v1.txt
      mutate_v1.txt
      compare_v1.txt
    services/
    ui/
  evaluation/
    README.md
    dataset_card.md
    examples.jsonl
    build_counterfactuals.py
    run_baselines.py
    evaluate.py
    human_eval_template.csv
  notebooks/
    01_gemma_smoke_test.ipynb
    02_evaluation.ipynb
  tests/
    test_schemas.py
    test_pipeline.py
    test_api.py
  assets/
    architecture.png
    hero_demo.gif
    results.png
  docs/
    MODEL_CARD.md
    PROMPT_CARD.md
    LIMITATIONS.md
    WRITEUP.md
```

README в первые 30 секунд должен отвечать на пять вопросов: что это, зачем, где live demo, где Gemma, как запустить.

## 10. План Kaggle write-up до 1 500 слов

### Заголовок и подзаголовок

**Humor Genome Lab**  
*Edit one comedy gene at a time—and see why the joke changes.*

### Story arc и бюджет слов

| Раздел | Слов | Содержание |
|---|---:|---|
| Hook | 80–100 | Одна шутка, два почти одинаковых варианта, совершенно разный эффект |
| Problem | 100–130 | «Сделай смешнее» не объясняет, что изменилось; симуляция аудитории не равна реальной реакции |
| What we built | 150–180 | Один сквозной пользовательский сценарий и три основных экрана |
| How Gemma powers it | 260–320 | Модель/checkpoint, три стадии, JSON schema, controlled generation, почему это не обычный chatbot |
| Architecture | 130–170 | Диаграмма, frontend/backend/inference, безопасность ключей, runtime |
| Evaluation and results | 220–280 | Baselines, датасет, human eval, метрики, честные числа и ablations |
| Challenges and decisions | 130–170 | Неоднозначность юмора, structured output, latency, почему отказались от ложного crowd prediction |
| Limitations and responsibility | 100–140 | Культура, bias, uncertainty, copyright, small-n human test |
| Reproducibility | 70–100 | Repo, notebook, prompt/model versions, quickstart |
| Conclusion | 50–80 | Один ясный вывод и следующий шаг |

Целевой объём: 1 350–1 450 слов, чтобы остался запас на подписи и правки.

### Что обязательно показать визуально

1. Hero screenshot: исходная шутка → genome → выбранный ген → две версии.
2. Одна компактная архитектурная диаграмма.
3. Одна таблица результатов baseline vs controlled pipeline.
4. Один success и один failure case.

### Правила текста

- начинать с результата/опыта, а не со списка технологий;
- не утверждать, что Gemma «знает, что смешно»;
- в каждом техническом разделе связывать решение с пользовательской ценностью;
- использовать точные названия моделей и версий;
- не писать ожидаемые метрики как уже достигнутые;
- не перегружать write-up кодом: дать 1–2 коротких фрагмента схемы, остальное — ссылками;
- явно назвать вклад каждого участника команды.

## 11. Сценарий demo video — максимум 2 минуты

| Время | Сцена | Сообщение |
|---|---|---|
| 0:00–0:08 | Две версии одной шутки | «Одно маленькое изменение может убить или спасти punchline» |
| 0:08–0:20 | Проблема | Обычный AI переписывает всё; автор не понимает причин |
| 0:20–0:55 | Live hero-flow | Ввод → Humor Genome → выбор «misdirection» → A/B |
| 0:55–1:15 | Human choice | Слепой выбор и объяснение ровно одного изменения |
| 1:15–1:35 | Under the hood | Gemma parse → controlled mutation → comparison; модель/checkpoint на экране |
| 1:35–1:50 | Evidence | Один график baseline, n human ratings, один failure case |
| 1:50–2:00 | Closing | «Не машина, которая решает, что смешно; инструмент, который делает редактирование проверяемым» |

Видео записывать только после feature freeze. Курсор и текст должны быть крупными; нельзя тратить время на установку, логин и длинные ожидания inference. Допустим монтаж, но основной сценарий должен быть настоящим работающим flow.

## 12. Риск-регистр

| Риск | Вероятность/ущерб | Митигация | Триггер отказа от функции |
|---|---|---|---|
| Gemma 4 не запускается на доступном железе | Средняя/высокий | Spike в первый день; E2B quantized; fallback Gemma 3 | Нет стабильного ответа к концу 11 июля |
| Аудио увеличивает latency/сложность | Высокая/средний | Text-first core; аудио как progressive enhancement | Аудио не стабильно к 14 июля |
| Модель меняет несколько «генов» | Высокая/высокий | Инварианты, JSON diff, validator, retry, human-visible warnings | Compliance ниже 80% на eval set |
| Слабый human eval | Средняя/высокий | Рано подготовить слепую форму; не обещать большие n | Недостаточно данных к 16 июля — оставить qualitative study |
| Live demo падает | Средняя/высокий | Pre-warm, cache seed cases, таймаут, recording fallback | Публичный URL не проходит 3 прогона 16 июля |
| Scope creep | Высокая/высокий | Один hero-flow; freeze 17 июля | Любая новая функция после freeze запрещена |
| Copyright/оскорбительный контент | Средняя/средний | Собственные/CC примеры, attribution, reporting, safety note | Спорные данные не публиковать |
| Секреты в клиенте/репозитории | Средняя/критический | Server-side env, secret scan, `.env.example` | Любая утечка блокирует публикацию |

## 13. Go / no-go gates

### Gate 1 — 11 июля

Go, если Gemma возвращает валидный genome и одну controlled mutation. Иначе упрощаем до text-only и меняем runtime/model, но не идею.

### Gate 2 — 14 июля

Go, если интерфейс завершает один сценарий и есть evaluation harness. Иначе отказываемся от audio, preference memory и любого fine-tuning.

### Gate 3 — 16 июля

Go, если deployment стабилен и получены реальные результаты. Иначе видео записывается локально, а обязательным публичным артефактом становится clonable Kaggle notebook.

### Gate 4 — 18 июля

Сабмит отправляется даже при отсутствии stretch-функций. Полнота заявки важнее последней фичи.

## 14. Матрица проверки против критериев жюри

### Gemma Integration — цель 27+/30

- конкретная Gemma model/version;
- Gemma участвует во всех трёх центральных шагах;
- structured schema и controlled constraints;
- comparison с baseline/другим размером модели;
- prompt/model cards и failure cases.

### Innovation & Impact — цель 26+/30

- юмор представлен как редактируемые механизмы;
- контрфактический эксперимент вместо ложной симуляции аудитории;
- конкретный пользователь и repeatable feedback loop;
- демонстрация пользы для обучения и авторской работы.

### Functionality — цель 18+/20

- публичный рабочий flow;
- три надёжных demo cases;
- корректные ошибки и таймауты;
- запуск по README;
- нет ключей во frontend.

### Presentation & Writeup — цель 18+/20

- видео не более 2 минут;
- write-up 1 350–1 450 слов;
- одна диаграмма, одна таблица, success + failure;
- все ссылки публичны без логина;
- Writeup имеет статус Submitted.

## 15. Финальный submission checklist

- [ ] Точный deadline/timezone перепроверен на Kaggle.
- [ ] Правильный Track выбран.
- [ ] Writeup отправлен, а не оставлен draft.
- [ ] Описание не превышает 1 500 слов.
- [ ] Видео публичное, без логина, не длиннее 2:00.
- [ ] Репозиторий публичный и имеет лицензию.
- [ ] Live demo доступен в инкогнито либо notebook клонируется.
- [ ] Указано точное имя Gemma checkpoint и способ запуска.
- [ ] Все результаты воспроизводимы и не являются «ожидаемыми» числами.
- [ ] Датасет имеет provenance и разрешающую лицензию.
- [ ] Нет API-ключей, токенов, `.env`, персональных данных и приватных URL.
- [ ] Есть limitations, safety и copyright notes.
- [ ] Указан вклад команды.
- [ ] Сделан последний smoke test всех ссылок.

## 16. Источники, использованные при планировании

- Локальное описание соревнования: `docs/Build with Gemma- Humor Genome NYC Build AI systems that understand, generate, and enhance humor through human-AI collaboration - description.docx`.
- Локальный референс: `docs/Room Sense Live - reference.docx`.
- Публичный референсный код: <https://github.com/michi883/room-sense-live>.
- Официальный выбор моделей Gemma: <https://ai.google.dev/gemma/docs/get_started>.
- Официальная model card Gemma 4: <https://ai.google.dev/gemma/docs/core/model_card_4>.
