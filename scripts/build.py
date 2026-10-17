#!/usr/bin/env python3
"""Build both zero-dependency, fully rendered language versions."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = 'https://stpork.github.io'
BASE = ORIGIN + '/mdvu'
REPO = 'https://github.com/stpork/mdvu'
RELEASE_DATA = json.loads((ROOT/'mdvu/data/release.json').read_text())
COMPARISON = json.loads((ROOT/'mdvu/data/comparison.json').read_text())
VERSION = RELEASE_DATA['version']
DOWNLOAD = RELEASE_DATA['packages']['macos.dmg']['url']
WINDOWS = RELEASE_DATA['packages'].get('windows-x86_64.msi', {}).get('url')


def theme_toggle(lang):
    def t(en, ru_text): return ru_text if lang == 'ru' else en
    return f'''<button class="theme-toggle" type="button" data-theme-toggle aria-label="{t('Switch theme','Сменить тему')}" title="{t('Switch theme','Сменить тему')}"><svg class="sun-icon" width="19" height="19" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="moon-icon" width="19" height="19" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14A9 9 0 0 1 10 3a9 9 0 1 0 10.5 11Z"/></svg></button>'''

def page(lang):
    ru = lang == 'ru'
    css_version = hashlib.sha256((ROOT/'mdvu/assets/site.css').read_bytes()).hexdigest()[:12]
    js_version = hashlib.sha256((ROOT/'mdvu/assets/site.js').read_bytes()).hexdigest()[:12]
    theme_version = hashlib.sha256((ROOT/'mdvu/assets/theme.js').read_bytes()).hexdigest()[:12]
    def t(en, ru_text): return ru_text if ru else en
    url = BASE + ('/ru/' if ru else '/')
    title = t('MDVu — Tiny, Fast Markdown Viewer for Mac & Windows', 'MDVu — компактный и быстрый Markdown для Mac и Windows')
    description = t('Native Markdown viewer for Mac and Windows. Mermaid, PlantUML, ZenUML and LaTeX math built in. Offline rendering, no plugins or Java. Free and open source.', 'Нативный просмотрщик Markdown для Mac и Windows. Mermaid, PlantUML, ZenUML и формулы LaTeX встроены. Офлайн, без плагинов и Java. Бесплатно, открытый код.')
    def download_buttons():
        return f'<div class="hero-buttons"><a class="button" href="{DOWNLOAD}">macOS · DMG ↓</a><a class="button button-outline" href="{WINDOWS or REPO + "/releases"}">Windows · MSI ↗</a></div><div class="download-links"><a href="{REPO}/releases">{t("Others · portable ZIPs", "Другие варианты · portable ZIP")} ↗</a></div>'
    products = COMPARISON['products']
    comparison_head = ''.join(f'<th scope="col"><a href="{product["source"]}">{product["name"]}</a><small>{product["version"]}</small></th>' for product in products)
    def size_cell(product, platform):
        package = product.get(platform)
        if package is None:
            return '—'
        return f'<a href="{package["source"]}">{package["bytes"]/1048576:.1f} MiB</a><small>{package["format"]}</small>'
    comparison_rows = [
        (t('macOS download', 'Загрузка для macOS'), [size_cell(p, 'macos') for p in products]),
        (t('Windows download', 'Загрузка для Windows'), [size_cell(p, 'windows') for p in products]),
        (t('Startup / rendering time', 'Запуск / рендеринг'), ['—'] * len(products)),
        (t('Purpose', 'Назначение'), [t(*p['purpose']) for p in products]),
        ('Mermaid', [t(*p['mermaid']) for p in products]),
        ('PlantUML', [t(*p['plantuml']) for p in products]),
        (t('Platforms', 'Платформы'), [p['platforms'] for p in products]),
        (t('License', 'Лицензия'), [t(*p['license']) for p in products]),
    ]
    comparison_rows_html = ''.join('<tr><th scope="row">'+label+'</th>'+''.join('<td>'+value+'</td>' for value in values)+'</tr>' for label,values in comparison_rows)
    comparison_sources = ''.join(f'<a href="{source["url"]}">{source["name"]} ↗</a>' for source in COMPARISON['sources'])
    faqs = [
        (t('What is a Markdown viewer?', 'Что такое просмотрщик Markdown?'), t('A Markdown viewer displays plain .md files as formatted documents, with readable headings, tables, code and links. MDVu provides a native Markdown preview on Mac and Windows, including offline math and diagram rendering.', 'Просмотрщик Markdown отображает обычные MD-файлы как оформленные документы: с заголовками, таблицами, кодом и ссылками. MDVu даёт нативный просмотр Markdown на Mac и Windows, включая локальное отображение формул и диаграмм.')),
        (t('Which Markdown files can I open?', 'Какие Markdown-файлы можно открыть?'), t('MDVu is an MD file viewer for .md, .markdown, .mdown and .mkd documents. Open a README, project documentation or a folder of notes directly from Finder, Explorer or the command line. The original Markdown files stay where they are.', 'MDVu открывает документы с расширениями .md, .markdown, .mdown и .mkd. Откройте README, документацию проекта или папку заметок прямо из Finder, Проводника или командной строки. Исходные Markdown-файлы остаются на своих местах.')),
        (t('Is MDVu an editor?', 'MDVu — это редактор?'), t('MDVu is a dedicated viewer. Write in your favorite editor and keep MDVu beside it: the file watcher refreshes the document when you save. It is made for reading, reviewing and navigating Markdown.', 'MDVu создан для просмотра. Пишите в любимом редакторе, а MDVu держите рядом: при сохранении файла документ обновляется автоматически. Это инструмент для чтения, проверки и навигации по Markdown.')),
        (t('Which systems are supported?', 'Какие системы поддерживаются?'), t('macOS 13+ on Apple Silicon and Intel; Windows 10/11 x64 with the Microsoft WebView2 runtime. Use DMG for Mac or MSI for Windows. Portable ZIPs cover Mac ARM, Universal, Intel and Windows x64. Windows distribution starts with 0.5.0.', 'macOS 13+ на Apple Silicon и Intel; Windows 10/11 x64 с Microsoft WebView2. Для Mac выбирайте DMG, для Windows — MSI. Portable ZIP: Mac ARM, Universal, Intel и Windows x64. Пакеты Windows выпускаются начиная с 0.5.0.')),
        (t('Does it really work offline?', 'Он действительно работает офлайн?'), t('Markdown, math and the bundled diagram engines render locally without a server, account or Java installation. Remote images or other external resources referenced by a document can still use the network. MDVu itself has no telemetry.', 'Markdown, формулы и встроенные движки диаграмм работают локально, без сервера, аккаунта и установки Java. Внешние изображения и другие удалённые ресурсы самого документа могут обращаться к сети. В MDVu нет телеметрии.')),
        (t('Can I open my Obsidian vault?', 'Можно открыть хранилище Obsidian?'), t('Yes. Open a folder or a Markdown file inside your vault. MDVu recognizes .obsidian and .git roots and supports callouts, wikilinks and media embeds. It does not run Obsidian plugins or replicate every vault feature.', 'Да. Откройте папку или Markdown-файл внутри хранилища. MDVu распознаёт корни .obsidian и .git, поддерживает выноски, вики-ссылки и медиа-вставки. Плагины Obsidian не запускаются; полного повторения всех его возможностей нет.')),
        (t('Why might macOS show a first-launch warning?', 'Почему macOS может показать предупреждение при запуске?'), t('Current macOS builds use ad-hoc signing, without Apple notarization. Gatekeeper may ask for an explicit first-launch approval. Download only from the project’s official releases, check the published SHA-256 checksum and follow the installation notes linked below.', 'Текущие сборки macOS подписаны ad-hoc, без нотариализации Apple. Gatekeeper может потребовать отдельного разрешения при первом запуске. Скачивайте приложение из официальных релизов, проверяйте опубликованную SHA-256-сумму и следуйте инструкции по установке ниже.')),
        (t('Is it free for commercial use?', 'Можно использовать бесплатно в работе?'), t('Yes. MDVu is released under the MIT license, with no subscription or paid feature tier. Bundled third-party components retain their own licenses, listed in the repository.', 'Да. MDVu распространяется под лицензией MIT, без подписки и платных уровней функций. Встроенные сторонние компоненты сохраняют собственные лицензии, перечисленные в репозитории.')),
    ]
    structured = {'@context':'https://schema.org','@graph':[
        {'@type':'SoftwareApplication','@id':BASE+'/#app','name':'MDVu','url':BASE+'/', 'applicationCategory':'UtilitiesApplication','operatingSystem':(['macOS 13+', 'Windows 10/11 x64'] if WINDOWS else ['macOS 13+']),'softwareVersion':VERSION,'description':description,'image':BASE+'/assets/mdvu.jpg','screenshot':BASE+'/assets/mdvu.jpg','downloadUrl':DOWNLOAD,'license':'https://opensource.org/license/mit','offers':{'@type':'Offer','price':'0','priceCurrency':'USD'},'author':{'@type':'Person','name':'Finn de Bear','url':'https://github.com/stpork'}},
        {'@type':'WebSite','@id':BASE+'/#website','name':'MDVu','url':BASE+'/','inLanguage':'en'},
        {'@type':'WebPage','@id':url+'#webpage','url':url,'name':title,'description':description,'inLanguage':lang,'isPartOf':{'@id':BASE+'/#website'},'about':{'@id':BASE+'/#app'}}
    ]}
    nav = [(t('Overview','Обзор'),'why'),(t('Features','Возможности'),'features'),('Performance','performance')]
    language_link = '<a class="language" href="/mdvu/" lang="en" hreflang="en">EN</a>' if ru else ''
    nav_html = ''.join(f'<a href="#{ident}">{label}</a>' for label,ident in nav)
    features = [
        ('01','macOS & Windows',t('Native windows, standard shortcuts and file dialogs. Open a document or folder, use the outline, search and zoom.', 'Нативные окна, стандартные горячие клавиши и файловые диалоги. Документы и папки, оглавление, поиск и масштабирование.'),'AppKit · Win32'),
        ('02',t('Diagrams and math','Диаграммы и формулы'),t('Mermaid, PlantUML, ZenUML and LaTeX formulas render offline. No plugins, diagram server or Java installation.', 'Mermaid, PlantUML, ZenUML и формулы LaTeX работают офлайн. Без плагинов, сервера диаграмм и установки Java.'),'Mermaid · PlantUML · ZenUML'),
        ('03',t('Local files','Локальные файлы'),t('Read your existing Markdown files and Obsidian vaults. Updates appear when you save. No account or telemetry.', 'Читайте существующие Markdown-файлы и хранилища Obsidian. Изменения отображаются при сохранении. Без аккаунта и телеметрии.'),'MIT · open source'),
    ]
    features_html = ''.join(f'<article class="principle"><span class="index">{n} /</span><h3>{h}</h3><p>{p}</p><span class="principle-tag">{tag}</span></article>' for n,h,p,tag in features)
    dialects = [
        ('CommonMark / GFM',t('Tables, tasks, footnotes, autolinks and strikethrough. Shared Rust parser.', 'Таблицы, задачи, сноски, автоссылки и зачёркивание. Общий парсер на Rust.')),
        ('Obsidian',t('Callouts, collapsible notes, wikilinks and media embeds.', 'Выноски, сворачиваемые заметки, вики-ссылки и медиа-вставки.')),
        ('MkDocs',t('Admonitions with !!!, ??? and ???+ syntax.', 'Блоки примечаний с синтаксисом !!!, ??? и ???+.')),
        ('Docusaurus / VuePress',t('Fenced :::note, :::tip, :::warning and :::danger containers.', 'Контейнеры :::note, :::tip, :::warning и :::danger.')),
        ('CriticMarkup',t('Additions, deletions, substitutions, highlights and review comments.', 'Добавления, удаления, замены, выделение и комментарии рецензента.')),
        (t('And the useful details','И важные детали'),t('YAML frontmatter, GitLab TOC tokens, subscript, superscript and underline.', 'YAML frontmatter, оглавление GitLab, нижние и верхние индексы, подчёркивание.')),
    ]
    dialect_html = ''.join(f'<div><h3>{h}</h3><p>{p}</p></div>' for h,p in dialects)
    faq_items = [f'<details><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>' for q,a in faqs]
    midpoint = (len(faq_items) + 1) // 2
    faq_html = '<div class="faq-column">' + ''.join(faq_items[:midpoint]) + '</div><div class="faq-column">' + ''.join(faq_items[midpoint:]) + '</div>'
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta name="google-site-verification" content="8hoHZ7azFNVSv9x07AUhAS5xpXH3vrk-LlH07z-cgBc">
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<meta name="robots" content="{'noindex, follow' if ru else 'index, follow, max-image-preview:large'}">
<meta name="theme-color" content="#f7f9fc"><meta name="color-scheme" content="light dark">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="MDVu"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/assets/social.jpg"><meta property="og:image:width" content="1120"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="MDVu — native Markdown viewer for Mac and Windows"><meta property="og:locale" content="{'ru_RU' if ru else 'en_US'}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{description}"><meta name="twitter:image" content="{BASE}/assets/social.jpg">
<link rel="icon" type="image/png" sizes="96x96" href="/mdvu/assets/favicon-96.png"><link rel="apple-touch-icon" href="/mdvu/assets/apple-touch-icon.png"><script src="/mdvu/assets/theme.js?v={theme_version}"></script><link rel="stylesheet" href="/mdvu/assets/site.css?v={css_version}"><script src="/mdvu/assets/site.js?v={js_version}" defer></script>
<script type="application/ld+json">{json.dumps(structured,ensure_ascii=False,separators=(',',':'))}</script>
</head>
<body>
<a class="skip" href="#main">{t('Skip to content','Перейти к содержимому')}</a>
<header class="header"><div class="container nav-wrap"><a class="brand" href="{'/mdvu/ru/' if ru else '/mdvu/'}" aria-label="MDVu — {t('home','главная')}"><img src="/mdvu/assets/icon.webp" width="36" height="36" alt=""><span>MDVu<span class="brand-dot">.</span></span></a><nav aria-label="{t('Main navigation','Основная навигация')}">{nav_html}</nav><div class="nav-actions">{language_link}{theme_toggle(lang)}<a class="button button-small" href="#download">{t('Get MDVu','Скачать')} <span aria-hidden="true">↗</span></a></div></div></header>
<main id="main">
<section class="hero container" aria-labelledby="hero-title"><div class="hero-copy">
<h1 id="hero-title"><span class="hero-category">MDVu · macOS &amp; Windows</span>{t('Markdown<br><span>viewer.</span>', 'Просмотрщик<br><span>Markdown.</span>')}</h1>
<p class="hero-description">{t('Mermaid, PlantUML, ZenUML and LaTeX formulas built in. Open documents and folders, follow links, search and zoom. Native, compact, offline.', 'Mermaid, PlantUML, ZenUML и формулы LaTeX встроены. Документы и папки, переходы по ссылкам, поиск и масштабирование. Нативный, компактный, офлайн.')}</p>
<div class="hero-buttons"><a class="button" href="{REPO}/releases">GitHub Releases ↗</a></div>
<p class="hero-meta">macOS 13+ <span>·</span> Windows 10/11 x64 <span>·</span> {t('Free · MIT','Бесплатно · MIT')}</p>
<div class="hero-terminal"><span aria-hidden="true">$</span><code>brew install --cask stpork/tap/mdvu</code><button class="copy" type="button" data-copy="brew install --cask stpork/tap/mdvu" aria-label="{t('Copy Homebrew command','Скопировать команду Homebrew')}"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/></svg></button></div>
</div><figure class="hero-visual"><div class="visual-label">MDVu · macOS</div><a class="screenshot-link" href="/mdvu/assets/mdvu.jpg" data-preview aria-label="{t('Enlarge the MDVu screenshot','Увеличить скриншот MDVu')}"><picture><source type="image/webp" srcset="/mdvu/assets/mdvu-768.webp 768w, /mdvu/assets/mdvu.webp 1228w" sizes="(max-width: 760px) 92vw, 55vw"><img class="app-screenshot" src="/mdvu/assets/mdvu.jpg" width="1228" height="1317" fetchpriority="high" alt="{t('MDVu on macOS showing Markdown, math, callouts and diagrams, with a table of contents and file navigator','MDVu на macOS: Markdown, формулы, выноски и диаграммы, оглавление и навигатор файлов')}"></picture></a></figure></section>
<section class="section container overview" id="why" aria-label="{t('Overview','Обзор')}"><div class="principles">{features_html}</div></section>
<section class="feature-section section" id="features"><div class="container"><div class="split-heading"><div><p class="eyebrow">{t('FEATURES','ВОЗМОЖНОСТИ')}</p><h2>{t('Markdown, diagrams<br>and math.','Markdown, диаграммы<br>и формулы.')}</h2></div><p>{t('CommonMark and GFM, plus syntax from Obsidian, MkDocs, Docusaurus and VuePress. Diagram and math engines are included.', 'CommonMark и GFM, а также синтаксис Obsidian, MkDocs, Docusaurus и VuePress. Движки диаграмм и формул включены в приложение.')}</p></div>
<div class="demo"><div class="demo-tabs" role="tablist" aria-label="{t('Rendering examples','Примеры отображения')}"><button type="button" role="tab" id="tab-diagrams" aria-controls="panel-diagrams" aria-selected="true">{t('Diagrams','Диаграммы')}</button><button type="button" role="tab" id="tab-math" aria-controls="panel-math" aria-selected="false" tabindex="-1">{t('Math','Формулы')}</button><button type="button" role="tab" id="tab-callouts" aria-controls="panel-callouts" aria-selected="false" tabindex="-1">{t('Callouts','Выноски')}</button></div>
<div class="demo-panel" id="panel-diagrams" role="tabpanel" aria-labelledby="tab-diagrams" tabindex="0"><div class="source-pane"><span class="pane-label">architecture.md</span><pre><code><span class="code-muted">```mermaid</span>
<span class="code-blue">flowchart</span> LR
  A[Your Markdown] --&gt; B&#123;MDVu&#125;
  B --&gt; C[Beautiful documents]
  B --&gt; D[Local rendering]
<span class="code-muted">```</span></code></pre><span class="source-note">Mermaid · PlantUML · ZenUML</span></div><div class="render-pane"><span class="pane-label">{t('THE IDEA, MADE VISIBLE','ИДЕЯ СТАНОВИТСЯ НАГЛЯДНОЙ')}</span><div class="flow" aria-label="Your Markdown → MDVu → Beautiful documents + Local rendering"><span class="flow-node">Your Markdown</span><span class="flow-arrow" aria-hidden="true">→</span><span class="flow-node flow-core">MDVu</span><span class="flow-arrow" aria-hidden="true">→</span><div class="flow-outputs"><span class="flow-node">Beautiful documents</span><span class="flow-node">Local rendering</span></div></div><p>{t('Architecture, sequences, charts and relationships. No diagram server. No Java install.', 'Архитектура, последовательности, графики и связи. Без сервера диаграмм. Без установки Java.')}</p></div></div>
<div class="demo-panel" id="panel-math" role="tabpanel" aria-labelledby="tab-math" tabindex="0"><div class="source-pane"><span class="pane-label">research.md</span><pre><code><span class="code-muted">## A little mathematical beauty</span>

Euler’s identity: <span class="code-blue">$e^&#123;i\\pi&#125; + 1 = 0$</span>

<span class="code-blue">$$</span>
\\int_&#123;-\\infty&#125;^&#123;\\infty&#125; e^&#123;-x^2&#125; dx
  = \\sqrt&#123;\\pi&#125;
<span class="code-blue">$$</span></code></pre><span class="source-note">LaTeX → KaTeX → MathML</span></div><div class="render-pane"><span class="pane-label">{t('MATHEMATICS, NOT SCREENSHOTS','МАТЕМАТИКА, А НЕ СКРИНШОТЫ')}</span><div class="math-demo"><math display="block"><msup><mi>e</mi><mrow><mi>i</mi><mi>π</mi></mrow></msup><mo>+</mo><mn>1</mn><mo>=</mo><mn>0</mn></math><math display="block"><msubsup><mo>∫</mo><mrow><mo>−</mo><mi>∞</mi></mrow><mi>∞</mi></msubsup><msup><mi>e</mi><mrow><mo>−</mo><msup><mi>x</mi><mn>2</mn></msup></mrow></msup><mi>d</mi><mi>x</mi><mo>=</mo><msqrt><mi>π</mi></msqrt></math></div><p>{t('Inline equations and display math, rendered with native browser MathML. No formula-font downloads.', 'Строчные и блочные формулы через нативный MathML. Без скачивания шрифтов для формул.')}</p></div></div>
<div class="demo-panel" id="panel-callouts" role="tabpanel" aria-labelledby="tab-callouts" tabindex="0"><div class="source-pane"><span class="pane-label">notes.md</span><pre><code><span class="code-blue">&gt; [!NOTE] Stay in context</span>
&gt; Your best ideas deserve a little space.

<span class="code-blue">&gt; [!TIP] Keep exploring</span>
&gt; Follow [[Architecture|the bigger picture]].</code></pre><span class="source-note">Obsidian · MkDocs · Docusaurus · VuePress</span></div><div class="render-pane"><span class="pane-label">{t('GIVE THE IMPORTANT BITS A VOICE','ВАЖНОЕ НЕ ОСТАНЕТСЯ НЕЗАМЕЧЕННЫМ')}</span><div class="callout note"><strong>ⓘ Stay in context</strong><p>Your best ideas deserve a little space.</p></div><div class="callout tip"><strong>◇ Keep exploring</strong><p>Follow <span class="inline-link">the bigger picture</span>.</p></div><p>{t('Familiar syntax, readable structure. Your notes keep their meaning when you open them here.', 'Привычный синтаксис, понятная структура. Здесь ваши заметки сохраняют смысл и оформление.')}</p></div></div>
</div><p class="demo-caption">{t('Illustrative syntax examples. See the actual MDVu rendering in the app screenshot above.', 'Иллюстрации синтаксиса. Реальный результат в MDVu показан на скриншоте приложения выше.')}</p>
<div class="dialects">{dialect_html}</div></div></section>
<section class="section container" id="performance"><div class="section-heading"><h2>Performance</h2><p>{t('MDVu, Typora, Obsidian, Marked and VS Code.', 'MDVu, Typora, Obsidian, Marked и VS Code.')}</p></div>
<div class="table-scroll" tabindex="0" role="region" aria-label="{t('Application comparison','Сравнение приложений')}"><table class="rivals"><caption>{t('Download sizes and capabilities','Размеры загрузки и возможности')}</caption><thead><tr><th scope="col">{t('Comparison','Сравнение')}</th>{comparison_head}</tr></thead><tbody>{comparison_rows_html}</tbody></table></div>
<p class="comparison-note">{t('Compressed downloads, not installed size or RAM. MDVu uses system WebKit/WebView2, not bundled runtimes. Package formats and known architectures are shown in each cell. MDVu 0.5.0: tested release candidate. Checked 17 Oct 2026. — means no verified data or no version for that OS.', 'Размер загрузки, не размер установленного приложения и не расход ОЗУ. MDVu использует системный WebKit/WebView2, не включая его в пакет. Форматы и известные архитектуры указаны в ячейках. MDVu 0.5.0 — проверенный кандидат в релиз. Проверено 17 октября 2026. — означает отсутствие подтверждённых данных или версии для этой ОС.')}</p>
<p class="comparison-note">{t('Comparable startup and rendering benchmarks are not available yet.', 'Сопоставимых тестов времени запуска и рендеринга пока нет.')}</p><div class="sources">{comparison_sources}</div></section>
<section class="download-section" id="download"><div class="container download-layout"><div><img src="/mdvu/assets/icon.webp" width="88" height="88" loading="lazy" alt="MDVu"><p class="eyebrow">{t('INSTALLATION','УСТАНОВКА')}</p><h2>{t('Download MDVu','Скачать MDVu')}</h2><p>{t('DMG for Mac. MSI for Windows. Portable archives on GitHub Releases.', 'DMG для Mac. MSI для Windows. Portable-архивы в GitHub Releases.')}</p>{download_buttons()}{'' if WINDOWS else '<p class="download-meta">'+t('Windows MSI will be published with 0.5.0.', 'Windows MSI будет опубликован с релизом 0.5.0.')+'</p>'}<p class="portable-note">{t('Portable ZIPs: macOS ARM · Universal · Intel · Windows x64. All available variants live on GitHub Releases.', 'Portable ZIP: macOS ARM · Universal · Intel · Windows x64. Все доступные варианты — в GitHub Releases.')}</p></div><div class="install-card"><div class="install-heading"><span class="terminal-icon" aria-hidden="true">&gt;_</span><h3>Homebrew · macOS</h3></div><p>{t('Already using Homebrew? Install the app and its command-line tool together.', 'Пользуетесь Homebrew? Установите приложение и инструмент командной строки вместе.')}</p><div class="install-command"><code>brew install --cask stpork/tap/mdvu</code><button class="copy" type="button" data-copy="brew install --cask stpork/tap/mdvu" aria-label="{t('Copy Homebrew command','Скопировать команду Homebrew')}">{t('Copy','Копировать')}</button></div><div class="install-step"><span>01</span><p>{t('Mac: open the DMG and drag MDVu into Applications, or install with Homebrew.', 'Mac: откройте DMG и перенесите MDVu в «Программы» или установите через Homebrew.')}</p></div><div class="install-step"><span>02</span><p>{t('Windows: run the MSI for a current-user or all-user install. WebView2 must be installed. Then open a file or folder.', 'Windows: запустите MSI для текущего пользователя или всех пользователей. Требуется WebView2. Затем откройте файл или папку.')}</p></div><p class="install-note">{t('macOS builds are ad-hoc signed. macOS may require first-launch approval.', 'Сборки macOS подписаны ad-hoc. macOS может запросить разрешение на первый запуск.')} <a href="{REPO}#2-pre-built-release-downloads-github-releases">{t('Installation notes','Инструкция по установке')} ↗</a></p></div></div></section>
<section class="section container faq-section"><div><p class="eyebrow">FAQ</p><h2>{t('Questions and answers','Вопросы и ответы')}</h2><p>{t('More details in the','Подробнее — в')} <a href="{REPO}#readme">README ↗</a></p></div><div class="faq">{faq_html}</div></section>
</main>
<footer class="container footer"><a class="brand" href="{'/mdvu/ru/' if ru else '/mdvu/'}"><img src="/mdvu/assets/icon.webp" width="28" height="28" loading="lazy" alt=""><span>MDVu<span class="brand-dot">.</span></span></a><p>Markdown · Mermaid · PlantUML · ZenUML</p><nav aria-label="{t('Footer navigation','Ссылки в подвале')}"><a href="{REPO}/blob/develop/LICENSE">MIT License</a><a href="{REPO}/releases">{t('Changelog','Релизы')}</a><a href="{REPO}/issues">{t('Feedback','Обратная связь')} ↗</a></nav><small><a href="mailto:finndebear@gmail.com">© 2026 Finn de Bear</a></small></footer>
<dialog class="image-dialog" aria-label="{t('MDVu screenshot','Скриншот MDVu')}"><button type="button" class="close-dialog" aria-label="{t('Close screenshot','Закрыть скриншот')}">✕</button><img src="/mdvu/assets/mdvu.webp" width="1228" height="1317" loading="lazy" alt="{t('Full MDVu application screenshot','Полный скриншот приложения MDVu')}"></dialog><div class="toast" role="status" aria-live="polite"></div>
</body></html>'''

def main():
    for lang,path in [('en',ROOT/'mdvu/index.html'),('ru',ROOT/'mdvu/ru/index.html')]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page(lang))
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
