t = int(input())

for _ in range(t):
    
    n = int(input())
    
    a = list(map(int, input().split()))

    zeros = a.count(0)

    # Если нулей два и больше, произведение всегда будет 0
    
    if zeros >= 2:
        
        print(0)

    # Если ровно один ноль
    
    elif zeros == 1:
        
        prod = 1
        
        for x in a:
            
            if x != 0:
                
                prod *= x
                
        # Выгодно увеличить ноль до 1
        
        print(prod)

    # Нулей нет
    
    else:
        
        prod = 1
        
        for x in a:
            
            prod *= x

        ans = 0
        
        for x in a:
            
            cur = prod // x * (x + 1)
            
            ans = max(ans, cur)

        print(ans)
