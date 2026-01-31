# Arithmetic

Bash supports integer arithmetic natively. For floating-point calculations, external tools are needed.

## Arithmetic Expansion

The `$(( ))` syntax evaluates arithmetic expressions:

```bash
echo $((5 + 3))       # 8
echo $((10 - 4))      # 6
echo $((6 * 7))       # 42
echo $((20 / 3))      # 6 (integer division)
echo $((20 % 3))      # 2 (modulo)
echo $((2 ** 10))     # 1024 (exponentiation)
```

### Operators

| Operator | Meaning |
|----------|---------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division (integer) |
| `%` | Modulo (remainder) |
| `**` | Exponentiation |
| `++` | Increment |
| `--` | Decrement |

### Compound Assignment

```bash
x=10
((x += 5))     # x = 15
((x -= 3))     # x = 12
((x *= 2))     # x = 24
((x /= 4))     # x = 6
((x %= 4))     # x = 2
```

### Increment and Decrement

```bash
x=5
echo $((x++))  # 5 (post-increment: use then increment)
echo $x        # 6

x=5
echo $((++x))  # 6 (pre-increment: increment then use)
echo $x        # 6
```

## The (( )) Command

For arithmetic evaluation without output:

```bash
((count++))         # Increment, no output
((total = a + b))   # Calculate and assign

# As a condition
if ((count > 10)); then
    echo "Large"
fi
```

### Exit Status

`(( ))` returns 0 (success) if result is non-zero, 1 (failure) if zero:

```bash
((5 > 3)) && echo "True"    # Prints True
((5 < 3)) && echo "True"    # Prints nothing

((0)) && echo "True"        # Prints nothing (0 = false)
((1)) && echo "True"        # Prints True (non-zero = true)
```

## Variables in Arithmetic

Variables don't need `$` inside `(( ))`:

```bash
a=5
b=3
echo $((a + b))     # 8
echo $((a * b))     # 15

# With $ works too, but not needed
echo $(($a + $b))   # 8
```

Undefined variables are treated as 0:

```bash
unset x
echo $((x + 5))     # 5
```

## Comparison Operators

Inside `(( ))`:

| Operator | Meaning |
|----------|---------|
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |
| `==` | Equal |
| `!=` | Not equal |

```bash
a=5
b=10

((a < b)) && echo "a is smaller"
((a == 5)) && echo "a equals 5"
```

## Logical Operators

| Operator | Meaning |
|----------|---------|
| `&&` | Logical AND |
| `\|\|` | Logical OR |
| `!` | Logical NOT |

```bash
a=5
b=10

((a > 0 && b > 0)) && echo "Both positive"
((a > 10 || b > 5)) && echo "At least one condition true"
((!0)) && echo "NOT 0 is true"
```

## Bitwise Operators

| Operator | Meaning |
|----------|---------|
| `&` | Bitwise AND |
| `\|` | Bitwise OR |
| `^` | Bitwise XOR |
| `~` | Bitwise NOT |
| `<<` | Left shift |
| `>>` | Right shift |

```bash
echo $((5 & 3))     # 1  (0101 & 0011 = 0001)
echo $((5 | 3))     # 7  (0101 | 0011 = 0111)
echo $((5 ^ 3))     # 6  (0101 ^ 0011 = 0110)
echo $((~5))        # -6 (bitwise NOT)
echo $((1 << 4))    # 16 (0001 << 4 = 10000)
echo $((16 >> 2))   # 4  (10000 >> 2 = 100)
```

## The let Command

Alternative syntax for arithmetic:

```bash
let "a = 5 + 3"
let a++
let "b = a * 2"
echo $a $b    # 9 18
```

Multiple expressions:

```bash
let "a = 1" "b = 2" "c = a + b"
echo $c    # 3
```

## The expr Command

External command (POSIX compatible, but slower):

```bash
result=$(expr 5 + 3)
echo $result    # 8

# Operators need escaping
expr 5 \* 3     # 15
expr 10 / 3     # 3
```

!!! note "Prefer $(( ))"
    `expr` is slower and more cumbersome. Use `$(( ))` in bash scripts.

## Floating-Point Arithmetic

Bash only handles integers. For floating-point, use external tools.

### Using bc

```bash
echo "5.5 + 3.2" | bc           # 8.7
echo "scale=2; 10 / 3" | bc     # 3.33
echo "scale=4; 22 / 7" | bc     # 3.1428
```

In scripts:

```bash
result=$(echo "scale=2; 10 / 3" | bc)
echo $result    # 3.33
```

bc features:

