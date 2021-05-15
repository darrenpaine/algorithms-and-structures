"""Implementation of the BaseBigInteger class

This class allows the creation and manipulation of long integer numbers
allowing the number base to be specified.

It implements the efficient Karatsuba multiplication algorithm.

Bases: any base from base 2 upwards. Up to base 36, this is represented
using the numeric and alphabetic symbols. Above that, numbers are shown
by writing each digit in base ten with a | symbol as a separator.
Bases that are multiples of 10 (e.g. 100, 1000, 1000000) can be used to
group digits together, which can increase the speed of processing.
These are printed out as base 10 format.

Initialising: these can accept a string, a Python integer, and a numpy
integer. It also accepts a (numpy) array but note the digits must be in
'reverse' or 'BigEndian' order, with the smallest digit first, e.g.
512 = [2, 1, 5]

Operators: +, - and x are implemented. Division (with remainder) to be
added. 

Example use:
num = BaseBigInteger(256)
print(num * num)
x = BaseBigInteger('F00D', base=16)
y = BaseBigInteger('C0FFEE', base=16)
print(x * y, x + y, x - y)
# Multiply two quite long numbers:
print(BaseBigInteger('9'*1000) * BaseBigInteger('8'*1000))

Other notes: This class is used as a base class for implmenting the
Fast Fourier Transform multiplication and Number Theoretic Transform
multiplication.
"""

import numpy as np

