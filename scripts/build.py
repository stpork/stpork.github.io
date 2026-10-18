#!/usr/bin/env python3
"""Build both zero-dependency, fully rendered language versions."""
from pathlib import Path
import json
import hashlib
import re
from html import escape
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = 'https://stpork.github.io'
BASE = ORIGIN + '/mdvu'
REPO = 'https://github.com/stpork/mdvu'
RELEASE_DATA = json.loads((ROOT/'mdvu/data/release.json').read_text())
DIAGRAMS = json.loads((ROOT/'mdvu/data/diagram-compatibility.json').read_text())
VERSION = RELEASE_DATA['version']
DOWNLOAD = RELEASE_DATA['packages']['macos.dmg']['url']
WINDOWS = RELEASE_DATA['packages'].get('windows-x86_64.msi', {}).get('url')
PREVIEW_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 3l6 6m12-6-6 6M3 21l6-6m12 6-6-6"/></svg>'


def preview_badge():
    return '<span class="preview-zoom" aria-hidden="true">'+PREVIEW_ICON+'</span>'


def preview_button(label):
    return '<button class="preview-zoom" type="button" aria-haspopup="dialog" aria-label="'+escape(label)+'">'+PREVIEW_ICON+'</button>'


def theme_toggle(lang):
    def t(en, ru_text): return ru_text if lang == 'ru' else en
    return f'''<button class="theme-toggle" type="button" data-theme-toggle aria-label="{t('Switch theme','Сменить тему')}" title="{t('Switch theme','Сменить тему')}"><svg class="sun-icon" width="19" height="19" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="moon-icon" width="19" height="19" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14A9 9 0 0 1 10 3a9 9 0 1 0 10.5 11Z"/></svg></button>'''

def diagram_comparison(lang):
    def t(en, ru): return ru if lang == 'ru' else en
    names = list(DIAGRAMS['applications'])
    labels = {'rendered':t('Diagram','Диаграмма'), 'error':t('Error','Ошибка'), 'source':t('Code','Код')}
    rows = ''
    for case in DIAGRAMS['cases']:
        engine = 'Mermaid' if case['language'] in {'mermaid','zenuml'} else 'PlantUML'
        kind = case['kind'] if engine == 'Mermaid' else re.sub(r'^\d+(?:\.\d+)*\s+', '',case['heading'])
        rows += '<tr><th scope="row">'+case['id']+'</th><td>'+escape(engine+' / '+kind)+'</td>'+''.join('<td>'+labels[DIAGRAMS['applications'][name]['results'][case['id']]['status']]+'</td>' for name in names)+'</tr>'
    summary_rows = ''.join('<tr><th scope="row">'+escape(name)+'<small>'+escape(DIAGRAMS['applications'][name]['version'])+'</small></th>'+''.join('<td>'+str(DIAGRAMS['applications'][name]['summary'].get(key,0))+'</td>' for key in ['rendered','error','source'])+'</tr>' for name in names)
    summary = '<h2>'+t('Diagram formats','Форматы диаграмм')+'</h2><p class="comparison-note">'+t('The same 73 examples in cold and warm passes. Built-in renderers, no extra plugins. A diagram is counted only when drawn; source and errors are separate. This is a catalogue of MDVu-supported inputs, not every feature unique to other apps.', 'Одни и те же 73 примера в холодном и тёплом проходах. Встроенные движки, без дополнительных плагинов. Засчитывается нарисованная диаграмма; код и ошибки — отдельно. Каталог содержит поддерживаемые MDVu входные форматы, а не все уникальные возможности других приложений.')+'</p><div class="table-scroll" tabindex="0"><table class="performance-summary"><thead><tr><th>'+t('Application','Приложение')+'</th><th>'+t('Rendered','Отрисовано')+'</th><th>'+t('Error','Ошибка')+'</th><th>'+t('Source','Код')+'</th></tr></thead><tbody>'+summary_rows+'</tbody></table></div>'
    return summary+'<details><summary>'+t('All 73 diagram examples','Все 73 примера диаграмм')+'</summary><p class="comparison-note">'+t('Same valid sources, built-in engines. Errors and source code do not count as diagrams. This catalogue covers MDVu-supported inputs, not every feature unique to other apps.','Одинаковые валидные исходники, встроенные движки. Ошибки и исходный код не считаются диаграммами. Каталог охватывает входные форматы MDVu, а не все уникальные возможности других приложений.')+'</p><div class="table-scroll" tabindex="0"><table><thead><tr><th>ID</th><th>'+t('Format','Формат')+'</th>'+''.join('<th>'+escape(n)+'</th>' for n in names)+'</tr></thead><tbody>'+rows+'</tbody></table></div></details><div class="sources"><a href="/mdvu/data/COMPARISON.md">COMPARISON.md ↓</a><a href="/mdvu/data/test-diagrams.md">test-diagrams.md ↓</a><a href="/mdvu/data/diagram-compatibility.json">'+t('Results (JSON)','Результаты (JSON)')+' ↓</a></div>'

