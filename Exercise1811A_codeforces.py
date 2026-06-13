t = int(input())

for _ in range(t):
    
    n, d = map(int, input().split())
    
    s = input().strip()

    d = str(d)
    
    pos = len(s)

    for i in range(len(s)):
        
        if s[i] < d:
            
            pos = i
            
            break

    print(s[:pos] + d + s[pos:])
