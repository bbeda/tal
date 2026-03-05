import subprocess, os, re, sys
from collections import defaultdict

files = subprocess.check_output(['git', 'ls-files'], text=True).strip().split('\n')
files = [f for f in files if not any(x in f for x in ['node_modules', 'package-lock', '.lock', '.min.'])]

ext_stats = defaultdict(lambda: {'files': 0, 'lines': 0, 'non_blank': 0})
lang_stats = defaultdict(lambda: {'files': set(), 'lines': 0, 'non_blank': 0})

EXT_TO_LANG = {
    '.cs': 'C#', '.csproj': 'XML (MSBuild)', '.slnx': 'XML (Solution)',
    '.sln': 'XML (Solution)', '.fsproj': 'XML (MSBuild)', '.vbproj': 'XML (MSBuild)',
    '.ts': 'TypeScript', '.tsx': 'TypeScript (JSX)',
    '.js': 'JavaScript', '.jsx': 'JavaScript (JSX)', '.mjs': 'JavaScript', '.cjs': 'JavaScript',
    '.json': 'JSON', '.jsonc': 'JSON',
    '.md': 'Markdown', '.mdx': 'Markdown',
    '.css': 'CSS', '.scss': 'SCSS', '.sass': 'SASS', '.less': 'LESS',
    '.html': 'HTML', '.htm': 'HTML',
    '.xml': 'XML', '.svg': 'SVG',
    '.yaml': 'YAML', '.yml': 'YAML', '.toml': 'TOML',
    '.py': 'Python', '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust',
    '.java': 'Java', '.kt': 'Kotlin', '.swift': 'Swift',
    '.sh': 'Shell', '.bash': 'Shell', '.zsh': 'Shell', '.ps1': 'PowerShell',
    '.sql': 'SQL',
    '.http': 'HTTP',
    '.dockerfile': 'Docker', '.dockerignore': 'Docker',
    '.proto': 'Protobuf',
}

BASENAME_TO_LANG = {
    '.gitignore': 'Config', '.gitattributes': 'Config', '.editorconfig': 'Config',
    '.eslintrc': 'Config', '.prettierrc': 'Config', '.babelrc': 'Config',
    'Dockerfile': 'Docker', 'Makefile': 'Make',
}


def count_lines(text):
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    return len(lines), sum(1 for l in lines if l.strip())


for fpath in files:
    if not os.path.isfile(fpath):
        continue
    ext = os.path.splitext(fpath)[1] or '(no ext)'
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            total, non_blank = count_lines(content)
            ext_stats[ext]['files'] += 1
            ext_stats[ext]['lines'] += total
            ext_stats[ext]['non_blank'] += non_blank

            if ext == '.vue':
                # template -> HTML
                m = re.search(r'<template[^>]*>(.*?)</template>', content, re.DOTALL)
                if m:
                    tl, tnb = count_lines(m.group(1))
                    lang_stats['HTML']['files'].add(fpath)
                    lang_stats['HTML']['lines'] += tl
                    lang_stats['HTML']['non_blank'] += tnb

                # script -> TS or JS
                m = re.search(r'<script\b([^>]*)>(.*?)</script>', content, re.DOTALL)
                if m:
                    attrs = m.group(1)
                    sl, snb = count_lines(m.group(2))
                    is_ts = 'lang="ts"' in attrs or "lang='ts'" in attrs
                    lang = 'TypeScript' if is_ts else 'JavaScript'
                    lang_stats[lang]['files'].add(fpath)
                    lang_stats[lang]['lines'] += sl
                    lang_stats[lang]['non_blank'] += snb

                # style -> CSS/SCSS
                for sm in re.finditer(r'<style\b([^>]*)>(.*?)</style>', content, re.DOTALL):
                    attrs = sm.group(1)
                    stl, stnb = count_lines(sm.group(2))
                    is_scss = 'lang="scss"' in attrs or "lang='scss'" in attrs
                    slang = 'SCSS' if is_scss else 'CSS'
                    lang_stats[slang]['files'].add(fpath)
                    lang_stats[slang]['lines'] += stl
                    lang_stats[slang]['non_blank'] += stnb

                # Remaining lines (vue tags, whitespace between sections)
                lang_stats['Vue (markup)']['files'].add(fpath)
                accounted = 0
                for pat in [r'<template[^>]*>.*?</template>', r'<script\b[^>]*>.*?</script>', r'<style\b[^>]*>.*?</style>']:
                    for mm in re.finditer(pat, content, re.DOTALL):
                        al, _ = count_lines(mm.group(0))
                        accounted += al
                remaining = total - accounted
                if remaining > 0:
                    lang_stats['Vue (markup)']['lines'] += remaining
                    lang_stats['Vue (markup)']['non_blank'] += remaining
            else:
                # Direct file -> language mapping
                basename = os.path.basename(fpath)
                lang = BASENAME_TO_LANG.get(basename) or EXT_TO_LANG.get(ext)
                if not lang:
                    lang = ext if ext != '(no ext)' else 'Other'
                lang_stats[lang]['files'].add(fpath)
                lang_stats[lang]['lines'] += total
                lang_stats[lang]['non_blank'] += non_blank
    except Exception:
        pass

W = 60

# Report 1: By file extension
print('=' * W)
print('REPORT 1: Lines by file extension')
print('=' * W)
print(f'{"Extension":<14} {"Files":>6} {"Lines":>8} {"Non-blank":>10}')
print('-' * W)
sorted_exts = sorted(ext_stats.items(), key=lambda x: -x[1]['lines'])
total_f = total_l = total_nb = 0
for ext, s in sorted_exts:
    print(f'{ext:<14} {s["files"]:>6} {s["lines"]:>8,} {s["non_blank"]:>10,}')
    total_f += s['files']
    total_l += s['lines']
    total_nb += s['non_blank']
print('-' * W)
print(f'{"TOTAL":<14} {total_f:>6} {total_l:>8,} {total_nb:>10,}')
print()

# Report 2: By language (across all file types)
print('=' * W)
print('REPORT 2: Lines by language (across all file types)')
print('=' * W)
print(f'{"Language":<18} {"Files":>6} {"Lines":>8} {"Non-blank":>10}')
print('-' * W)
sorted_langs = sorted(lang_stats.items(), key=lambda x: -x[1]['lines'])
total_f2 = total_l2 = total_nb2 = 0
for lang, s in sorted_langs:
    fc = len(s['files'])
    print(f'{lang:<18} {fc:>6} {s["lines"]:>8,} {s["non_blank"]:>10,}')
    total_f2 += fc
    total_l2 += s['lines']
    total_nb2 += s['non_blank']
print('-' * W)
print(f'{"TOTAL":<18} {total_f2:>6} {total_l2:>8,} {total_nb2:>10,}')
print()
print('* File counts in Report 2 may exceed Report 1 totals because')
print('  multi-language files (e.g. .vue) contribute to multiple languages.')
