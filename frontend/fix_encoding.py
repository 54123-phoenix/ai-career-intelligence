import sys

# Fix growth/page.tsx
path = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth/page.tsx'
with open(path, 'r', encoding='utf-8') as fh:
    text = fh.read()

replacements = [
    ('"互联\ufffd?,"', '"互联网","'),
    ('parse \ufffd?retrieve \ufffd?re', 'parse → retrieve → re'),
    ('rse \ufffd?retrieve \ufffd?review \ufffd?arch', 'rse → retrieve → review → arch'),
    ('rieve \ufffd?review \ufffd?architect \ufffd?s', 'rieve → review → architect → s'),
    ('ew \ufffd?architect \ufffd?simulate \ufffd?fr', 'ew → architect → simulate → fr'),
    ('ect \ufffd?simulate \ufffd?frontend', 'ect → simulate → frontend'),
    ('education_level || "\ufffd?}</dd>', 'education_level || "—"}</dd>'),
    ('<div key={i}>\ufffd?{e}</div>', '<div key={i}>• {e}</div>'),
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        print('growth: replaced OK')
    else:
        print('growth: NOT FOUND')

with open(path, 'w', encoding='utf-8') as fh:
    fh.write(text)

count = text.count('\ufffd')
print('growth remaining:', count)

# Fix growth-v2/page.tsx
path2 = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth-v2/page.tsx'
with open(path2, 'r', encoding='utf-8') as fh:
    text2 = fh.read()

replacements2 = [
    ('"互联\ufffd?, source: "sa', '"互联网", source: "sa'),
    ('None \ufffd?show all</opt', 'None — show all</opt'),
    ('Basic \ufffd?mask PII</opt', 'Basic — mask PII</opt'),
    ('Full \ufffd?mask companie', 'Full — mask companie'),
    ('education_level || "\ufffd?}</dd>', 'education_level || "—"}</dd>'),
    ('text-blue-600">\ufffd?{flag.recomme', 'text-blue-600">→ {flag.recomme'),
    ('👍 This helps \ufffd?adopt this st', '👍 This helps — adopt this st'),
    ('Feedback sent \ufffd?weights will ', 'Feedback sent — weights will '),
    ('bel="Retrieval \ufffd?Reviewer"', 'bel="Retrieval ↔ Reviewer"'),
    ('xt-orange-500">\ufffd?off-path</spa', 'xt-orange-500">⚠ off-path</spa'),
    ('text-2xl mb-2">\ufffd?</div>', 'text-2xl mb-2">👆</div>'),
    ('<div key={i}>\ufffd?{e}</div>', '<div key={i}>• {e}</div>'),
]

for old, new in replacements2:
    if old in text2:
        text2 = text2.replace(old, new)
        print('growth-v2: replaced OK')
    else:
        print('growth-v2: NOT FOUND')

with open(path2, 'w', encoding='utf-8') as fh:
    fh.write(text2)

count2 = text2.count('\ufffd')
print('growth-v2 remaining:', count2)

if count == 0 and count2 == 0:
    print('All fixed!')
    sys.exit(0)
else:
    print('Some remain')
    sys.exit(1)
