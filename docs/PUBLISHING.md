# Как опубликовать ABLab на GitHub

Полная пошаговая инструкция: от пустого репо до работающего сайта `gobberz.github.io/ablab` и десктопных установщиков в Releases.

## Часть 1 — Публикация на GitHub Pages (5 минут)

Это основной путь — даёт публичный URL, работает всегда, ничего собирать не надо.

### Шаг 1. Создай репо на GitHub

1. Открой https://github.com/new
2. **Repository name:** `ablab`
3. **Description:** `A/B testing toolkit for quantitative experiment design and inference`
4. **Public** (чтобы Pages работал бесплатно и репо был виден в портфолио)
5. **БЕЗ** README / .gitignore / LICENSE — у нас уже есть свои
6. Жми **Create repository**

### Шаг 2. Залей код

В терминале, в папке с распакованным репо:

```bash
cd ablab/                                    # папка, что я тебе отдал
git init
git add .
git commit -m "feat: initial commit — ABLab v2.0 with 12 modules"
git branch -M main
git remote add origin https://github.com/Gobberz/ablab.git
git push -u origin main
```

### Шаг 3. Включи GitHub Pages

1. В репо открой **Settings** → **Pages** (в левом меню).
2. **Source:** выбери `GitHub Actions` (не `Deploy from a branch`).
3. Готово. Workflow `pages.yml` сам запустится при первом push.

### Шаг 4. Проверь деплой

1. Перейди во вкладку **Actions** репо — увидишь запущенный workflow `Deploy to GitHub Pages`.
2. Подожди ~30 секунд, пока станет зелёным.
3. Открой `https://gobberz.github.io/ablab/` — приложение работает.

**Готово.** Эту ссылку можно класть в резюме, LinkedIn, gobberz.com.

### Шаг 5 (опционально) — кастомный домен

Если хочешь `ablab.gobberz.com`:

1. В Settings → Pages добавь Custom domain → `ablab.gobberz.com`.
2. На Namecheap (где у тебя gobberz.com) добавь CNAME-запись:
   - Host: `ablab`
   - Value: `gobberz.github.io`
   - TTL: Automatic
3. Через ~10 минут включи **Enforce HTTPS** в Pages.

---

## Часть 2 — Десктопные установщики через Tauri (опционально)

Если хочешь, чтобы из Releases можно было скачать `.exe` / `.dmg` / `.AppImage`. Лучшая часть — собирать локально не нужно, всё делают сервера GitHub.

### Шаг 1. Создай и запушь тег

```bash
git tag v2.0.0
git push origin v2.0.0
```

### Шаг 2. Workflow стартует автоматически

Тег вида `v*` триггерит `desktop.yml`. Он параллельно:
- собирает на `windows-latest` → `ABLab_2.0.0_x64-setup.exe`
- на `macos-latest` → `ABLab_2.0.0_universal.dmg`
- на `ubuntu-22.04` → `ablab_2.0.0_amd64.AppImage` + `.deb`

Сборка занимает ~10–20 минут (Rust компилирует Tauri runtime для каждой платформы).

### Шаг 3. Опубликуй draft release

1. Перейди в **Releases** репо — там будет draft с прицепленными бинарниками.
2. Отредактируй описание (что нового), отметь **Set as latest release**, нажми **Publish**.
3. Кнопка **Download desktop app** в README теперь ведёт сюда.

### Что будет видеть пользователь

- **Windows:** двойной клик по `.exe` → стандартный установщик → ярлык на рабочем столе. SmartScreen может ругнуться («приложение неизвестного издателя») — стандартная история для несигнованных бинарников. Жмётся «Подробнее → Запустить всё равно». Чтобы убрать — нужен code signing certificate (~$200/год).
- **macOS:** `.dmg` → перетащить в Applications. Gatekeeper может ругнуться (нужно `xattr -d com.apple.quarantine /Applications/ABLab.app` или Apple Developer ID).
- **Linux:** `.AppImage` → `chmod +x ablab.AppImage && ./ablab.AppImage` — работает без установки.

---

## Часть 3 — Локальная разработка (если хочешь дорабатывать)

### Только веб (быстрая итерация)

```bash
# Просто открой файл в браузере
open src/index.html      # macOS
xdg-open src/index.html  # Linux
start src/index.html     # Windows
```

Любая правка → F5 в браузере → готово. Никакой сборки.

### С Tauri (для тестирования десктоп-приложения)

Требования: Node 18+, Rust (`rustup`), системные библиотеки для Tauri ([полный список](https://tauri.app/start/prerequisites/)).

```bash
npm install
npm run tauri:dev    # запускает приложение в dev-режиме
npm run tauri:build  # собирает релизный бинарник в src-tauri/target/release/bundle/
```

---

## Часть 4 — Что дописать в README после публикации

Когда репо живёт, обнови:

1. Замени бейдж демо-ссылки на актуальный URL (если используешь кастомный домен).
2. Сделай скриншот приложения, положи в `docs/screenshot.png`, добавь в README:
   ```markdown
   ![ABLab screenshot](docs/screenshot.png)
   ```
3. (Опционально) Добавь GIF с демо-прохождением модулей через [Kap](https://getkap.co/) или [LICEcap](https://www.cockos.com/licecap/).
4. Прицепи к LinkedIn-профилю как Project, поставь линк в hero gobberz.com.

---

## Часть 5 — Версионирование

Когда добавишь фичи и захочешь новый релиз:

1. Обнови `version` в `package.json` и `src-tauri/tauri.conf.json` (должны совпадать).
2. Закоммить.
3. `git tag v2.1.0 && git push origin v2.1.0` — workflow соберёт новые бинарники.

Используй [SemVer](https://semver.org/lang/ru/):
- `2.0.1` — багфикс
- `2.1.0` — новая фича без поломки совместимости
- `3.0.0` — breaking change (например, поменялся формат CSV)

---

## Troubleshooting

**Pages деплоится, но 404.**
В Settings → Pages проверь, что Source = GitHub Actions (не Branch). Подожди ещё 1 минуту после первого запуска — DNS-кэш у GitHub.

**Tauri build падает на Windows с `webview2 not found`.**
В workflow есть `windows-latest` — там всё уже стоит. Если собираешь локально — поставь WebView2 Runtime: https://developer.microsoft.com/microsoft-edge/webview2/.

**Tauri build падает на Linux.**
Нужны `libwebkit2gtk-4.1-dev` и пара других пакетов — в workflow они уже стоят. Локально:
```bash
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
```

**Хочу поменять иконку.**
Замени `src-tauri/icons/icon.svg`, перезапусти `python3 scripts/gen_icons.py` (нужны `cairosvg` и `Pillow`).

**Workflow desktop.yml висит на «waiting for runner».**
Бесплатные GitHub Actions limits на private репо: 2000 минут/месяц. На public — unlimited. У тебя репо public → проблем не будет.

---

Если что-то не получится — скинь скриншот ошибки, разберём.
