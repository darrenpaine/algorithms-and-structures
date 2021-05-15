# Big Integer Multiplication
A set of notebooks looking at different algorithms for multiplying integer. These form an investigation into various implementation techniques (e.g. adding operators) and some interesting algorithms. The aim is to build code that can handle multiplication (and add/subtract) in any base, from binary through decimal to 'base 1,000,000' and above. It will also handle long integers - 10s of thousands of digits or 'limbs' long.

The notebooks are:
1. [Integer Multiplication using Karatsuba method]() Investigation of the Karatsuba algorithm.
2. [Multiplication with Fast Fourier Transform]() looking at Fast Fourier Transforms (FFTs) for multiplication.
3. [Multiplication with Number Theoretic Transform]() - Number Theoretic Transforms (NTTs), which are FFTs using modular arithmatic and are the basis of the Schönhage-Strassen methods and other further improvements.

The final version of the class can be also found in the [bigbaseinteger.py file](), which includes unit tests. As we are implementing in Python, we are at a disadvantage in general compared to - for example, writing this in optimised C or C++, but it is useful to see how the algorithms work and what improvements can be made.

TO DO:
- Add other functionality, such as division, powers, modular arithmaetic, 'integer square root'.
- Implement other mechanisms, such as 'school' long multiplication and 'Russian Peasent' multiplication.
- A C or C++ implementation
