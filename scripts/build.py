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
GOOGLE_TAG = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-HHVQNXLXCP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-HHVQNXLXCP');
</script>'''
RELEASE_DATA = json.loads((ROOT/'mdvu/data/release.json').read_text())
DIAGRAMS = json.loads((ROOT/'mdvu/data/diagram-compatibility.json').read_text())
PRODUCTS = json.loads((ROOT/'mdvu/data/comparison.json').read_text())['products']
REPORTED_RESULTS = {p['name']: p['reportedResults'] for p in PRODUCTS if 'reportedResults' in p}
APP_LABELS = {p['name']: p.get('displayName', p['name']) for p in PRODUCTS}
VERSION = RELEASE_DATA['version']
DOWNLOAD = RELEASE_DATA['packages']['macos.dmg']['url']
WINDOWS = RELEASE_DATA['packages'].get('windows-x86_64.msi', {}).get('url')
PREVIEW_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 3l6 6m12-6-6 6M3 21l6-6m12 6-6-6"/></svg>'


def display_name(name):
    return APP_LABELS.get(name, name)


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
    summary_rows = ''.join('<tr><th scope="row">'+escape(display_name(name))+'<small>'+escape(DIAGRAMS['applications'][name]['version'])+'</small></th>'+''.join('<td>'+str(DIAGRAMS['applications'][name]['summary'].get(key,0))+'</td>' for key in ['rendered','error','source'])+'</tr>' for name in names)
    summary = '<h2>'+t('Diagram formats','Форматы диаграмм')+'</h2><p class="comparison-note">'+t('The same 73 examples in cold and warm passes. Built-in renderers, no extra plugins. A diagram is counted only when drawn; source and errors are separate. This is a catalogue of MDVu-supported inputs, not every feature unique to other apps.', 'Одни и те же 73 примера в холодном и тёплом проходах. Встроенные движки, без дополнительных плагинов. Засчитывается нарисованная диаграмма; код и ошибки — отдельно. Каталог содержит поддерживаемые MDVu входные форматы, а не все уникальные возможности других приложений.')+'</p><div class="table-scroll" tabindex="0"><table class="performance-summary"><thead><tr><th>'+t('Application','Приложение')+'</th><th>'+t('Rendered','Отрисовано')+'</th><th>'+t('Error','Ошибка')+'</th><th>'+t('Source','Код')+'</th></tr></thead><tbody>'+summary_rows+'</tbody></table></div>'
    return summary+'<details><summary>'+t('All 73 diagram examples','Все 73 примера диаграмм')+'</summary><p class="comparison-note">'+t('Same valid sources, built-in engines. Errors and source code do not count as diagrams. This catalogue covers MDVu-supported inputs, not every feature unique to other apps.','Одинаковые валидные исходники, встроенные движки. Ошибки и исходный код не считаются диаграммами. Каталог охватывает входные форматы MDVu, а не все уникальные возможности других приложений.')+'</p><div class="table-scroll" tabindex="0"><table><thead><tr><th>ID</th><th>'+t('Format','Формат')+'</th>'+''.join('<th>'+escape(display_name(n))+'</th>' for n in names)+'</tr></thead><tbody>'+rows+'</tbody></table></div></details><div class="sources"><a href="/mdvu/data/test-diagrams.md">test-diagrams.md ↓</a><a href="/mdvu/data/diagram-compatibility.json">'+t('Results (JSON)','Результаты (JSON)')+' ↓</a></div>'

def landing_comparison(lang):
    def t(en, ru): return ru if lang == 'ru' else en
    verification = ROOT/'mdvu/data/verification-2026-10-19.json'
    data = json.loads((verification if verification.exists() else ROOT/'mdvu/data/full-pass-performance.json').read_text())
    records = {(r['app'], r['fixture']): r for r in data['measurements']
               if r.get('selectedForComparison', data.get('complete', False)) and r['cacheState'] == 'warm'}
    home = '/mdvu/' + ('ru/' if lang == 'ru' else '')
    headings = [t('Application', 'Приложение'), '<span title="'+t('Installed Universal app; excludes system browser runtime and user profiles', 'Установленное Universal-приложение; без системного браузерного движка и профилей')+'">'+t('Size · MiB', 'Размер · MiB')+'</span>', '<span title="'+t('Application memory in MiB; recorded sources in comparison data', 'Память приложения в MiB; источники сохранены в данных сравнения')+'">RAM · MiB</span>',
                '<span title="'+t('Warm process start to the first visible two-node Mermaid diagram; cached SVG allowed', 'Тёплый запуск до первой видимой Mermaid из двух узлов; допускается SVG из кеша')+'">'+t('Render · Page', 'Рендер · Страница')+'</span>', '<a href="'+home+'diagrams/">'+t('Formats', 'Форматы')+' ↗</a>']
    rows = []
    for app in data['apps']:
        name = app['name']
        light = records[name, 'common-test-light.md']
        graph = records[name, 'diagram-control.md']
        reported = REPORTED_RESULTS.get(name, {})
        graph_timing = {'launchToContentMs': reported['firstMermaidMs']} if 'firstMermaidMs' in reported else graph['timing']
        seconds = observed_seconds(graph_timing, 1).replace(' s', ' '+t('s', 'с'))
        rendered = sum(r['status'] == 'rendered' for r in DIAGRAMS['applications'][name]['results'].values())
        values = [f"{app['installedBytes']/1048576:.0f}",
                  f"{reported.get('ramMiB', light['memory']['medianMiBAt8s']):.0f}", seconds,
                  f'{rendered}/{len(DIAGRAMS["cases"])}']
        rows.append('<tr><th scope="row">'+escape(display_name(name))+'</th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
    return ('<section class="landing-comparison" id="comparison" aria-labelledby="comparison-title">'
            '<h2 id="comparison-title">'+t('Comparison', 'Сравнение')+'</h2>'
            '<div class="table-scroll" tabindex="0" role="region" aria-label="'+t('Application comparison', 'Сравнение приложений')+'">'
            '<table class="landing-table"><thead><tr>'+''.join('<th scope="col"><strong>'+h+'</strong></th>' for h in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
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
            rows.append('<tr><th scope="row">'+escape(display_name(app))+'<small>'+escape(fixture)+'</small></th>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
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
                rows.append('<tr><th scope="row">'+escape(display_name(name))+'<small>'+escape(app['version'])+'</small></th>'+''.join('<td>'+value+'</td>' for value in values)+'</tr>')
            html += '<h3>'+title+'</h3><div class="table-scroll" tabindex="0"><table class="performance-summary"><thead><tr>'+''.join('<th scope="col">'+heading+'</th>' for heading in headings)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
        html += '<p class="comparison-note">'+t('Universal app file bytes, counting symlinks once; system WebKit and browser profiles excluded. Light is the same 91,722-byte text fixture with diagram fences removed. RAM: median at 8 s / first-8-s peak. The Mermaid control is two nodes; full format coverage is reported separately.', 'Размер файлов Universal-приложения, симлинки учтены один раз; без системного WebKit и профилей браузера. Light — один и тот же текстовый файл, 91 722 байта, без блоков диаграмм. RAM: медиана на 8-й секунде / пик за первые 8 с. Контроль Mermaid содержит два узла; полная матрица форматов приведена отдельно.')+'</p>'
    html += '<details><summary>'+t('Method and scope','Методика и границы сравнения')+'</summary>'+method+'</details>'
    for group, title in groups:
        items = [(key, pair) for key, pair in pairs.items() if ('control' if key[1]=='diagram-control.md' else 'catalogue' if key[1]=='test-diagrams.md' else 'common' if key[1].startswith('common-') else 'original')==group]
        if items:
            note = t('RAM: median at 8 s / startup peak / full-pass peak. The full-pass peak includes later Accessibility overhead and is a diagnostic, not a clean startup-memory ranking.', 'RAM: медиана на 8-й секунде / пик старта / пик полного прохода. Последний включает накладные расходы Accessibility и служит диагностикой, а не чистым рейтингом памяти запуска.')
            html += '<details><summary>'+title+'</summary><p class="comparison-note">'+note+'</p>'+table(items)+'</details>'
    html += '<div class="sources"><a href="/mdvu/data/full-pass-performance.json">'+t('Every attempt (JSON)','Все попытки (JSON)')+' ↓</a><a href="/mdvu/data/BENCHMARK-PROTOCOL.md">'+t('Protocol','Методика')+' ↓</a></div>'
    verification = ROOT/'mdvu/data/verification-2026-10-19.json'
    if verification.exists():
        return verified_observations(json.loads(verification.read_text()), lang) + '<details><summary>'+t('18 October archive · superseded RAM attribution', 'Архив 18 октября · прежний учёт RAM')+'</summary><p class="comparison-note">'+t('The current comparison above replaces these older size, startup and RAM observations. The older sampler used temporal attribution for WebKit and did not consistently count other application-owned XPC services; use the new responsible-PID measurements for RAM comparisons.', 'Новое сравнение выше заменяет прежние наблюдения размера, старта и RAM. Старый стенд относил WebKit по времени запуска и не всегда учитывал другие XPC-службы приложения; для сравнения RAM используйте новые измерения с системной атрибуцией владельца.')+'</p>'+html+'</details>'
    return html


def observed_seconds(timing, precision=2):
    ms = timing.get('launchToContentMs')
    if ms is None:
        return 'N/A'
    if timing.get('frameGapMs', 0) >= 80 and 'firstPaintFrameBracketMs' in timing:
        low, high = timing['firstPaintFrameBracketMs']
        offset = ms - timing['dispatchToContentMs']
        return f'{(low+offset)/1000:.{precision}f}–{(high+offset)/1000:.{precision}f} s'
    return f'{ms/1000:.{precision}f} s'


def verified_observations(data, lang):
    def t(en, ru): return ru if lang == 'ru' else en
    records = {(r['app'], r['fixture'], r['cacheState']): r for r in data['measurements']}
    def table(headings, rows):
        return '<div class="table-scroll" tabindex="0"><table class="performance-summary"><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in headings)+'</tr></thead><tbody>'+''.join('<tr><th scope="row">'+escape(row[0])+'</th>'+''.join('<td>'+escape(str(v))+'</td>' for v in row[1:])+'</tr>' for row in rows)+'</tbody></table></div>'
    html = '<h2>'+t('Release 0.5.0 verification · 19 October', 'Проверка релиза 0.5.0 · 19 октября')+'</h2><p class="comparison-note">'+escape(data['machine'])+'</p><p class="comparison-note">'+t('Same inputs, one document per fresh process, built-in renderers. Cold clears identified application caches; the OS file cache remains. Warm follows a completed cold traversal. Times come from compositor frames and process birth, before input. Each cell is one observation, not a statistical ranking. Default window sizes differ between apps.', 'Одинаковые файлы, один документ на новый процесс, встроенные движки. Холодный запуск — после очистки известных кешей приложения; файловый кеш ОС остаётся. Тёплый — после полного холодного прохода. Время определяется по системным кадрам от рождения процесса, до ввода. Каждая ячейка — одно наблюдение, а не статистический рейтинг. Размеры окон по умолчанию различаются.')+'</p>'
    for phase in ['cold', 'warm']:
        rows = []
        for app in data['apps']:
            name = app['name']
            light = records[name, 'common-test-light.md', phase]
            graph = records[name, 'diagram-control.md', phase]
            reported = REPORTED_RESULTS.get(name, {}) if phase == 'warm' else {}
            graph_timing = {'launchToContentMs': reported['firstMermaidMs']} if 'firstMermaidMs' in reported else graph['timing']
            rows.append([display_name(name), f"{app['installedBytes']/1048576:.2f}", observed_seconds(light['timing']), observed_seconds(graph_timing), f"{reported.get('ramMiB', light['memory']['medianMiBAt8s']):.1f}"])
        html += '<h3>'+t('Cold start' if phase == 'cold' else 'Warm start', 'Холодный запуск' if phase == 'cold' else 'Тёплый запуск')+'</h3>'+table([t('Application', 'Приложение'), t('Size · MiB', 'Размер · MiB'), 'Light', t('First Mermaid', 'Первая Mermaid'), 'RAM · MiB'], rows)
    html += '<p class="comparison-note">'+t('The MacDown warm reference uses the maintainer’s final manual measurements: 201 MiB RAM and 1.1 s to the first diagram, supplied on 19 October. The original automated observations remain in the JSON evidence; no benchmark was rerun for this correction.', 'Для тёплого MacDown использованы окончательные ручные замеры автора: 201 MiB RAM и 1,1 с до первой диаграммы, переданные 19 октября. Исходные автоматические наблюдения сохранены в JSON; для этой поправки бенчмарк не перезапускался.')+'</p>'
    html += '<p class="comparison-note">'+t('Size is the complete Universal app, excluding mutable profiles and the system browser runtime. Light is the same 91,722-byte diagram-free derivative. RAM is summed physical footprint, median at seconds 7–8, including bundle processes, descendants and all system/XPC services owned by the app according to the OS responsible PID. The Mermaid control has two nodes; Render · Page is its first visible graph, not full-document completion. N/A means source was displayed instead of a diagram.', 'Размер — полное Universal-приложение без изменяемых профилей и системного браузерного движка. Light — одинаковый файл на 91 722 байта без диаграмм. RAM — суммарная физическая память, медиана на 7–8-й секунде: процессы приложения, потомки и все принадлежащие ему системные/XPC-службы по владельцу, указанному ОС. Контроль Mermaid содержит два узла; «Рендер · Страница» означает первую видимую диаграмму, а не готовность всего документа. N/A — вместо диаграммы показан код.')+'</p>'
    rows = [[display_name(r['app']), f"{r['medianSteadyMiB']:.1f}", f"{r['sampledPeakMiB']:.1f}"] for r in data['empty']]
    html += '<h3>'+t('No document', 'Без документа')+'</h3>'+table([t('Application', 'Приложение'), t('Settled RAM · MiB', 'RAM после стабилизации · MiB'), t('Observed peak · MiB', 'Наблюдаемый пик · MiB')], rows)+'<p class="comparison-note">'+t('Median at seconds 30–40. MDVu shows the system Open dialog; MacDown shows an empty Untitled document. These are different default states, not identical blank-viewer workloads.', 'Медиана на 30–40-й секунде. MDVu показывает системный диалог открытия; MacDown — пустой документ Untitled. Это разные стартовые состояния, а не одинаковая нагрузка пустого просмотрщика.')+'</p>'
    rows = []
    for r in data['measurements']:
        if r['fixture'] not in ['test-complete.md', 'test-heavy.md']: continue
        m = r['memory']
        rows.append([display_name(r['app'])+' · '+r['fixture']+' · '+r['cacheState'], f"{m['medianMiBAt8s']:.1f}", f"{m['medianMiBAfterEOF']:.1f}", f"{m['peakMiBFullPass']:.1f}"])
    html += '<h3>'+t('Complete and Heavy · RAM', 'Complete и Heavy · RAM')+'</h3>'+table([t('Application / file / phase', 'Приложение / файл / фаза'), t('At 8 s · MiB', 'На 8-й с · MiB'), t('After EOF · MiB', 'После EOF · MiB'), t('Pass peak · MiB', 'Пик прохода · MiB')], rows)+'<p class="comparison-note">'+t('After EOF is the median 5–10 seconds after verified arrival at the document end. The sampled pass peak includes traversal and Accessibility overhead; it is diagnostic, not clean startup RAM or rendering speed. Reaching EOF does not establish that every optional diagram is supported.', 'После EOF — медиана через 5–10 секунд после подтверждённого достижения конца документа. Пик выборки включает проход и накладные расходы Accessibility; это диагностика, а не чистая память старта или скорость рендера. EOF не доказывает поддержку каждой дополнительной диаграммы.')+'</p>'
    for outcome in data['boundedOutcomes']:
        html += '<p class="comparison-note">'+t(f"MacDown Heavy: the main process kernel lifetime peak reached {outcome['lifetimePeakBytes']/1048576:.1f} MiB. EOF remained unconfirmed after 7 min 42 s; warm was not run. This is a main-process lifetime counter, not the sampled concurrent process-tree peak in the table.", f"MacDown Heavy: системный счётчик пика основного процесса достиг {outcome['lifetimePeakBytes']/1048576:.1f} MiB. Через 7 мин 42 с EOF не подтверждён; тёплый проход не запускался. Это пик за время жизни основного процесса, а не пик одновременной выборки дерева процессов в таблице.")+'</p>'
    return html+'<div class="sources"><a href="/mdvu/data/verification-2026-10-19.json">'+t('Verified results (JSON)', 'Проверенные результаты (JSON)')+' ↓</a></div>'


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


def hero_screenshots(lang):
    labels = {'mac': 'macOS', 'win': 'Windows'}
    tabs, panels = [], []
    for platform, label in labels.items():
        selected = platform == 'mac'
        tabs.append(f'<button type="button" role="tab" id="tab-{platform}" aria-controls="screenshot-{platform}" aria-selected="{str(selected).lower()}" tabindex="{0 if selected else -1}" data-platform="{platform}">{label}</button>')
        alt = (f'MDVu на {label}: Markdown, формулы, выноски и диаграммы, оглавление и навигатор файлов' if lang == 'ru' else f'MDVu on {label} showing Markdown, math, callouts and diagrams, with a table of contents and file navigator')
        enlarge = f'Увеличить скриншот {label}' if lang == 'ru' else f'Enlarge the {label} screenshot'
        asset = f'/mdvu/assets/mdvu-{platform}'
        urls = {suffix: asset+suffix+'?v='+hashlib.sha256((ROOT/(asset+suffix).lstrip('/')).read_bytes()).hexdigest()[:12]
                for suffix in ('.jpg', '.webp', '-720.webp')}
        panels.append(f'<div id="screenshot-{platform}" role="tabpanel" aria-labelledby="tab-{platform}"{ " hidden" if not selected else ""}><a class="screenshot-link" href="{urls[".jpg"]}" data-preview aria-haspopup="dialog" aria-label="{enlarge}"><picture><source type="image/webp" srcset="{urls["-720.webp"]} 720w, {urls[".webp"]} 1440w" sizes="(max-width: 760px) 92vw, 55vw"><img class="app-screenshot" src="{urls[".jpg"]}" width="1440" height="1760" loading="{"eager" if selected else "lazy"}" fetchpriority="{"high" if selected else "auto"}" alt="{alt}"></picture>{preview_badge()}</a></div>')
    label = 'Платформа' if lang == 'ru' else 'Platform'
    return f'<figure class="hero-visual"><div class="platform-tabs" role="tablist" aria-label="{label}">{"".join(tabs)}</div>{"".join(panels)}</figure>'


def page(lang, section=None):
    ru = lang == 'ru'
    css_version = hashlib.sha256((ROOT/'mdvu/assets/site.css').read_bytes()).hexdigest()[:12]
    js_version = hashlib.sha256((ROOT/'mdvu/assets/site.js').read_bytes()).hexdigest()[:12]
    theme_version = hashlib.sha256((ROOT/'mdvu/assets/theme.js').read_bytes()).hexdigest()[:12]
    def t(en, ru_text): return ru_text if ru else en
    home = '/mdvu/' + ('ru/' if ru else '')
    url = ORIGIN + home + (section + '/' if section else '')
    title = t('MDVu — Ultrafast Markdown Viewer for Mac & Windows', 'MDVu — быстрый просмотрщик Markdown для Mac и Windows')
    description = t('A superlight, ultracompact Markdown viewer for Mac and Windows. Read MD files, Mermaid, PlantUML and LaTeX offline. Native, free and open source.', 'Компактный просмотрщик Markdown и MD-файлов для Mac и Windows. Диаграммы Mermaid, PlantUML и формулы LaTeX работают офлайн. Бесплатно, открытый код.')
    app_description = description
    if section:
        title = t('Markdown Viewer Performance Comparison', 'Быстродействие просмотрщиков Markdown') if section == 'performance' else t('Markdown Diagrams: Mermaid, PlantUML, C4 & More', 'Диаграммы Markdown: Mermaid, PlantUML, C4 и другие')
        title += ' — MDVu'
        description = (t('Compare Markdown viewers on the same files: application size, memory, cold and warm opening times, plus 73 diagram examples. Recorded methods and results.', 'Сравнение просмотрщиков Markdown на одинаковых файлах: размер, память, холодный и тёплый запуск, 73 примера диаграмм. Методика и результаты.') if section == 'performance' else t('73 Markdown diagram examples with source and rendered SVG: Mermaid, PlantUML, ZenUML, Graphviz DOT, C4 and ArchiMate. Browse the MDVu diagram gallery.', '73 примера диаграмм Markdown: исходный код и SVG для Mermaid, PlantUML, ZenUML, Graphviz DOT, C4 и ArchiMate. Галерея поддерживаемых форматов MDVu.'))
    def download_buttons():
        windows_download = ' download' if WINDOWS else ''
        windows_arrow = '↓' if WINDOWS else '↗'
        return f'<div class="hero-buttons"><a class="button" data-download-platform="mac" href="{DOWNLOAD}" download>macOS · DMG ↓</a><a class="button button-outline" data-download-platform="win" href="{WINDOWS or REPO + "/releases"}"{windows_download}>Windows · MSI {windows_arrow}</a></div><div class="download-links"><a href="{REPO}/releases">{t("Other versions · portable ZIPs", "Other versions · portable ZIPs")} ↗</a></div>'
    faqs = [
        (t('Which version is available?', 'Какая версия доступна?'), t('Download buttons always fetch the latest stable release. '+('Install it with the macOS DMG or Windows MSI, or choose portable ZIPs on GitHub Releases.' if WINDOWS else 'Download the macOS DMG or a portable ZIP on GitHub Releases. Windows packages are not available in this release.'), 'Кнопки скачивания всегда открывают последний стабильный релиз. '+('Установите его из DMG для macOS или MSI для Windows. Переносимые ZIP-архивы доступны на GitHub Releases.' if WINDOWS else 'Скачайте DMG для macOS или переносимый ZIP-архив на GitHub Releases. В этом релизе пакетов для Windows нет.'))),
        (t('What makes a Markdown viewer feel blazing fast?', 'За счёт чего MDVu работает быстро?'), t('Ultra-fast Markdown parsing comes from a shared Rust core. Native windows and diagram engines loaded only when needed keep the app supercompact. Cached SVGs speed up repeated opening; the comparison reports recorded size, memory and first-render times.', 'Общий парсер на Rust, нативные окна и движки диаграмм, которые загружаются по необходимости. Кеш SVG ускоряет повторное открытие документов. В таблице — реальные размер, память и время первого отображения на одном Mac.')),
        (t('Why choose an ultra-small Markdown viewer?', 'Зачем нужен компактный просмотрщик Markdown?'), t('A lightweight viewer opens your documents without a full editor or note-taking workspace. MDVu uses the system WebKit or WebView2 engine and compressed diagram libraries for an ultra-compact app with built-in Markdown, math and diagrams.', 'Лёгкий просмотрщик открывает документы без полноценного редактора или рабочего пространства заметок. MDVu использует системный WebKit или WebView2 и сжатые библиотеки диаграмм: компактное приложение с Markdown, формулами и диаграммами внутри.')),
        (t('What is a Markdown viewer?', 'Что такое просмотрщик Markdown?'), t('A Markdown viewer, also called an MD viewer, displays plain .md files as formatted documents, with readable headings, tables, code and links. MDVu provides a native Markdown preview on Mac and Windows, including offline math and diagram rendering.', 'Просмотрщик Markdown отображает обычные MD-файлы как оформленные документы: с заголовками, таблицами, кодом и ссылками. MDVu даёт нативный просмотр Markdown на Mac и Windows, включая локальное отображение формул и диаграмм.')),
        (t('Which Markdown files can I open?', 'Какие Markdown-файлы можно открыть?'), t('MDVu is an MD file viewer for .md, .markdown, .mdown and .mkd documents. Open a README, project documentation or a folder of notes directly from Finder, Explorer or the command line. The original Markdown files stay where they are.', 'MDVu открывает документы с расширениями .md, .markdown, .mdown и .mkd. Откройте README, документацию проекта или папку заметок прямо из Finder, Проводника или командной строки. Исходные Markdown-файлы остаются на своих местах.')),
        (t('Can I use MDVu as a live Markdown view?', 'Можно использовать MDVu для живого просмотра Markdown?'), t('MDVu is a dedicated viewer, not an editor. Write in your favorite editor and keep a live Markdown view beside it: saving the file refreshes the preview. Read, review and navigate without changing your workflow.', 'MDVu создан для просмотра. Пишите в любимом редакторе, а MDVu держите рядом: при сохранении файла документ обновляется автоматически. Это инструмент для чтения, проверки и навигации по Markdown.')),
        (t('Which systems are supported?', 'Какие системы поддерживаются?'), t('macOS 13+ on Apple Silicon and Intel; Windows 10/11 x64 with the Microsoft WebView2 runtime. Use DMG for Mac or MSI for Windows. Portable ZIPs cover Mac ARM, Universal, Intel and Windows x64. Windows distribution starts with 0.5.0.', 'macOS 13+ на Apple Silicon и Intel; Windows 10/11 x64 с Microsoft WebView2. Для Mac выбирайте DMG, для Windows — MSI. Portable ZIP: Mac ARM, Universal, Intel и Windows x64. Пакеты Windows выпускаются начиная с 0.5.0.')),
        (t('Does it really work offline?', 'Он действительно работает офлайн?'), t('Markdown, math and the bundled diagram engines render locally without a server, account or Java installation. Remote images or other external resources referenced by a document can still use the network. MDVu itself has no telemetry.', 'Markdown, формулы и встроенные движки диаграмм работают локально, без сервера, аккаунта и установки Java. Внешние изображения и другие удалённые ресурсы самого документа могут обращаться к сети. В MDVu нет телеметрии.')),
        (t('Can I open my Obsidian vault?', 'Можно открыть хранилище Obsidian?'), t('Yes. Open a folder or a Markdown file inside your vault. MDVu recognizes .obsidian and .git roots and supports callouts, wikilinks and media embeds. It does not run Obsidian plugins or replicate every vault feature.', 'Да. Откройте папку или Markdown-файл внутри хранилища. MDVu распознаёт корни .obsidian и .git, поддерживает выноски, вики-ссылки и медиа-вставки. Плагины Obsidian не запускаются; полного повторения всех его возможностей нет.')),
        (t('Why might macOS show a first-launch warning?', 'Почему macOS может показать предупреждение при запуске?'), t('Current macOS builds use ad-hoc signing, without Apple notarization. Gatekeeper may ask for an explicit first-launch approval. Download only from the project’s official releases, check the published SHA-256 checksum and follow the installation notes linked below.', 'Текущие сборки macOS подписаны ad-hoc, без нотариализации Apple. Gatekeeper может потребовать отдельного разрешения при первом запуске. Скачивайте приложение из официальных релизов, проверяйте опубликованную SHA-256-сумму и следуйте инструкции по установке ниже.')),
        (t('Is it free for commercial use?', 'Можно использовать бесплатно в работе?'), t('Yes. MDVu is released under the MIT license, with no subscription or paid feature tier. Bundled third-party components retain their own licenses, listed in the repository.', 'Да. MDVu распространяется под лицензией MIT, без подписки и платных уровней функций. Встроенные сторонние компоненты сохраняют собственные лицензии, перечисленные в репозитории.')),
    ]
    structured = {'@context':'https://schema.org','@graph':[
        {'@type':'SoftwareApplication','@id':BASE+'/#app','name':'MDVu','url':BASE+'/', 'applicationCategory':'UtilitiesApplication','operatingSystem':(['macOS 13+', 'Windows 10/11 x64'] if WINDOWS else ['macOS 13+']),'softwareVersion':VERSION,'description':app_description,'image':BASE+'/assets/mdvu-mac.jpg','screenshot':[BASE+'/assets/mdvu-mac.jpg',BASE+'/assets/mdvu-win.jpg'],'downloadUrl':[DOWNLOAD]+([WINDOWS] if WINDOWS else []),'sameAs':REPO,'isAccessibleForFree':True,'releaseNotes':REPO+'/releases/latest','featureList':['Native macOS and Windows Markdown viewer', 'CommonMark, GFM and Obsidian Markdown extensions', 'Offline Mermaid, PlantUML, ZenUML, Graphviz DOT, C4 and ArchiMate diagrams', 'LaTeX math with KaTeX and MathML', 'Search, outline, folder navigation and zoom'],'license':'https://opensource.org/license/mit','offers':{'@type':'Offer','price':'0','priceCurrency':'USD'},'author':{'@type':'Person','name':'Finn de Bear','url':'https://github.com/stpork'}},
        {'@type':'WebSite','@id':BASE+'/#website','name':'MDVu','alternateName':'MDVu Markdown Viewer','url':BASE+'/','inLanguage':['en','ru']},
        {'@type':'WebPage','@id':url+'#webpage','url':url,'name':title,'description':description,'inLanguage':lang,'isPartOf':{'@id':BASE+'/#website'},'about':{'@id':BASE+'/#app'}}
    ]}
    if section:
        breadcrumb = url+'#breadcrumb'
        structured['@graph'][2]['breadcrumb'] = {'@id': breadcrumb}
        structured['@graph'].append({'@type':'BreadcrumbList','@id':breadcrumb,'itemListElement':[{'@type':'ListItem','position':1,'name':'MDVu','item':ORIGIN+home},{'@type':'ListItem','position':2,'name':t('Performance','Быстродействие') if section == 'performance' else t('Diagrams','Диаграммы'),'item':url}]})
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
{GOOGLE_TAG}
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
</div>{hero_screenshots(lang)}</section>
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
<dialog class="image-dialog" aria-label="{t('Image preview','Просмотр изображения')}"><button type="button" class="close-dialog" aria-label="{t('Close preview','Закрыть изображение')}">✕</button><div class="preview-content" hidden></div><img width="1440" height="1760" alt="{t('Full MDVu application screenshot','Полный скриншот приложения MDVu')}"></dialog><div class="toast" role="status" aria-live="polite"></div>
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
    (ROOT/'404.html').write_text(f'''<!doctype html><html lang="en"><head>
{GOOGLE_TAG}
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#f7f9fc"><title>Page not found — MDVu</title><script src="/mdvu/assets/theme.js?v={theme_version}"></script><link rel="stylesheet" href="/mdvu/assets/site.css?v={css_version}"><link rel="icon" href="/mdvu/assets/favicon-96.png"></head><body><main class="container section"><div class="nav-wrap"><a class="brand" href="/mdvu/"><img src="/mdvu/assets/icon.webp" width="64" height="64" alt="">MDVu.</a>{theme_toggle('en')}</div><p class="eyebrow" style="margin-top:48px">404 / PAGE NOT FOUND</p><h1>A little detour.</h1><p class="section-intro">This page isn’t here. Your next Markdown viewer is.</p><a class="button" href="/mdvu/" style="margin-top:24px">Back to MDVu →</a></main></body></html>''')


    def redirect_page(target, lang):
        label = 'Открыть MDVu' if lang == 'ru' else 'Open MDVu'
        return f'''<!doctype html>
<html lang="{lang}"><head>
{GOOGLE_TAG}
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

    for route, stplayer_target in (
        ('stplayer', 'https://finndebear.github.io/stplayer/'),
        ('stplayer-releases', 'https://finndebear.github.io/stplayer/latest/'),
    ):
        stplayer_redirect = f'''<!doctype html>
<html lang="en"><head>
{GOOGLE_TAG}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>STPlayer has moved</title>
<link rel="canonical" href="{stplayer_target}">
<meta http-equiv="refresh" content="0;url={stplayer_target}">
<script>location.replace({json.dumps(stplayer_target)});</script>
</head><body><p><a href="{stplayer_target}">Open STPlayer</a></p></body></html>
'''
        directory = ROOT / route
        directory.mkdir(exist_ok=True)
        (directory / 'index.html').write_text(stplayer_redirect)


if __name__ == '__main__':
    main()
