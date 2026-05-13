# Fix growth remaining
path = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth/page.tsx'
with open(path, 'r', encoding='utf-8') as fh:
    text = fh.read()

old = '"互联\ufffd?,'
new = '"互联网","'
if old in text:
    text = text.replace(old, new)
    print('growth: replaced industry')
else:
    print('growth: NOT FOUND industry')

with open(path, 'w', encoding='utf-8') as fh:
    fh.write(text)

count = text.count('\ufffd')
print('growth remaining:', count)

# Fix growth-v2 remaining
path2 = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth-v2/page.tsx'
with open(path2, 'r', encoding='utf-8') as fh:
    text2 = fh.read()

old2 = '>\ufffd?/div>'
new2 = '>👆</div>'
if old2 in text2:
    text2 = text2.replace(old2, new2)
    print('growth-v2: replaced emoji')
else:
    print('growth-v2: NOT FOUND emoji')

with open(path2, 'w', encoding='utf-8') as fh:
    fh.write(text2)

count2 = text2.count('\ufffd')
print('growth-v2 remaining:', count2)
