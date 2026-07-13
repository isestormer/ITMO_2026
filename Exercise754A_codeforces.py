n = int(input())

a = list(map(int, input().split()))

if sum(a) != 0:
    
    print("YES")
    
    print(1)
    
    print(1, n)
    
else:
    
    pos = -1

    for i in range(n):
        
        if a[i] != 0:
            
            pos = i
            
            break

    if pos == -1:
        
        print("NO")
        
    else:
        
        print("YES")

        if pos == n - 1:
            
            print(2)
            
            print(1, n - 1)
            
            print(n, n)
            
        else:
            
            print(2)
            
            print(1, pos + 1)
            
            print(pos + 2, n)