def landing_comparison(lang):
    def t(en, ru): return ru if lang == 'ru' else en
    data = json.loads((ROOT/'mdvu/data/full-pass-performance.json').read_text())
    records = {(r['app'], r['fixture']): r for r in data['measurements']
               if r.get('selectedForComparison') and r['cacheState'] == 'warm'}
    home = '/mdvu/' + ('ru/' if lang == 'ru' else '')
    headings = [t('Application', 'Приложение'), '<span title="'+t('Installed Universal app; excludes system browser runtime and user profiles', 'Установленное Universal-приложение; без системного браузерного движка и профилей')+'">'+t('Size · MiB', 'Размер · MiB')+'</span>', '<span title="'+t('Warm Light file; main and helper processes, median footprint at 7–8 seconds', 'Тёплый Light: память основного и вспомогательных процессов, медиана на 7–8-й секунде')+'">RAM · MiB</span>',
                '<span title="'+t('Warm process start to the first visible two-node Mermaid diagram; cached SVG allowed', 'Тёплый запуск до первой видимой Mermaid из двух узлов; допускается SVG из кеша')+'">'+t('Render · Page', 'Рендер · Страница')+'</span>', '<a href="'+home+'diagrams/">'+t('Formats', 'Форматы')+' ↗</a>']
    rows = []
    for app in data['apps']:
        name = app['name']
        light = records[name, 'common-test-light.md']
        graph = records[name, 'diagram-control.md']
        ms = graph['timing'].get('launchToContentMs')
        seconds = f'{ms/1000:.1f} '+t('s', 'с') if ms is not None else 'N/A'
        rendered = sum(r['status'] == 'rendered' for r in DIAGRAMS['applications'][name]['results'].values())
        values = [f"{app['installedBytes']/1048576:.0f}",
                  f"{light['memory']['medianMiBAt8s']:.0f}", seconds,
                  f'{rendered}/{len(DIAGRAMS["cases"])}']
        rows.append('<tr><th scope="row">'+escape(name)+'</th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
    return ('<section class="landing-comparison" id="comparison" aria-labelledby="comparison-title">'
            '<h2 id="comparison-title">'+t('Comparison', 'Сравнение')+'</h2>'
            '<div class="table-scroll" tabindex="0" role="region" aria-label="'+t('Application comparison', 'Сравнение приложений')+'">'
            '<table class="landing-table"><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
            '</section>')


def full_pass_observations(lang):
    def t(en, ru): return ru if lang == 'ru' else en
    path = ROOT/'mdvu/data/full-pass-performance.json'
    if not path.exists(): return ''
    data = json.loads(path.read_text())
    records = [r for r in data['measurements'] if r.get('selectedForComparison')]
    pairs = {}
    for row in records:
        pairs.setdefault((row['app'], row['fixture']), {})[row['cacheState']] = row
    for outcome in data.get('terminalOutcomes', []):
        pairs[outcome['app'], outcome['fixture']] = {'cold': dict(outcome['coldObservation'], boundedIncomplete=True), 'warm': {'warmBlocked': True}}
    def timing(row):
        if not row: return t('Pending', 'В работе')
        if row.get('warmBlocked'): return t('Not run: cold incomplete', 'Не запускался: холодный проход не завершён')
        if row.get('renderOutcome')=='html-source-fallback': return t('HTML source displayed', 'Показан HTML-код')
        if row.get('renderOutcome')=='source-displayed': return t('Source displayed', 'Показан код')
        info = row['timing']
        if 'launchToContentMs' not in info:
            return t('Source only', 'Исходный код') if row['app']=='MD Viewer' and row['fixture']=='diagram-control.md' else t('Frame analysis pending', 'Анализ кадров')
        ms = info['launchToContentMs']
        if info.get('frameGapMs', 0)>=80 and 'firstPaintFrameBracketMs' in info:
            low, high = info['firstPaintFrameBracketMs']
            offset = ms-info['dispatchToContentMs']
            return f'{(low+offset)/1000:.2f}–{(high+offset)/1000:.2f} s'+('†' if row.get('startupOnlyReview') else '')
        return (t('EOF not reached; text ', 'EOF не достигнут; текст ') if row.get('boundedIncomplete') else '')+f'{ms/1000:.2f} s'+('†' if row.get('startupOnlyReview') else '')
    def memory(row, full=False):
        if not row: return t('Pending', 'В работе')
        if row.get('warmBlocked'): return t('Not run', 'Не запускался')
        m = row['memory']
        value = f"{m['medianMiBAt8s']:.0f} / {m['peakMiBFirst8s']:.0f}"
        return value + (f" / {m['peakMiBFullPass']:.0f}"+("†" if row.get("startupOnlyReview") else "") if full else "")
    def table(items):
        headings = [t('Application / file','Приложение / файл'),t('Cold start','Холодный старт'),t('RAM · MiB','RAM · MiB'),t('Warm start','Тёплый старт'),t('RAM · MiB','RAM · MiB')]
        rows = []
        for (app, fixture), pair in sorted(items):
            values = [timing(pair.get('cold')), memory(pair.get('cold'), True), timing(pair.get('warm')), memory(pair.get('warm'), True)]
            rows.append('<tr><th scope="row">'+escape(app)+'<small>'+escape(fixture)+'</small></th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
        return '<div class="table-scroll" tabindex="0"><table class="performance-summary full-pass-table"><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
    total = data.get('verifiedCanonicalCells', 0)
    qualified = data.get('selectedMeasurementCells', total)
    intro = '<h2>'+t('Cold and warm starts','Холодные и тёплые запуски')+'</h2><p class="comparison-note">'+t('Same Mac, one document per fresh process. First readable body comes from system frames before any input; the Mermaid control requires the visible graph. RAM: median at 8 s / peak in the first 8 s, including helper processes. Application caches are cleared for cold starts; the OS file cache remains. Warm starts follow a complete cold traversal. First valid complete pair per file; later repeats remain in raw data.','Один Mac, один документ на новый процесс. Первое читаемое содержимое определяется по системным кадрам до любого ввода; в контроле Mermaid требуется готовая диаграмма. RAM: медиана на 8-й секунде / пик за первые 8 с, вместе со вспомогательными процессами. Перед холодным запуском очищаются кеши приложения; файловый кеш ОС остаётся. Тёплый запуск следует после полного холодного прохода. Выбрана первая валидная полная пара; повторы сохранены в исходных данных.')+'</p><p class="comparison-note">'+t(f'Verified full-document passes: {total} / 192. Frame intervals are shown when the capture cannot support a precise point value. Full traversal checks EOF, not rendering speed or automatic success of every diagram. Earlier calibration attempts are excluded.','Подтверждено полных проходов: '+str(total)+' / 192. При редких кадрах показан временной интервал. Проход проверяет конец файла, а не скорость рендера или успешность всех диаграмм. Калибровочные попытки исключены.')+'</p>'
    groups = [('common',t('Common content · diagram fences removed','Общее содержимое · без блоков диаграмм')),('original',t('Original project fixtures','Исходные фикстуры проекта')),('control',t('First Mermaid · two nodes','Первая Mermaid · два узла')),('catalogue',t('Complete 73-example document','Документ с 73 примерами'))]
    if data.get('terminalOutcomes'):
        intro += '<p class="comparison-note">'+t('Incomplete cold passes: '+str(len(data['terminalOutcomes']))+'. Their warm phase is not run; EOF failure is shown beside the first-text observation. These are bounded observations, not crash claims.', 'Незавершённых холодных проходов: '+str(len(data['terminalOutcomes']))+'. Их тёплая фаза не запускается; рядом со временем текста отмечен недостигнутый EOF. Это ограниченные наблюдения, а не утверждения о падении.')+'</p>'
    if any(r.get('startupOnlyReview') for r in records):
        intro += '<p class="comparison-note">'+t('† Startup timing and first-8-s RAM are qualified independently; later traversal was not confirmed by the input adapter. The paired cold pass completed. The later observed peak is not a full-file memory result.', '† Время старта и RAM за первые 8 с проверены отдельно; последующая прокрутка не подтверждена стендом. Парный холодный проход завершён. Поздний наблюдаемый пик не является памятью полного файла.')+'</p>'
    method = intro
    html = '<p class="comparison-note">'+t(f'Partial comparison: {qualified}/192 startup observations; {total}/192 full-document passes.', f'Неполное сравнение: {qualified}/192 наблюдений старта; {total}/192 полных проходов.')+'</p><p class="comparison-note">Apple M1 · 8 GiB · macOS 27.0.1 · 18 Oct 2026</p>'
    names = [app['name'] for app in data['apps']]
    if all(all(phase in pairs.get((name, 'common-test-light.md'), {}) for phase in ['cold', 'warm']) for name in names):
        for phase, title in [('cold', t('Cold start', 'Холодный старт')), ('warm', t('Warm start', 'Тёплый старт'))]:
            headings = [t('Application', 'Приложение'), t('App · MiB', 'Размер · MiB'), 'Light', t('First Mermaid', 'Первая Mermaid'), t('RAM · MiB', 'RAM · MiB')]
            rows = []
            for app in data['apps']:
                name = app['name']
                light = pairs[(name, 'common-test-light.md')][phase]
                graph = pairs.get((name, 'diagram-control.md'), {}).get(phase)
                values = [f"{app['installedBytes']/1048576:.2f}", timing(light), timing(graph), memory(light)]
                rows.append('<tr><th scope="row">'+escape(name)+'<small>'+escape(app['version'])+'</small></th>'+''.join('<td>'+value+'</td>' for value in values)+'</tr>')
            html += '<h3>'+title+'</h3><div class="table-scroll" tabindex="0"><table class="performance-summary"><thead><tr>'+''.join('<th scope="col">'+heading+'</th>' for heading in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
        html += '<p class="comparison-note">'+t('Universal app file bytes, counting symlinks once; system WebKit and browser profiles excluded. Light is the same 91,722-byte text fixture with diagram fences removed. RAM: median at 8 s / first-8-s peak. The Mermaid control is two nodes; full format coverage is reported separately.', 'Размер файлов Universal-приложения, симлинки учтены один раз; без системного WebKit и профилей браузера. Light — один и тот же текстовый файл, 91 722 байта, без блоков диаграмм. RAM: медиана на 8-й секунде / пик за первые 8 с. Контроль Mermaid содержит два узла; полная матрица форматов приведена отдельно.')+'</p>'
    html += '<details><summary>'+t('Method and scope','Методика и границы сравнения')+'</summary>'+method+'</details>'
    for group, title in groups:
        items = [(key, pair) for key, pair in pairs.items() if ('control' if key[1]=='diagram-control.md' else 'catalogue' if key[1]=='test-diagrams.md' else 'common' if key[1].startswith('common-') else 'original')==group]
        if items:
            note = t('RAM: median at 8 s / startup peak / full-pass peak. The full-pass peak includes later Accessibility overhead and is a diagnostic, not a clean startup-memory ranking.', 'RAM: медиана на 8-й секунде / пик старта / пик полного прохода. Последний включает накладные расходы Accessibility и служит диагностикой, а не чистым рейтингом памяти запуска.')
            html += '<details><summary>'+title+'</summary><p class="comparison-note">'+note+'</p>'+table(items)+'</details>'
    html += '<div class="sources"><a href="/mdvu/data/full-pass-performance.json">'+t('Every attempt (JSON)','Все попытки (JSON)')+' ↓</a><a href="/mdvu/data/BENCHMARK-PROTOCOL.md">'+t('Protocol','Методика')+' ↓</a></div>'
    return html


def diagram_preview(case, lang):
    title = escape(case['title'][lang])
    label = ('Увеличить: ' if lang == 'ru' else 'Enlarge: ') + title
    return (f'<a class="diagram-preview" href="{case["svg"]}" data-preview aria-haspopup="dialog" aria-label="{label}">'
            f'<img src="{case["svg"]}" width="{round(case["width"])}" height="{round(case["height"])}" loading="lazy" alt="{title}">{preview_badge()}</a>')


def diagram_gallery(lang):
    def t(en, ru): return ru if lang == 'ru' else en
    data = json.loads((ROOT/'mdvu/data/diagram-gallery.json').read_text())
    cards = []
    for case in data['cases']:
        title = case['title'][lang]
        wide = ' diagram-wide' if case['width'] / case['height'] > 3.2 else ''
        code = '```' + case['language'] + '\n' + case['source'] + '\n```'
        cards.append(f'<article class="diagram-card{wide}" id="{case["id"]}"><header><span>{escape(case["engine"])} · {case["id"]}</span><h2>{escape(title)}</h2></header><div class="diagram-example"><pre tabindex="0" aria-label="{t("Source code", "Исходный код")}"><code>{escape(code)}</code></pre><figure>{diagram_preview(case, lang)}</figure></div></article>')
    return '<div class="diagram-gallery">' + ''.join(cards) + '</div>'


def diagram_demo(case_id, panel, lang):
    case = next(c for c in json.loads((ROOT/'mdvu/data/diagram-gallery.json').read_text())['cases'] if c['id'] == case_id)
    code = '```' + case['language'] + '\n' + case['source'] + '\n```'
    title = escape(case['title'][lang])
    return (f'<div class="demo-panel diagram-demo" id="panel-{panel}" role="tabpanel" aria-labelledby="tab-{panel}" tabindex="0">'
            f'<div class="source-pane"><span class="pane-label">{escape(case["engine"])} · {title}</span><pre tabindex="0"><code>{escape(code)}</code></pre></div>'
            f'<div class="render-pane">{diagram_preview(case, lang)}</div></div>')


def page(lang, section=None):
    ru = lang == 'ru'
    css_version = hashlib.sha256((ROOT/'mdvu/assets/site.css').read_bytes()).hexdigest()[:12]
    js_version = hashlib.sha256((ROOT/'mdvu/assets/site.js').read_bytes()).hexdigest()[:12]
    theme_version = hashlib.sha256((ROOT/'mdvu/assets/theme.js').read_bytes()).hexdigest()[:12]
    def t(en, ru_text): return ru_text if ru else en
    home = '/mdvu/' + ('ru/' if ru else '')
    url = ORIGIN + home + (section + '/' if section else '')
    title = t('MDVu — Ultrafast Markdown Viewer for Mac & Windows', 'MDVu — быстрый просмотрщик Markdown для Mac и Windows')
    description = t('A supercompact MD file viewer for Mac and Windows. Read Markdown, diagrams and LaTeX offline. Native, free and open source, with Mermaid and PlantUML built in.', 'Компактный просмотрщик Markdown и MD-файлов для Mac и Windows. Диаграммы Mermaid, PlantUML и формулы LaTeX работают офлайн. Бесплатно, открытый код.')
    app_description = description
    if section:
        title = t('Markdown Viewer Performance Comparison', 'Быстродействие просмотрщиков Markdown') if section == 'performance' else t('Markdown Diagrams: Mermaid, PlantUML, C4 & More', 'Диаграммы Markdown: Mermaid, PlantUML, C4 и другие')
        title += ' — MDVu'
        description = (t('Compare Markdown viewers on the same files: application size, memory, cold and warm opening times, plus 73 diagram examples. Recorded methods and results.', 'Сравнение просмотрщиков Markdown на одинаковых файлах: размер, память, холодный и тёплый запуск, 73 примера диаграмм. Методика и результаты.') if section == 'performance' else t('73 Markdown diagram examples with source and rendered SVG: Mermaid, PlantUML, ZenUML, Graphviz DOT, C4 and ArchiMate. Browse the MDVu diagram gallery.', '73 примера диаграмм Markdown: исходный код и SVG для Mermaid, PlantUML, ZenUML, Graphviz DOT, C4 и ArchiMate. Галерея поддерживаемых форматов MDVu.'))
    def download_buttons():
        return f'<div class="hero-buttons"><a class="button" href="{DOWNLOAD}">macOS · DMG ↓</a><a class="button button-outline" href="{WINDOWS or REPO + "/releases"}">Windows · MSI ↗</a></div><div class="download-links"><a href="{REPO}/releases">{t("Other versions · portable ZIPs", "Other versions · portable ZIPs")} ↗</a></div>'
    preview_version = DIAGRAMS['applications']['MDVu']['version']
    faqs = [
        (t('Which version is available?', 'Какая версия доступна?'), t(f'The current public release is {VERSION}. '+('It is macOS-only. ' if not WINDOWS else '')+f'The features, 73-example gallery and comparison on this site describe the {preview_version} development build. '+('Windows MSI and ZIP are planned for that release.' if not WINDOWS else 'Download the available installers from the links above.'), f'Текущий публичный релиз — {VERSION}. '+('Он доступен только для macOS. ' if not WINDOWS else '')+f'Возможности, галерея из 73 примеров и сравнение на сайте относятся к разрабатываемой версии {preview_version}. '+('MSI и ZIP для Windows появятся с этим релизом.' if not WINDOWS else 'Доступные установщики — по ссылкам выше.'))),
        (t('What makes a Markdown viewer feel blazing fast?', 'За счёт чего MDVu работает быстро?'), t('A shared Rust parser, native windows and diagram engines loaded only when needed. Cached SVGs speed up repeated document opening. The comparison table reports observed size, memory and first-render times on the same Mac.', 'Общий парсер на Rust, нативные окна и движки диаграмм, которые загружаются по необходимости. Кеш SVG ускоряет повторное открытие документов. В таблице — реальные размер, память и время первого отображения на одном Mac.')),
        (t('What is a Markdown viewer?', 'Что такое просмотрщик Markdown?'), t('A Markdown viewer, also called an MD viewer, displays plain .md files as formatted documents, with readable headings, tables, code and links. MDVu provides a native Markdown preview on Mac and Windows, including offline math and diagram rendering.', 'Просмотрщик Markdown отображает обычные MD-файлы как оформленные документы: с заголовками, таблицами, кодом и ссылками. MDVu даёт нативный просмотр Markdown на Mac и Windows, включая локальное отображение формул и диаграмм.')),
        (t('Which Markdown files can I open?', 'Какие Markdown-файлы можно открыть?'), t('MDVu is an MD file viewer for .md, .markdown, .mdown and .mkd documents. Open a README, project documentation or a folder of notes directly from Finder, Explorer or the command line. The original Markdown files stay where they are.', 'MDVu открывает документы с расширениями .md, .markdown, .mdown и .mkd. Откройте README, документацию проекта или папку заметок прямо из Finder, Проводника или командной строки. Исходные Markdown-файлы остаются на своих местах.')),
        (t('Is MDVu an editor?', 'MDVu — это редактор?'), t('MDVu is a dedicated viewer. Write in your favorite editor and keep MDVu beside it: the file watcher refreshes the document when you save. It is made for reading, reviewing and navigating Markdown.', 'MDVu создан для просмотра. Пишите в любимом редакторе, а MDVu держите рядом: при сохранении файла документ обновляется автоматически. Это инструмент для чтения, проверки и навигации по Markdown.')),
        (t('Which systems are supported?', 'Какие системы поддерживаются?'), t('macOS 13+ on Apple Silicon and Intel; Windows 10/11 x64 with the Microsoft WebView2 runtime. Use DMG for Mac or MSI for Windows. Portable ZIPs cover Mac ARM, Universal, Intel and Windows x64. Windows distribution starts with 0.5.0.', 'macOS 13+ на Apple Silicon и Intel; Windows 10/11 x64 с Microsoft WebView2. Для Mac выбирайте DMG, для Windows — MSI. Portable ZIP: Mac ARM, Universal, Intel и Windows x64. Пакеты Windows выпускаются начиная с 0.5.0.')),
        (t('Does it really work offline?', 'Он действительно работает офлайн?'), t('Markdown, math and the bundled diagram engines render locally without a server, account or Java installation. Remote images or other external resources referenced by a document can still use the network. MDVu itself has no telemetry.', 'Markdown, формулы и встроенные движки диаграмм работают локально, без сервера, аккаунта и установки Java. Внешние изображения и другие удалённые ресурсы самого документа могут обращаться к сети. В MDVu нет телеметрии.')),
        (t('Can I open my Obsidian vault?', 'Можно открыть хранилище Obsidian?'), t('Yes. Open a folder or a Markdown file inside your vault. MDVu recognizes .obsidian and .git roots and supports callouts, wikilinks and media embeds. It does not run Obsidian plugins or replicate every vault feature.', 'Да. Откройте папку или Markdown-файл внутри хранилища. MDVu распознаёт корни .obsidian и .git, поддерживает выноски, вики-ссылки и медиа-вставки. Плагины Obsidian не запускаются; полного повторения всех его возможностей нет.')),
        (t('Why might macOS show a first-launch warning?', 'Почему macOS может показать предупреждение при запуске?'), t('Current macOS builds use ad-hoc signing, without Apple notarization. Gatekeeper may ask for an explicit first-launch approval. Download only from the project’s official releases, check the published SHA-256 checksum and follow the installation notes linked below.', 'Текущие сборки macOS подписаны ad-hoc, без нотариализации Apple. Gatekeeper может потребовать отдельного разрешения при первом запуске. Скачивайте приложение из официальных релизов, проверяйте опубликованную SHA-256-сумму и следуйте инструкции по установке ниже.')),
        (t('Is it free for commercial use?', 'Можно использовать бесплатно в работе?'), t('Yes. MDVu is released under the MIT license, with no subscription or paid feature tier. Bundled third-party components retain their own licenses, listed in the repository.', 'Да. MDVu распространяется под лицензией MIT, без подписки и платных уровней функций. Встроенные сторонние компоненты сохраняют собственные лицензии, перечисленные в репозитории.')),
    ]
    structured = {'@context':'https://schema.org','@graph':[
        {'@type':'SoftwareApplication','@id':BASE+'/#app','name':'MDVu','url':BASE+'/', 'applicationCategory':'UtilitiesApplication','operatingSystem':(['macOS 13+', 'Windows 10/11 x64'] if WINDOWS else ['macOS 13+']),'softwareVersion':VERSION,'description':app_description,'image':BASE+'/assets/mdvu.jpg','screenshot':BASE+'/assets/mdvu.jpg','downloadUrl':DOWNLOAD,'license':'https://opensource.org/license/mit','offers':{'@type':'Offer','price':'0','priceCurrency':'USD'},'author':{'@type':'Person','name':'Finn de Bear','url':'https://github.com/stpork'}},
        {'@type':'WebSite','@id':BASE+'/#website','name':'MDVu','url':BASE+'/','inLanguage':'en'},
        {'@type':'WebPage','@id':url+'#webpage','url':url,'name':title,'description':description,'inLanguage':lang,'isPartOf':{'@id':BASE+'/#website'},'about':{'@id':BASE+'/#app'}}
    ]}
    nav = [(t('Overview','Обзор'),home+'#why'),(t('Features','Возможности'),home+'#features'),(t('Diagrams','Диаграммы'),home+'diagrams/')]
    language_link = '<a class="language" href="/mdvu/'+(section+'/' if section else '')+'" lang="en" hreflang="en">EN</a>' if ru else ''
    nav_html = ''.join(f'<a href="{ident}">{label}</a>' for label,ident in nav)
    features = [
        ('01','macOS & Windows',t('Native windows, standard shortcuts and file dialogs. Open a document or folder, use the outline, search and zoom.', 'Нативные окна, стандартные горячие клавиши и файловые диалоги. Документы и папки, оглавление, поиск и масштабирование.'),'AppKit · Win32'),
        ('02',t('Diagrams and math','Диаграммы и формулы'),t('Mermaid, PlantUML, ZenUML and LaTeX formulas render offline. No plugins, diagram server or Java installation.', 'Mermaid, PlantUML, ZenUML и формулы LaTeX работают офлайн. Без плагинов, сервера диаграмм и установки Java.'),'Mermaid · PlantUML · ZenUML'),
        ('03',t('Local files','Локальные файлы'),t('Read your existing Markdown files and Obsidian vaults. Updates appear when you save. No account or telemetry.', 'Читайте существующие Markdown-файлы и хранилища Obsidian. Изменения отображаются при сохранении. Без аккаунта и телеметрии.'),'MIT · open source'),
    ]
    features_html = ''.join(f'<article class="principle"><span class="index">{n} /</span><h3>{h}</h3><p>{p}</p><span class="principle-tag">{tag}</span></article>' for n,h,p,tag in features)
    diagram_formats = [
        ('Mermaid', 'D001', t('Flowcharts, sequences, ER models, Gantt, pie charts, timelines and more.', 'Блок-схемы, последовательности, ER-модели, Gantt, круговые диаграммы, временные шкалы и другое.')),
        ('PlantUML', 'D038', t('UML, networks, JSON/YAML, wireframes and mind maps. No Java required.', 'UML, сети, JSON/YAML, прототипы интерфейсов и интеллект-карты. Без установки Java.')),
        ('ZenUML', 'D014', t('Sequence diagrams with calls, conditions and loops in concise code-like syntax.', 'Диаграммы последовательностей: вызовы, условия и циклы в компактном синтаксисе, похожем на код.')),
        ('Graphviz · DOT', 'D090', t('Directed graphs with Graphviz layout via Viz.js, inside @startdot blocks.', 'Ориентированные графы с компоновкой Graphviz через Viz.js, в блоках @startdot.')),
        ('C4', 'D100', t('Context, containers, components and deployment. Mermaid and C4-PlantUML syntax.', 'Контекст, контейнеры, компоненты и развёртывание. Синтаксис Mermaid и C4-PlantUML.')),
        ('ArchiMate', 'D110', t('Business, application and technology layers, with the ArchiMate library included.', 'Бизнес, приложения и технологии: библиотека ArchiMate уже включена.')),
    ]
    formats_html = ''.join(f'<div><h4><a href="{home}diagrams/#{case}">{name} ↗</a></h4><p>{text}</p></div>' for name, case, text in diagram_formats)
    dialects = [
        ('CommonMark / GFM',t('Tables, tasks, footnotes, autolinks and strikethrough. Shared Rust parser.', 'Таблицы, задачи, сноски, автоссылки и зачёркивание. Общий парсер на Rust.')),
        ('Obsidian',t('Callouts, collapsible notes, wikilinks and media embeds.', 'Выноски, сворачиваемые заметки, вики-ссылки и медиа-вставки.')),
        ('MkDocs',t('Admonitions with !!!, ??? and ???+ syntax.', 'Блоки примечаний с синтаксисом !!!, ??? и ???+.')),
        ('Docusaurus / VuePress',t('Fenced :::note, :::tip, :::warning and :::danger containers.', 'Контейнеры :::note, :::tip, :::warning и :::danger.')),
        ('CriticMarkup',t('Additions, deletions, substitutions, highlights and review comments.', 'Добавления, удаления, замены, выделение и комментарии рецензента.')),
        (t('And the useful details','И важные детали'),t('YAML frontmatter, GitLab TOC tokens, subscript, superscript and underline.', 'YAML frontmatter, оглавление GitLab, нижние и верхние индексы, подчёркивание.')),
    ]
    dialect_html = ''.join(f'<div><h4>{h}</h4><p>{p}</p></div>' for h,p in dialects)
    faq_items = [f'<details><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>' for q,a in faqs]
    midpoint = (len(faq_items) + 1) // 2
    faq_html = '<div class="faq-column">' + ''.join(faq_items[:midpoint]) + '</div><div class="faq-column">' + ''.join(faq_items[midpoint:]) + '</div>'
    html = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta name="google-site-verification" content="8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc">
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<meta name="robots" content="{'index, follow, max-image-preview:large'}">
<meta name="theme-color" content="#f7f9fc"><meta name="color-scheme" content="light dark">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="MDVu"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/assets/social.jpg"><meta property="og:image:width" content="1120"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="MDVu — native Markdown viewer for Mac and Windows"><meta property="og:locale" content="{'ru_RU' if ru else 'en_US'}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{description}"><meta name="twitter:image" content="{BASE}/assets/social.jpg"><meta name="twitter:image:alt" content="MDVu — native Markdown and MD file viewer">
<link rel="icon" type="image/png" sizes="96x96" href="/mdvu/assets/favicon-96.png"><link rel="apple-touch-icon" href="/mdvu/assets/apple-touch-icon.png"><script src="/mdvu/assets/theme.js?v={theme_version}"></script><link rel="stylesheet" href="/mdvu/assets/site.css?v={css_version}"><script src="/mdvu/assets/site.js?v={js_version}" defer></script>
<script type="application/ld+json">{json.dumps(structured,ensure_ascii=False,separators=(',',':'))}</script>
</head>
<body>
<a class="skip" href="#main">{t('Skip to content','Перейти к содержимому')}</a>
<header class="header"><div class="container nav-wrap"><a class="brand" href="{'/mdvu/ru/' if ru else '/mdvu/'}" aria-label="MDVu — {t('home','главная')}"><img src="/mdvu/assets/icon.webp" width="36" height="36" alt=""><span>MDVu<span class="brand-dot">.</span></span></a><nav aria-label="{t('Main navigation','Основная навигация')}">{nav_html}</nav><div class="nav-actions">{language_link}{theme_toggle(lang)}<a class="button button-small" href="{home}#download">{t('Get MDVu','Скачать')} <span aria-hidden="true">↗</span></a></div></div></header>
<main id="main">
<section class="hero container" aria-labelledby="hero-title"><div class="hero-copy">
<h1 id="hero-title"><span class="hero-category">MDVu · macOS &amp; Windows</span>{t('Markdown<br><span>viewer.</span>', 'Просмотрщик<br><span>Markdown.</span>')}</h1>
<p class="hero-description">{t('A superfast, ultracompact Markdown viewer. Mermaid, PlantUML, ZenUML and LaTeX built in. Open your files and folders, follow links, search and zoom. All rendered locally.', 'Быстрый и компактный просмотрщик Markdown. Mermaid, PlantUML, ZenUML и LaTeX уже внутри. Открывайте файлы и папки, переходите по ссылкам, ищите и меняйте масштаб. Всё рендерится локально.')}</p>
{download_buttons()}
<p class="hero-meta">macOS 13+ <span>·</span> Windows 10/11 x64 <span>·</span> {t('Free · MIT','Бесплатно · MIT')}</p>
<div class="hero-terminal"><span aria-hidden="true">$</span><code>brew install --cask stpork/tap/mdvu</code><button class="copy" type="button" data-copy="brew install --cask stpork/tap/mdvu" aria-label="{t('Copy Homebrew command','Скопировать команду Homebrew')}"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/></svg></button></div>
</div><figure class="hero-visual"><div class="visual-label">MDVu · macOS</div><a class="screenshot-link" href="/mdvu/assets/mdvu.jpg" data-preview aria-haspopup="dialog" aria-label="{t('Enlarge the MDVu screenshot','Увеличить скриншот MDVu')}"><picture><source type="image/webp" srcset="/mdvu/assets/mdvu-768.webp 768w, /mdvu/assets/mdvu.webp 1228w" sizes="(max-width: 760px) 92vw, 55vw"><img class="app-screenshot" src="/mdvu/assets/mdvu.jpg" width="1228" height="1317" fetchpriority="high" alt="{t('MDVu on macOS showing Markdown, math, callouts and diagrams, with a table of contents and file navigator','MDVu на macOS: Markdown, формулы, выноски и диаграммы, оглавление и навигатор файлов')}"></picture>{preview_badge()}</a></figure></section>
<div class="container comparison-section">{landing_comparison(lang)}</div>
<section class="section container overview" id="why" aria-label="{t('Overview','Обзор')}"><div class="principles">{features_html}</div></section>

<section class="feature-section section" id="features"><div class="container"><div class="split-heading"><div><p class="eyebrow">{t('FEATURES','ВОЗМОЖНОСТИ')}</p><h2>{t('Markdown, diagrams<br>and math.','Markdown, диаграммы<br>и формулы.')}</h2></div><p>{t('From notes and formulas to software architecture. Markdown dialects and diagram engines built in, with local rendering on Mac and Windows.', 'От заметок и формул до архитектуры систем. Диалекты Markdown и движки диаграмм встроены и работают локально на Mac и Windows.')}</p></div>
<div class="demo"><div class="demo-tabs"><div class="demo-tablist" role="tablist" aria-label="{t('Rendering examples','Примеры отображения')}"><button type="button" role="tab" id="tab-architecture" aria-controls="panel-architecture" aria-selected="true">{t('Architecture','Архитектура')}</button><button type="button" role="tab" id="tab-classes" aria-controls="panel-classes" aria-selected="false" tabindex="-1">{t('Classes','Классы')}</button><button type="button" role="tab" id="tab-flowcharts" aria-controls="panel-flowcharts" aria-selected="false" tabindex="-1">{t('Flowcharts','Блок-схемы')}</button><button type="button" role="tab" id="tab-sequence" aria-controls="panel-sequence" aria-selected="false" tabindex="-1">{t('Sequence','Последовательности')}</button><button type="button" role="tab" id="tab-math" aria-controls="panel-math" aria-selected="false" tabindex="-1">{t('Math','Формулы')}</button><button type="button" role="tab" id="tab-callouts" aria-controls="panel-callouts" aria-selected="false" tabindex="-1">{t('Callouts','Выноски')}</button></div><a class="demo-more" href="{home}diagrams/">{t('More…','Ещё…')}</a></div>
{diagram_demo('D110', 'architecture', lang)}
{diagram_demo('D040', 'classes', lang)}
{diagram_demo('D001', 'flowcharts', lang)}
{diagram_demo('D010', 'sequence', lang)}
<div class="demo-panel" id="panel-math" role="tabpanel" aria-labelledby="tab-math" tabindex="0"><div class="source-pane"><span class="pane-label">research.md</span><pre><code><span class="code-muted">## A little mathematical beauty</span>

Euler’s identity: <span class="code-blue">$e^&#123;i\\pi&#125; + 1 = 0$</span>

<span class="code-blue">$$</span>
\\int_&#123;-\\infty&#125;^&#123;\\infty&#125; e^&#123;-x^2&#125; dx
  = \\sqrt&#123;\\pi&#125;
<span class="code-blue">$$</span></code></pre><span class="source-note">LaTeX → KaTeX → MathML</span></div><div class="render-pane content-preview" data-preview-content="preview-math">{preview_button(t('Enlarge Math','Увеличить формулы'))}<span class="pane-label">{t('MATHEMATICS, NOT SCREENSHOTS','МАТЕМАТИКА, А НЕ СКРИНШОТЫ')}</span><div class="math-demo" id="preview-math"><math display="block"><msup><mi>e</mi><mrow><mi>i</mi><mi>π</mi></mrow></msup><mo>+</mo><mn>1</mn><mo>=</mo><mn>0</mn></math><math display="block"><msubsup><mo>∫</mo><mrow><mo>−</mo><mi>∞</mi></mrow><mi>∞</mi></msubsup><msup><mi>e</mi><mrow><mo>−</mo><msup><mi>x</mi><mn>2</mn></msup></mrow></msup><mi>d</mi><mi>x</mi><mo>=</mo><msqrt><mi>π</mi></msqrt></math></div><p>{t('Inline equations and display math, rendered with native browser MathML. No formula-font downloads.', 'Строчные и блочные формулы через нативный MathML. Без скачивания шрифтов для формул.')}</p></div></div>
<div class="demo-panel" id="panel-callouts" role="tabpanel" aria-labelledby="tab-callouts" tabindex="0"><div class="source-pane"><span class="pane-label">notes.md</span><pre><code><span class="code-blue">&gt; [!NOTE] Stay in context</span>
&gt; Your best ideas deserve a little space.

<span class="code-blue">&gt; [!TIP] Keep exploring</span>
&gt; Follow [[Architecture|the bigger picture]].</code></pre><span class="source-note">Obsidian · MkDocs · Docusaurus · VuePress</span></div><div class="render-pane content-preview" data-preview-content="preview-callouts">{preview_button(t('Enlarge Callouts','Увеличить выноски'))}<span class="pane-label">{t('GIVE THE IMPORTANT BITS A VOICE','ВАЖНОЕ НЕ ОСТАНЕТСЯ НЕЗАМЕЧЕННЫМ')}</span><div class="callouts-demo" id="preview-callouts"><div class="callout note"><strong>ⓘ Stay in context</strong><p>Your best ideas deserve a little space.</p></div><div class="callout tip"><strong>◇ Keep exploring</strong><p>Follow <span class="inline-link">the bigger picture</span>.</p></div></div><p>{t('Familiar syntax, readable structure. Your notes keep their meaning when you open them here.', 'Привычный синтаксис, понятная структура. Здесь ваши заметки сохраняют смысл и оформление.')}</p></div></div>
</div>
<div class="feature-group"><h3>{t('Diagram formats','Форматы диаграмм')}</h3><div class="dialects">{formats_html}</div></div>
<div class="feature-group"><h3>{t('Markdown dialects','Диалекты Markdown')}</h3><div class="dialects">{dialect_html}</div></div></div></section>

<section class="download-section" id="download"><div class="container download-layout"><div><img src="/mdvu/assets/icon.webp" width="88" height="88" loading="lazy" alt="MDVu"><p class="eyebrow">{t('INSTALLATION','УСТАНОВКА')}</p><h2>{t('Download MDVu','Скачать MDVu')}</h2><p>{t('DMG for Mac. MSI for Windows. Portable archives on GitHub Releases.', 'DMG для Mac. MSI для Windows. Portable-архивы в GitHub Releases.')}</p>{download_buttons()}{'' if WINDOWS else '<p class="download-meta">'+t('Windows MSI will be published with 0.5.0.', 'Windows MSI будет опубликован с релизом 0.5.0.')+'</p>'}<p class="portable-note">{t('Portable ZIPs: macOS ARM · Universal · Intel · Windows x64. All available variants live on GitHub Releases.', 'Portable ZIP: macOS ARM · Universal · Intel · Windows x64. Все доступные варианты — в GitHub Releases.')}</p></div><div class="install-card"><div class="install-heading"><span class="terminal-icon" aria-hidden="true">&gt;_</span><h3>Homebrew · macOS</h3></div><p>{t('Already using Homebrew? Install the app and its command-line tool together.', 'Пользуетесь Homebrew? Установите приложение и инструмент командной строки вместе.')}</p><div class="install-command"><code>brew install --cask stpork/tap/mdvu</code><button class="copy" type="button" data-copy="brew install --cask stpork/tap/mdvu" aria-label="{t('Copy Homebrew command','Скопировать команду Homebrew')}">{t('Copy','Копировать')}</button></div><div class="install-step"><span>01</span><p>{t('Mac: open the DMG and drag MDVu into Applications, or install with Homebrew.', 'Mac: откройте DMG и перенесите MDVu в «Программы» или установите через Homebrew.')}</p></div><div class="install-step"><span>02</span><p>{t('Windows: run the MSI for a current-user or all-user install. WebView2 must be installed. Then open a file or folder.', 'Windows: запустите MSI для текущего пользователя или всех пользователей. Требуется WebView2. Затем откройте файл или папку.')}</p></div><p class="install-note">{t('macOS builds are ad-hoc signed. macOS may require first-launch approval.', 'Сборки macOS подписаны ad-hoc. macOS может запросить разрешение на первый запуск.')} <a href="{REPO}#2-pre-built-release-downloads-github-releases">{t('Installation notes','Инструкция по установке')} ↗</a></p></div></div></section>
<section class="section container faq-section"><div><p class="eyebrow">FAQ</p><h2>{t('Questions and answers','Вопросы и ответы')}</h2><p>{t('More details in the','Подробнее — в')} <a href="{REPO}#readme">README ↗</a></p></div><div class="faq">{faq_html}</div></section>
</main>
<footer class="container footer"><a class="brand" href="{'/mdvu/ru/' if ru else '/mdvu/'}"><img src="/mdvu/assets/icon.webp" width="28" height="28" loading="lazy" alt=""><span>MDVu<span class="brand-dot">.</span></span></a><p>Markdown · Mermaid · PlantUML · ZenUML</p><nav aria-label="{t('Footer navigation','Ссылки в подвале')}"><a href="{REPO}/blob/develop/LICENSE">MIT License</a><a href="{REPO}/releases">{t('Changelog','Релизы')}</a><a href="{REPO}/issues">{t('Feedback','Обратная связь')} ↗</a></nav><small><a href="mailto:finndebear@gmail.com">© 2026 Finn de Bear</a></small></footer>
<dialog class="image-dialog" aria-label="{t('Image preview','Просмотр изображения')}"><button type="button" class="close-dialog" aria-label="{t('Close preview','Закрыть изображение')}">✕</button><div class="preview-content" hidden></div><img src="/mdvu/assets/mdvu.webp" width="1228" height="1317" loading="lazy" alt="{t('Full MDVu application screenshot','Полный скриншот приложения MDVu')}"></dialog><div class="toast" role="status" aria-live="polite"></div>
</body></html>'''
    if section:
        heading = t('Performance','Быстродействие') if section == 'performance' else t('Diagrams','Диаграммы')
        if section == 'performance':
            content = '<section class="section container" id="performance"><h1 class="page-title">'+heading+'</h1>'+full_pass_observations(lang)+diagram_comparison(lang)+'</section>'
        else:
            content = '<section class="section gallery-page"><div class="page-heading"><h1 class="page-title">'+heading+'</h1><p>'+t('73 examples. Source on the left, SVG rendered by MDVu on the right.', '73 примера. Слева исходный код, справа SVG, отрисованный в MDVu.')+'</p></div>'+diagram_gallery(lang)+'</section>'
        html = re.sub(r'(<main[^>]*>).*?(</main>)', lambda m: m[1]+content+m[2], html, flags=re.S)
        if section == 'performance':
            html = re.sub(r'<dialog .*?</dialog>', '', html, flags=re.S)
    return html

def main():
    for lang,path in [('en',ROOT/'mdvu/index.html'),('ru',ROOT/'mdvu/ru/index.html')]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page(lang))
        for section in ('performance','diagrams'):
            child = path.parent / section / 'index.html'
            child.parent.mkdir(exist_ok=True)
            child.write_text(page(lang,section))
    print('Built English and Russian pages.')

    css_version = hashlib.sha256((ROOT/'mdvu/assets/site.css').read_bytes()).hexdigest()[:12]
    theme_version = hashlib.sha256((ROOT/'mdvu/assets/theme.js').read_bytes()).hexdigest()[:12]
    (ROOT/'404.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#f7f9fc"><title>Page not found — MDVu</title><script src="/mdvu/assets/theme.js?v={theme_version}"></script><link rel="stylesheet" href="/mdvu/assets/site.css?v={css_version}"><link rel="icon" href="/mdvu/assets/favicon-96.png"></head><body><main class="container section"><div class="nav-wrap"><a class="brand" href="/mdvu/"><img src="/mdvu/assets/icon.webp" width="64" height="64" alt="">MDVu.</a>{theme_toggle('en')}</div><p class="eyebrow" style="margin-top:48px">404 / PAGE NOT FOUND</p><h1>A little detour.</h1><p class="section-intro">This page isn’t here. Your next Markdown viewer is.</p><a class="button" href="/mdvu/" style="margin-top:24px">Back to MDVu →</a></main></body></html>''')


    def redirect_page(target, lang):
        label = 'Открыть MDVu' if lang == 'ru' else 'Open MDVu'
        return f'''<!doctype html>
<html lang="{lang}"><head>
<meta charset="utf-8">
<meta name="google-site-verification" content="8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="{'noindex, follow' if lang == 'ru' else 'index, follow'}">
<title>MDVu — Markdown Viewer for Mac &amp; Windows</title>
<link rel="icon" type="image/png" sizes="96x96" href="/mdvu/assets/favicon-96.png">
<link rel="canonical" href="{ORIGIN}{target}">
<meta http-equiv="refresh" content="0;url={target}">
<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>
</head><body><p><a href="{target}">{label}</a></p></body></html>
'''

    (ROOT/'index.html').write_text(redirect_page('/mdvu/', 'en'))
    (ROOT/'ru').mkdir(exist_ok=True)
    (ROOT/'ru/index.html').write_text(redirect_page('/mdvu/ru/', 'ru'))


if __name__ == '__main__':
    main()
