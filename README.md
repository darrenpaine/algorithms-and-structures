# Experimenting with Algorithms and Structures
A set of implementations looking at different algorithms and structures in Python. These form an investigation into various implementation techniques (e.g. adding operators) and some interesting algorithms.

## Integer Manipulation - Algorithms
[Jupyter workbook](https://github.com/darrenpaine/algorithms-and-structures/blob/main/Integer%20Manipulation%20-%20Algorithms.ipynb)
This prjoect looks at the mechanisms for different integer arithmatic by implementing different algorithms for integer manipulation. The initial focus is on the ['Karatsuba Multiplication Algorithm'](https://en.wikipedia.org/wiki/Karatsuba_algorithm). It turns out that multiplication using the algorithm we learned in school (shift across, multiply each digit, carry over, etc) is not the most efficient, especially when dealing with very large integers - such as those used in cryptography.
First, the algorithm is tested out in Python integers. Then, a BaseInteger class will be developed that will take in different representations and build up to addition, multiplication, different bases (from binary to base 36), powers, subtraction and division. Various operators, such as +, \*, - are then added.
Once developed in Jupyter notebook, the final implementation is transferred to baseinteger.py - to be done.

## Implementation of sorting algorithms
[Jupyter workbook](https://github.com/darrenpaine/algorithms-and-structures/blob/main/Merge%20and%20Search%20Algorithms.ipynb)
1) Implementing MergeSort

## Simple Expression Parser
[Jupyter workbook](https://github.com/darrenpaine/algorithms-and-structures/blob/main/Numerical%20Expression%20Parser.ipynb)
Implementation of a simple mathematical expression parser. This implements a Stack class which extends a Linkedist, to perform postfix evaluation (1 2 + = ?), then infix evaluation (1 + 2 = ?).