class BaseBigInteger:
    
    def __init__ (self, x, base=10, negative=False, store=np.int16):
        self._base = base
        self._negative = negative
        self._store = store
        if isinstance(x,(np.ndarray,)):
            # An array (which needs to be in the order we expect)
            self._number = x.copy()
            
            # In case we copy a zero-length array, add one digit (a zero)
            # This was an error found during testing with random numbers (speed test)
            if len(x) < 1:
                self._number = np.zeros(1, dtype=self._store)
            
        elif isinstance(x,(np.int16,np.int32,np.int64,int)):
            # Handle a negative integer
            if x < 0:
                x = -x
                self._negative = True
            
            # Add the digits one-by-one, converting to the target base.
            first = True
            while first or x >= self._base:
                if first:
                    self._number = np.asarray((x % self._base,),dtype=self._store)
                    first = False
                else:
                    self._number[-1] = x % self._base
                    x //= self._base
                    self._number = np.append(self._number, [x])
        else:
            # String? First check for a negative sign up front.
            if x[0] == '-':
                self._negative = True
                x = x.replace('-','')
                
            # Empty? Then we are nothing!
            if len(x) < 1:
                self._number = np.zeros(1, dtype=self._store)
            elif (base <= 10):
                # assume that we only have numeric characters and can convert directly
                self._number = np.array(list(map(int,reversed(x))), dtype=self._store)
            else:
                # Bigger base, so could have other characters in there.
                self._number = np.array(list(map(lambda x: (ord(x) - 48) if 48 <=ord(x)<=57
                                                 else ord(x)-65+10,reversed(x.upper()))),
                                        dtype=self._store)

        # Calculate any carryovers
        if len(self._number) > 0:
            self._number, self._negative = self.propogate_carryovers(self._number,base,self._negative)
        else:
            print ('empty init', self._number, base, x)
            raise Exception("Zero length")

        # Clean up any leading zeros:
        while len(self._number) > 1 and self._number[-1] == 0:
            self._number = np.delete(self._number, -1)
        # A sanity check that all digits are less than the base number - use for testing.
        #assert (self._number[self._number[:] >= base].sum() == 0), "Overflow - digit out of range."

    def __str__ (self):
        if (self._base <= 10):
            # Throw out all the numbers directly if base 10 or less.
            return ('-' if self._negative else '') + ''.join(map(str,reversed(self._number.tolist())))
        elif (self._base <= 36):
            # Could have characters in there.
            return ('-' if self._negative else '') + ''.join(map(lambda x: str(x) if x < 10
                                                                 else chr(65+x-10),
                                                                 reversed(self._number.tolist())))
        elif self._base in (100 ,1_000, 10_000, 1_00_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000):
            # Multiples of ten, which read exactly right in base 10 (as long as we zero-pad).
            result = ('-' if self._negative else '')
            result += str(self._number[-1])
            if len(self._number > 1):
                num = 0
                b = self._base
                while (b > 1):
                    num += 1
                    b //= 10
                result += ''.join([str(x).zfill(num) for x in self._number[-2::-1]])
            return result
        else:
            # Another base - over 36 and we have run out of alphabet.
            # Instead, output digits (in base 10) with | separators.
            return ('-' if self._negative else '') + ('|'.join(reversed(self._number.tolist())))

    def __add__(self, other):
        result, neg = self._add_numbers(self._number, self._negative, other._number, other._negative)
        return BaseBigInteger(result, self._base, neg, self._store)
    

    def __mul__(self, other):
        result, neg = self._multiply_numbers(self._number.copy(), other._number.copy())
        return BaseBigInteger(result, self._base, neg | (self._negative != other._negative))
    def __sub__(self, other):
        result, neg = self._add_numbers(self._number, self._negative, other._number, not other._negative)
        return BaseBigInteger(result, self._base, neg, self._store)

    def _add_numbers(self, n1, neg1, n2, neg2):
        # Logic for adding:
        # If the signs are the same add the two numbers.
        # If the signs are different, use absolute values and 
        # subtract the smaller value from the bigger.
        # Set the sign to the same as the bigger number's sign.
        
        # Make a copy (or it has side-effects elsewhere)
        # Take the longer one, so that we fit all the numbers in
        bigger, smaller = self.get_bigger_smaller(n1,n2)
        overlap = len(smaller)
        result = bigger.copy()
        
        # numbers are little endian, so overlap is at the front:
        if neg1 == neg2:
            result[:overlap] = bigger[:overlap] + smaller
        else:
            result[:overlap] = bigger[:overlap] - smaller
            
        result, neg = self.propogate_carryovers(result, self._base,
                                                neg1 if n1 is bigger else neg2)

        return np.trim_zeros(result,'b'), neg

    def _subtract_numbers(self, n1, neg1, n2, neg2):
        # Logic for subtracting:
        # Change the sign on the second number (being subtracted).
        # Proceed as for addition - so we call the add() function.
        return self._add_numbers(n1, neg1, n2, not neg2)

    def _multiply_numbers(self, first, second):
        # If one is single digit, this is the base case:
        lenfirst = len(first)
        lensecond = len(second)
        if lenfirst < lensecond:
            first, second = second,first
            lenfirst, lensecond = lensecond, lenfirst
        if lenfirst == 1:
            return self.propogate_carryovers(second[:] * first[0], self._base, False)
            #return result, False
        if lensecond == 1:
            return self.propogate_carryovers(first[:] * second[0], self._base, False)
            #return result, False
        if not lenfirst or not lensecond:
            return np.zeros(1, dtype=self._store), False

        # Split the digits into two halves:
        m = lenfirst >> 1 # divide by 2
        b = np.trim_zeros(first[:m], 'b')
        a = first[m:]
        d = np.trim_zeros(second[:m], 'b')
        c = second[m:]

        z2, z2neg = self._multiply_numbers(a, c)
        z0, z0neg = self._multiply_numbers(b, d)
        z1, z1neg = self._multiply_numbers(self._add_numbers(a, False, b, False)[0], self._add_numbers(c, False, d, False)[0])

        # Do the additions needed. A little more longwinded that previously,
        # as we have to separate them out with the new implementation.
        z2z0, z2z0neg = self._add_numbers(z2, z1neg, z0, z0neg)
        # This subtraction is done by changing the sign and adding:
        zmiddle, zmneg = self._add_numbers(z1, z1neg, z2z0, not z2z0neg)
        zmiddle = np.append(np.zeros(m, dtype=self._store), zmiddle)

        zends, zendsneg = self._add_numbers(np.append(np.zeros(m << 1, dtype=self._store), z2), z2neg,
                                            z0, z0neg)
        return self._add_numbers(zends, zendsneg, zmiddle, zmneg)
    
        #return z2.shift(2*m)+(z1-z2-z0).shift(m)+z0

    def get_bigger_smaller(self, x, y):
        # Swap if longer
        if (len(x) < len (y)):
            return y,x
        # If same length, check digit by digit, only until we find one is bigger.
        if (len(x) == len (y)):
            for i in range (-1,-len(x)-1,-1):
                if x[i] < y[i]:
                    return y,x
                    break
                elif x[i] > y[i]:
                    break
        return x,y       

    def propogate_carryovers(self, result, base, negative):
        # Calculate any carryovers
        for digit in range(0,len(result)-1):
            # note, if we come here after subtraction, some digits may be negative
            # the calculation still works, as the // returns a negative, and
            # the % correctly gives the remainder from the carryover number
            result[digit+1] += result[digit]//base
            result[digit] %= self._base
            #print (result[digit],result[digit+1])

        # Anything to fix with the highest digit?
        if len(result):
            # Is it negative? Convert to a positive and change the sign.
            if result[-1] < 0:
                if len(result) > 1:
                    result[-2] = result[-1] % self._base
                    result[-1] = 0
                else:
                    result[-1] %= self._base
                negative = not negative
            
            # Is there carry over needed to even higher digits?
            while result[-1]>=self._base:
                result = np.append(result, [result[-1]//self._base])
                result[-2] %= self._base
                
            return result, negative
        else:
            # It's zero if empty. Let's make sure it looks right:
            return np.zeros(1, dtype=self._store), False

    def shift (self, shift_num):
        result = BaseBigInteger(self._number, self._base, self._negative)
        if shift_num == 0:
            return result
        elif shift_num > 0:
            result._number = np.append(np.zeros(shift_num, dtype=self._store), result._number)
        elif len(result._number) + shift_num > 0:
            result._number = np.delete(result._number, range(0,-shift_num))
        else:
            return BaseBigInteger(0,self._base)
        return result    

if __name__ == '__main__':
    # Unit tests
    # Test cases
    # First, we'll implement get_base_integer() so that we can override
    # it to return a different version of the BaseInteger class later,
    # as features are added. This will be like an # object factory model,
    # providing different versions as needed.
    # First - redefine the 'object factory' to give our NewBaseInteger object.
    def get_base_integer(digits, base=10, negative=False, store=np.int16):
        return BaseBigInteger(digits, base, negative, store)

    def test_base_integer_add():
        print ("Testing + infix operator for get_base_integer2 class")
        for x,y in ('0','0'), ('1','1'), ('1','10'),('9','9'), ('1000','999'), \
                   ('9999999','9999999'), ('9999999','1'), ('1', '9999999'), ('9999999','0'), \
                   ('987654321987654321987654321987654321987654321','9'), \
                   ('987654321987654321987654321987654321987654321',
                    '987654321987654321987654321987654321987654321'):
            x_test = get_base_integer(x)
            y_test = get_base_integer(y)
            result = x_test + y_test
            print ("Adding:",x,'+',y,'=',result, '- Result same as python:', \
                   (int(x)+int(y) == int(result.__str__())) )

    def test_base_integer_multiply():
        print ("\nTesting * infix operator - uses Karatsuba multiplication algorithm")
        for x,y in ('0','0'), ('1','1'), ('1','10'),('9','9'), ('1000','999'), \
                   ('9999999','9999999'), ('9999999','1'), ('1', '9999999'), ('9999999','0'), \
                   ('987654321987654321987654321987654321987654321','9'), \
                   ('987654321987654321987654321987654321987654321',
                    '987654321987654321987654321987654321987654321'):
            x_test = get_base_integer(x)
            y_test = get_base_integer(y)
            result = x_test * y_test
            print ("Multiplying:",x,'x',y,'=',result, '- Result same as python:', \
                   (int(x)*int(y) == int(result.__str__())) )

    def test_base_integer_shift():
        print ("\nTesting digit shift algorithm")
        shifty = get_base_integer(2)
        # Implement __rshift__ for >> and __lshift__ for <<
        print('Shift 2 left 1:',shifty.shift(1))
        print('Shift 2 left 5:',shifty.shift(5))
        print('Shift 2 right 1:',shifty.shift(-1))
        print('Shift 1000 right 3:',get_base_integer(1000).shift(-3))
        print('Shift 2 left 5 and right 1:',shifty.shift(5).shift(-4))

    def test_base_integer_other_bases():
        print('\nTesting alternative bases:')
        for text,base in ('100', 2), ('fff',16), ('abcdefg',17):
            print(f'Input: {text} in base {base} is: {get_base_integer(text, base=base)}')

        for n1, n2, base in ('100', '100', 2), ('111', '111', 2), ('10000', '100', 2), ('FFFF', 'FFFF', 16), \
                            ('11110100001000111111', '11110100001000111111', 2), ('123434561', '234267123', 8), \
                            ('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', 16), \
                            ('BADF00D', 'BADF00D', 16), ('A', 'A', 16), ('A', 'A', 36), \
                            ('ABCDEFGHIJKLMNOPQRSTUVWXYZ0000000000', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789', 36), \
                            ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 36), \
                            ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[::-1], 36), \
                            ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[::-1], 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[::-1], 36):
            print(f'{n1} + {n2} (base {base}) =', get_base_integer(n1,base=base) + get_base_integer(n2,base=base))
            print(f'{n1} x {n2} (base {base}) =', get_base_integer(n1,base=base) * get_base_integer(n2,base=base))


    # Testing for negative numbers and addition, subtraction, multiplication:
    def test_base_integer_minus():
        print('\nTesting negative values:')
        for text,base in ('-100', 2), ('-fff',16), ('-abcdefg',17):
            print(f'Input: {text} in base {base} is: {get_base_integer(text, base=base)}')
        for text,base in ('100', 2), ('fff',16), ('abcdefg',17):
            print(f'Input: {text} in base {base} with negative flag is: {get_base_integer(text, base=base, negative=True)}')

        print ("\nTesting + - and * operators")
        error_found = False
        for x,y in ('0','0'), ('-1','-1'), ('1','-1'), ('-1','1'), ('1','1'), ('1','10'), \
                   ('9','9'), ('1000','999'), ('9','-9'), ('-1000','999'), ('-9','-9'), ('-1000','-999'), \
                   ('-9999999','9999999'), ('-9999999','1'), ('1', '-9999999'), ('-9999999','0'), \
                   ('987654321987654321987654321987654321987654321','9'), \
                   ('-987654321987654321987654321987654321987654321',
                    '-987654321987654321987654321987654321987654321'), \
                   ('0','0'), ('1','1'), ('1','10'),('9','9'), ('1000','999'), \
                   ('9999999','9999999'), ('9999999','1'), ('1', '9999999'), ('9999999','0'), \
                   ('987654321987654321987654321987654321987654321','9'), \
                   ('987654321987654321987654321987654321987654321',
                    '987654321987654321987654321987654321987654321'):
            x_test = get_base_integer(x)
            y_test = get_base_integer(y)
            result_add = x_test + y_test
            result_min = x_test - y_test
            result_mult = x_test * y_test
            if not (int(x)+int(y) == int(result_add.__str__())):
                print (x,'+',y,'=', result_add, '- ERROR, should be :', int(x)+int(y) )
                error_found = True
            if not (int(x)-int(y) == int(result_min.__str__())):
                print (x,'-',y,'=', result_min, '- ERROR, should be :', int(x)-int(y) )
                error_found = True
            if not (int(x)*int(y) == int(result_mult.__str__())):
                print (x,'x',y,'=', result_mult, '- ERROR, should be :', int(x)*int(y) )
                error_found = True
        if not error_found:
            print('No errors found - all calcuations matched the Python results')

    # Test different bases produce the same results with add, subtract and multiply
    import operator
    def test_base_operator(x, y, op_name, op_func, base):
        print(f'Python {op_name}    {np.base_repr(op_func(int(x, base),int(y, base)), base)}')
        print(f'Karatsuba {op_name} {op_func(BaseBigInteger(x, base=base), BaseBigInteger(y, base=base))}')

    def test_base_integer_bases_operators(base, num1, num2):
        print(f'Base {base}')
        print('='*(5+len(str(base))))
        print('Num 1:   ', num1)
        print('Num 2:   ', num2)
        test_base_operator(num1, num2,'+', operator.add, base)
        test_base_operator(num1, num2,'-', operator.sub, base)
        test_base_operator(num1, num2,'x', operator.mul, base)

    # TO DO: test the constructor __init__ with different types.
    
    # Test operators - mostly in base 10
    test_base_integer_add()
    test_base_integer_multiply()
    test_base_integer_shift()
    test_base_integer_other_bases()
    test_base_integer_minus()

    # Test different bases
    test_base_integer_bases_operators(2, num1 = '101001010010111011100111001', num2 = '11110111011100000101110111101')
    test_base_integer_bases_operators(8, num1 = '235356344561234346451230', num2 = '503453545231356344034')
    test_base_integer_bases_operators(16, num1 = 'BADF00DFEEDFEDDEAD', num2 = 'C0FFEEEEEEEEEEEEEEEEEE')
    test_base_integer_bases_operators(36, num1 = '9876543210qwertyuiopasdfghjklzxcvbnm', num2 = 'thequickbrownfoxjumpsoverthelazydog')
    