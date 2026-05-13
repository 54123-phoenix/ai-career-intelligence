path = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth/page.tsx'
with open(path, 'r', encoding='utf-8') as fh:
    text = fh.read()

# Fix the over-replacement
if '"互联网","' in text:
    text = text.replace('"互联网","', '"互联网",')
    print('Fixed over-replacement in growth')
else:
    print('Pattern not found')

with open(path, 'w', encoding='utf-8') as fh:
    fh.write(text)

# Verify
idx = text.find('industry')
print('Context:', repr(text[idx:idx+20]))
