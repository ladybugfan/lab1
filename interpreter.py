import sys
import re
import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.value = None
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, key, value):
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.value = value

    def search(self, key):
        node = self.root
        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]
        if node.is_end_of_word:
            return node.value
        return None
    
    def delete(self, key):
        def _delete(node, key, depth):
            if node is None:
                return None

            if depth == len(key):
                if node.is_end_of_word:
                    node.is_end_of_word = False
                if not node.children:
                    return None
                return node

            char = key[depth]
            node.children[char] = _delete(node.children[char], key, depth + 1)

            if not node.children and not node.is_end_of_word:
                return None
            return node

        _delete(self.root, key, 0)

    def obtain_all(self):
        def _obtain_all(node, prefix):
            if node== None:
                return
            if node.is_end_of_word:
                results.append(prefix)
            for char, next_node in node.children.items():
                _obtain_all(next_node, prefix + char)

        results = []
        _obtain_all(self.root, "")
        return results

class Interpreter:
    def __init__(self, settings_file, base_input=10, base_output=10, base_assign=16, debug=False):
        self.commands = {
            'not': 'not',
            'input': 'input',
            'output': 'output',
            'add': 'add',
            'mult': 'mult',
            'sub': 'sub',
            'pow': 'pow',
            'div': 'div',
            'rem': 'rem',
            'xor': 'xor',
            'and': 'and',
            'or': 'or',
            '=': '='
        }
        self.variables = Trie()
        self.base_input = base_input
        self.base_output = base_output
        self.base_assign = base_assign
        self.result_placement = 'left'
        self.unary_syntax = 'op()'
        self.binary_syntax = 'op()'
        self.debug = debug
        self.load_settings(settings_file)
        self.settings_file = settings_file
        self.save_last_settings()
        
        self.oper = []
        for original, _ in self.commands.items():
            self.oper.append(original)
        

    def save_last_settings(self):
        with open('last_settings.json', 'w') as f:
            json.dump({'settings_file': self.settings_file}, f)

    def load_settings(self, settings_file):
        with open(settings_file, 'r') as file:
            for line in file:
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue
                
                if line == 'left=':
                    self.result_placement = 'left'
                elif line == 'right=':
                    self.result_placement = 'right'
                elif line in ['op()', '()op']:
                    self.binary_syntax = line
                    self.unary_syntax = line
                elif line == "(op)":
                    self.binary_syntax = line
                else:
                    parts = line.split()
                    if len(parts) == 2:
                        self.commands[parts[0]] = parts[1]
                    elif len(parts) == 3 and parts[0] == '[':
                        self.commands[parts[1]] = parts[2].rstrip(']')

    def execute(self, program):
        """  program = self.remove_comments(program) """
        lines = program.split(';')
        for line in lines:
            line = line.strip()
            line = self.remove_nested_comments(line)
            if line:
                if self.debug and '#BREAKPOINT' in line:
                    self.debug_prompt()
                    line = line.replace("#BREAKPOINT", "")
                
                line = self.remove_comments(line)
                self.process_line(line)
    
    def remove_comments(self, program):
        program = self.remove_nested_comments(program)
        program = re.sub(r'#.*', '', program)
        return program  

    def remove_nested_comments(self, text):
        pattern = r'\[([^\[\]]*?)\]'
        while re.search(pattern, text):
            text = re.sub(pattern, '', text)
        return text
        
    def process_line(self, line):
        for original, synonym in self.commands.items():
            strr1 = synonym + "("
            strr2 =   ")" + synonym
            strr3 = " " + synonym + " "
            if strr1 in line or strr2 in line or strr3 in line:
                line = line.replace(synonym, original)
            

        if '=' in line:
            if self.result_placement == 'left':
                var, expr = line.split('=', 1)
            else:
                expr, var = line.split('=', 1)
            var = var.strip()
            if "input()" in line:
                var = var.strip()
                value = int(input(f'Enter value for {var}: '), self.base_input)
                self.variables.insert(var, value)
            else:
                value = self.evaluate_expression(expr.strip())
                self.variables.insert(var, value)
        else:
            self.evaluate_expression(line)
    
    def evaluate_expression(self, expr):
        
        if 'output' in expr:
            expr = expr.strip()
            var = ""
            if expr.startswith('output'):
                if self.unary_syntax!="op()":
                    raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                else:
                    var = expr[7:-1].strip()
                    
            if expr.endswith('output'):
                if self.unary_syntax!="()op":
                    raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                else:
                    var = expr[1:-7].strip()
                    
            if "output" in var or "input" in var:
                raise ValueError("ошибка")
            
            value = self.evaluate_expression(var)
            base_output_value = self.decimal_to_base(value, self.base_output)
            print(f'{var} = {base_output_value}')
            return value
            
        elif re.match(r'^[0-9A-Fa-f]+$', expr):
            return int(expr, self.base_assign)
        else:
            return self.evaluate_infix(expr)
    

    def decimal_to_base(self, num, base):
        if num == 0:
            return '0'
        digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = ''
        while num:
            num, remainder = divmod(num, base)
            result = digits[remainder] + result
        return result
    
    def evaluate_infix(self, expression):
        
        precedence = {'add': 1, 
                    'sub': 1, 
                    'mult': 2, 
                    'div': 2, 
                    'rem': 2, 
                    'xor': 1, 
                    'and': 1, 
                    'or': 1, 
                    'pow': 3}

        def higher_precedence(op1, op2):
            return precedence[op1] >= precedence[op2]

        postfix = []
        stack = []

        tokens = self.tokenize(expression)    #3

        for token in tokens:
            if self.is_number(token):
                postfix.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    postfix.append(stack.pop())
                stack.pop()  
            elif token in precedence:
                while stack and stack[-1] != '(' and higher_precedence(stack[-1], token):
                    postfix.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError("Недопустимый токен: " + token)

        while stack:
            postfix.append(stack.pop())

        result = self.eval_postfix(postfix)   #7
        return result

    def is_number(self, s):
        try:
            float(s) 
            return True
        except ValueError:
            return False
    
    def tokenize(self, expression):
        expression = expression.strip()
        tokens = []
        current_token = ''
        open_b = 0
        i=0
        while i!=len(expression):
            if expression[i]==" " and current_token!="" and open_b==0:
                if current_token in ["add","sub","pow","div","rem","xor","and"] and self.binary_syntax!="(op)":
                    raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                tokens.append(current_token)
                current_token = ""
                
            elif expression[i] not in "()" and expression[i]!=" ":    #or (char == "-" and (len(tokens)==0 or tokens[-1] in "-+*/()") and current_token == "")
                current_token += expression[i]
                
            elif expression[i]=='(':
                current_token += expression[i]
                open_b += 1

            elif expression[i]==')' and open_b!=0:
                current_token += expression[i]
                open_b -= 1
                if open_b==0:
                    """ if current_token[0]!="(" and not (self.binary_syntax=="()op" or self.unary_syntax=="()op"):
                        raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                     """
                    if current_token[0]!="(":
                        func_name, arg = list(map(str, current_token.split('(', 1)))
                        arg = arg[:-1]
                    else:
                        arg = current_token[1:-1]
                        func_name = ""
                    
                    current = ""
                    args = []
                    open = 0
                    
                    for j in range(len(arg)):
                        if arg[j]=="(":
                            open += 1
                            current += arg[j]
                        elif arg[j] == ")":
                            open -= 1
                            current += arg[j]
                        elif arg[j] =="," and open == 0:
                            args.append(current)
                            current = ""
                        else:
                            current += arg[j]
                        if j==len(arg)-1:
                            args.append(current)
                            
                    if func_name=="" and len(args)==1:
                        st =expression[i+1:]
                        if st[:3]=="not":
                            if self.unary_syntax!="()op":
                                raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                            else:
                                func_name="not"
                                i+=3
                                
                    elif func_name=="" and len(args)>1:
                        if self.binary_syntax!="()op":
                            raise ValueError("Ошибка: недопустимое расположение операндов и операций")
                        
                        st=expression[i+1:]
                        if st[:3] in ["add","sub","pow","div","rem","xor","and"]:
                            func_name = st[:3]
                            i+=3
                        elif st[:4] in ["mult"]:
                            func_name = st[:4]
                            i+=4
                        elif st[:2] in ["or"]:
                            func_name = st[:2]
                            i+=2
                    if func_name=="":
                        tokens.append(str(self.evaluate_infix(args[0])))
                        current_token = ''
                    else:
                        for k in range(len(args)):
                            args[k] = str(self.evaluate_infix(args[k]))
                            
                            
                        tokens.append(str(self.execute_command(func_name, args)))
                        current_token = ''   
                    
            elif current_token!='' and open_b!=0:
                current_token += expression[i]
                
            elif current_token!='':
                tokens.append(current_token)
                tokens.append(expression[i])
                current_token = ''
            
            i+=1
            
        if current_token:
            tokens.append(current_token)
            
        for i in range(len(tokens)):
            if self.variables.search(tokens[i])!=None:
                tokens[i] = str(self.variables.search(tokens[i]))
        return tokens

    def eval_postfix(self, expression):
        stack = []
        if isinstance(expression, int):
            expression = str(expression)
        for token in expression:
            if self.is_number(token):
                if '.' in token:
                    stack.append(float(token))
                else:
                    stack.append(int(token))
            elif token in self.oper:
                if len(stack) < 2:
                    raise ValueError("Недопустимое выражение")
                operand2 = stack.pop()
                operand1 = stack.pop()
                args = [str(operand1), str(operand2)]
                result = self.execute_command(token, args)
                stack.append(result)
            else:
                raise ValueError("Недопустимый токен: " + token)

        if len(stack) != 1:
            raise ValueError("Недопустимое выражение")

        return stack[0]
    
    def execute_command(self, cmd, args):
        if cmd == 'not':
            arg = self.evaluate_expression(args[0])
            return ~arg & 0xFFFFFFFF
        else:
            arg1 = self.evaluate_expression(args[0])
            arg2 = self.evaluate_expression(args[1])
            if cmd == 'add':
                return (arg1 + arg2) & 0xFFFFFFFF
            elif cmd == 'mult':
                return (arg1 * arg2) & 0xFFFFFFFF
            elif cmd == 'sub':
                return (arg1 - arg2) & 0xFFFFFFFF
            elif cmd == 'div':
                return arg1 // arg2
            elif cmd == 'rem':
                return arg1 % arg2
            elif cmd == 'xor':
                return arg1 ^ arg2
            elif cmd == 'and':
                return arg1 & arg2
            elif cmd == 'or':
                return arg1 | arg2
            elif cmd == 'pow':
                return pow(arg1, arg2, 0x100000000)
        return 0
    
    def roman_to_int(self, s):
        roman_numerals = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000
        }
        total = 0
        prev_value = 0
        for char in reversed(s):
            value = roman_numerals[char]
            if value < prev_value:
                total -= value
            else:
                total += value
            prev_value = value
        return total
    
    def fib_sequence(self, max_value):
        fibs = [1, 2]
        while fibs[-1] + fibs[-2] <= max_value:
            fibs.append(fibs[-1] + fibs[-2])
        return fibs

    def is_zeckendorf(self, fib_nums, fibs):
        fib_set = set(fib_nums)
        for i in range(1, len(fibs)):
            if fibs[i] in fib_set and fibs[i-1] in fib_set:
                return False
        return True

    def zeckendorf_to_int(self, fib_nums):
        return sum(fib_nums)

    def debug_prompt(self):
        
        print("Доступные команды:")
        print("1) Вывод значения и двоичного представления переменной")
        print("2) Вывести все переменные")
        print("3) Обновить значение существующей переменной")
        print("4) Объявить новую переменную")
        print("5) Удалить переменную")
        print("6) Продолжить выполнение кода")
        print("7) Завершить работу интерпретатора")
        
        while True:
            command = input('DEBUG> ').strip().lower()
            
            if command == '1':
                var_name = input('Введите имя переменной: ').strip()
                value = self.variables.search(var_name)
                if value is not None:
                    print(f'{var_name} = {value}')
                    binary_value = f'{value:032b}'
                    print(' '.join(binary_value[i:i+8] for i in range(0, 32, 8)))
                else:
                    print('Переменная не объявлена')
            
            elif command == '2':
                for var in self.variables.obtain_all():
                    value = self.variables.search(var)
                    print(f'{var} = {value}')
            
            elif command == '3':
                var_name = input('Введите имя переменной: ').strip()
                if var_name in self.variables.obtain_all():
                    hex_value = input('Введите шестнадцатеричное значение переменной: ').strip()
                    try:
                        value = int(hex_value, 16)
                        self.variables.insert(var_name, value)
                        print(f'Значение переменной "{var_name}" обновлено')
                    except ValueError:
                        print('Некорректное значение')
                else:
                    print(f'Переменная "{var_name}" не объявлена')
            
            elif command == '4':
                var_name = input('Введите имя новой переменной: ').strip()
                all_var = self.variables.obtain_all()
                while var_name in all_var:
                    print('Переменная уже объявлена. Введите другое имя переменной.')
                    var_name = input('Введите имя новой переменной:  ').strip()
                    
                value_type = input('Введите тип значения (цекендорфский(1)/римский(2)): ').strip().lower()
                
                if value_type == '1':
                    fib_sequence = self.fib_sequence(10**6)
                    while True:
                        fib_nums = list(map(int, input('Введите число в цекендорфовом представлении: ').strip().split()))
                        if self.is_zeckendorf(fib_nums, fib_sequence):
                            value = self.zeckendorf_to_int(fib_nums)
                            self.variables.insert(var_name, value)
                            print(f'Переменная {var_name} объявлена со значением {value}.')
                            break
                        else:
                            print('Недопустимое цекендорфово представление. Попробуйте снова.')
                elif value_type == '2':
                    roman_value = input('Введите значение римскими цифрами: ').strip().upper()
                    value = self.roman_to_int(roman_value)
                    self.variables.insert(var_name, value)
                    print(f'Переменная {var_name} объявлена со значением {value}.')
                else:
                    print('Неизвестный тип значения')
            
            elif command == '5':
                var_name = input('Введите имя переменной: ').strip()
                if self.variables.search(var_name):
                    self.variables.delete(var_name)
                    print(f'Переменная "{var_name}" удалена')
                else:
                    print(f'Переменная "{var_name}" не объявлена')
            
            elif command == '6':
                break
            elif command == '7':
                sys.exit(0)

def main():
    argv = sys.argv
    if len(argv) < 3:
        print("Usage: python interpreter.py <settings_file> <program_file> [--debug|-d|/debug] [base_input] [base_output] [base_assign]")
        sys.exit(1)
    
    program_file = argv[1]
    
    if "lab1/settings.txt" in argv:
        settings_file = "lab1/settings.txt"
    else:
        try:
            with open('lab1/last_settings.json', 'r') as f:
                last_settings = json.load(f)
                settings_file = last_settings.get('settings_file')
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    base_assign = 10
    base_input = 10
    base_output = 10
    
    for arg in argv:
        if arg.startswith("base-assign"):
            base_assign = int(arg.split('=')[1])
            
        elif arg.startswith("base-input"):
            base_input = int(arg.split('=')[1])
            
        elif arg.startswith("base-output"):
            base_output = int(arg.split('=')[1])

    debug = '--debug' in argv or '-d' in argv or '/debug' in argv

    with open(program_file, 'r') as file:
        program = file.read()

    interpreter = Interpreter(settings_file, base_input, base_output, base_assign, debug)
    interpreter.execute(program)
    

main()
    