```bash
# Math functions
echo "scale=4; sqrt(2)" | bc -l     # 1.4142
echo "scale=4; s(3.14159/2)" | bc -l  # sin(pi/2) = 1.0000
echo "scale=4; c(0)" | bc -l        # cos(0) = 1.0000
echo "scale=4; l(2.71828)" | bc -l  # ln(e) = .9999
```

### Using awk

```bash
awk "BEGIN {print 5.5 + 3.2}"           # 8.7
awk "BEGIN {printf \"%.2f\n\", 10/3}"   # 3.33
```

In scripts:

```bash
result=$(awk "BEGIN {printf \"%.2f\", 10/3}")
echo $result    # 3.33
```

### Using Python

```bash
python3 -c "print(5.5 + 3.2)"           # 8.7
python3 -c "print(f'{10/3:.2f}')"       # 3.33
```

## Number Bases

### Specify Base

```bash
echo $((16#FF))       # 255 (hex)
echo $((2#1111))      # 15 (binary)
echo $((8#77))        # 63 (octal)
echo $((36#z))        # 35 (base 36)
```

### Convert to Base

```bash
# Decimal to hex
printf '%x\n' 255     # ff
printf '%X\n' 255     # FF

# Decimal to octal
printf '%o\n' 64      # 100

# Binary (using bc)
echo "obase=2; 255" | bc    # 11111111
```

## Random Numbers

```bash
echo $RANDOM              # 0-32767
echo $((RANDOM % 100))    # 0-99
echo $((RANDOM % 100 + 1)) # 1-100
```

Random in range:

```bash
# Random between min and max
min=10
max=20
echo $((RANDOM % (max - min + 1) + min))
```

## Practical Examples

### Sum Numbers

```bash
nums=(1 2 3 4 5)
sum=0
for n in "${nums[@]}"; do
    ((sum += n))
done
echo "Sum: $sum"    # 15
```

### Average

```bash
nums=(10 20 30 40 50)
sum=0
for n in "${nums[@]}"; do
    ((sum += n))
done
avg=$(echo "scale=2; $sum / ${#nums[@]}" | bc)
echo "Average: $avg"    # 30.00
```

### Factorial

```bash
factorial() {
    local n=$1
    local result=1
    for ((i=2; i<=n; i++)); do
        ((result *= i))
    done
    echo $result
}

factorial 5    # 120
```

### Power of Two Check

```bash
is_power_of_two() {
    local n=$1
    ((n > 0 && (n & (n - 1)) == 0))
}

is_power_of_two 16 && echo "Yes"    # Yes
is_power_of_two 15 && echo "Yes"    # (nothing)
```

### Temperature Conversion

```bash
# Celsius to Fahrenheit
c_to_f() {
    echo "scale=1; ($1 * 9 / 5) + 32" | bc
}

c_to_f 0     # 32.0
c_to_f 100   # 212.0
```

### File Size Formatting

```bash
format_bytes() {
    local bytes=$1
    if ((bytes < 1024)); then
        echo "${bytes}B"
    elif ((bytes < 1048576)); then
        echo "$(echo "scale=1; $bytes / 1024" | bc)K"
    elif ((bytes < 1073741824)); then
        echo "$(echo "scale=1; $bytes / 1048576" | bc)M"
    else
        echo "$(echo "scale=1; $bytes / 1073741824" | bc)G"
    fi
}

format_bytes 500         # 500B
format_bytes 5000        # 4.8K
format_bytes 5000000     # 4.7M
format_bytes 5000000000  # 4.6G
```

## Try It

1. Basic arithmetic:
   ```bash
   a=10
   b=3
   echo "Sum: $((a + b))"
   echo "Product: $((a * b))"
   echo "Division: $((a / b))"
   echo "Modulo: $((a % b))"
   ```

2. Compound assignment:
   ```bash
   x=5
   ((x += 10))
   echo $x    # 15
   ((x *= 2))
   echo $x    # 30
   ```

3. Floating-point:
   ```bash
   echo "scale=4; 22 / 7" | bc
   awk "BEGIN {printf \"%.2f\n\", 355/113}"
   ```

4. Random number:
   ```bash
   echo "Random 1-100: $((RANDOM % 100 + 1))"
   ```

## Summary

| Method | Use Case |
|--------|----------|
| `$((expr))` | Integer arithmetic, returns value |
| `((expr))` | Integer arithmetic, no return (for conditions) |
| `let` | Alternative integer arithmetic |
| `bc` | Floating-point, advanced math |
| `awk` | Floating-point, inline calculations |

Key points:

- `$(( ))` is for integer arithmetic only
- Variables don't need `$` inside `(( ))`
- Use `bc` or `awk` for floating-point
- `(( ))` returns true (0) for non-zero results
- Division is integer division (truncates)
