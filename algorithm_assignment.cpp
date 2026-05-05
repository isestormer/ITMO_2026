#include <iostream>

// Шаг 5: Объявление и реализация функции расчета квадратного корня

double calculation(double target) {
    
    double x = 1;
    
    double oldx;
    
    do {
        
        oldx = x;
        
        x = (x + target / x) / 2;
        
    } while (oldx != x);
    
    return x; // Возвращаем найденное значение (выходная переменная)
}

int main() {
    
    // Шаг 6a: Объявление и инициализация переменной
    
    double target = 2021;
    
    // Шаг 6b: Вызов метода с сохранением результата в другую переменную
    
    double result = calculation(target);
    
    // Шаг 6c: Вывод результата и проверочного значения на экран
    
    std::cout << "x = " << result << "\n";
    
    std::cout << "x^2 = " << result * result << "\n";
    
    return 0;
    
}