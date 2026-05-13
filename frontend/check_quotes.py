path = 'C:/Users/Phoenix/Desktop/ai-career-intelligence/frontend/app/career/growth-lite/page.tsx'
with open(path, 'r', encoding='utf-8') as fh:
    lines = fh.readlines()

for i, line in enumerate(lines[:90], 1):
    q = line.count('"')
    if q % 2 != 0:
        print(f'Line {i} has {q} quotes')
