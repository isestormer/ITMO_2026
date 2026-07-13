class Fibo:
    def __init__(self):
        
        self.current = 0
        
        self.next_val = 1

    def __iter__(self):
        
        return self

    def __next__(self):
        
        res = self.current
        
        temp = self.current + self.next_val
        
        self.current = self.next_val
        
        self.next_val = temp
        
        return res

def integers():
    
    num = 0
    
    while True:
        
        yield num
        
        num += 1

def primes():
    
    num = 2
    
    while True:
        
        is_prime = True
        
        for i in range(2, int(num ** 0.5) + 1):
            
            if num % i == 0:
                
                is_prime = False
                
                break
        
        if is_prime:
            
            yield num
            
        num += 1

# Проверка работоспособности Fibo
print("Числа Фибоначчи (первые 7):")

fibo_iter = Fibo()

for _ in range(7):
    
    print(next(fibo_iter), end=" ")
    
print("\n")

# Проверка работоспособности integers
print("Целые числа (первые 5):")

gen_ints = integers()

for _ in range(5):
    
    print(next(gen_ints), end=" ")
    
print("\n")

# Проверка работоспособности primes
print("Простые числа (первые 7):")

gen_primes = primes()

for _ in range(7):
    
    print(next(gen_primes), end=" ")
    
print()
