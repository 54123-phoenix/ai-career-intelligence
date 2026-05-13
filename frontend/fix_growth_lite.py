path = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth-lite/page.tsx'
with open(path, 'rb') as fh:
    raw = fh.read()

# Fix missing closing quote after 互联网
bad = b'industry: "\xe4\xba\x92\xe8\x81\x94\xe7\xbd\x91, source: "'
good = b'industry: "\xe4\xba\x92\xe8\x81\x94\xe7\xbd\x91", source: "'

if bad in raw:
    raw = raw.replace(bad, good)
    print('Fixed growth-lite industry quote')
else:
    print('Pattern not found')

with open(path, 'wb') as fh:
    fh.write(raw)

# Verify
text = raw.decode('utf-8')
idx = text.find('industry')
print('Context:', repr(text[idx:idx+25]))
