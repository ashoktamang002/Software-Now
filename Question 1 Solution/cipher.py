# =================================
#     HIT137: SOFTWARE NOW
# Group Assignment 2: Question 1
# =================================
#     Group Name: DAN/EXT 15
# =================================

# Group Members:
# -------------------------
# Ashok Tamang   -  S406128
# Rajesh Basnet  -  S404205
# Aryan Karki    -  S407507
# Ayun Neupane   -  S406923

# =================================
#       PROGRAM DESCRIPTION
# =================================

# Running this file as a script will:
#   1. Prompt the user for two non-negative integers, "shift1" and "shift2".
#   2. Read "raw_text.txt" and encrypt it, writing the result to "encrypted_text.txt".
#   3. Decrypt "encrypted_text.txt", writing the result to "decrypted_text.txt".
#   4. Compare "decrypted_text.txt" against "raw_text.txt" and report whether 
#      the decryption is succesful or not.
# ----------------- 
# Encryption rules
# -----------------
# Lowercase letters:
#   -> a-n (first half)  -> shift forward  by "shift1 * shift2"
#   -> o-z (second half) -> shift backward by "shift1 + shift2"
 
# Uppercase letters:
#   -> A-M (first half)  -> shift backward by "shift1"
#   -> N-Z (second half) -> shift forward  by "shift2 ** 2"
 
# Digits:
#   -> 0-9 -> shift forward by "shift1 - shift2"

# Other characters:
#   -> Spaces, tabs, newlines, punctuation, symbols -> remain unchanged.

# ===============================
#       SOLUTION START
# ===============================

from __future__ import annotations # Enable postponed evaluation of annotations

def _shift_within_range(char: str, start: str, size: int, amount: int) -> str:
    """
    Shift a character within a fixed range by a specified amount.

    It converts the character to a numeric position using ord(), adds the
    shift amount, uses modulo (%) to wrap around when the end of the range
    is reached, and converts the new position back to a character using chr().
    """
    offset = ord(char) - ord(start)             # char's position within the range, 0-based
    new_offset = (offset + amount) % size       # apply the shift; % wraps around the range
    return chr(ord(start) + new_offset)         # convert the wrapped position back to a character

def _transform_char(char: str, shift1: int, shift2: int, *, encrypting: bool) -> str:
    """
    Encrypt or decrypt a single character using different shift rules.

    It first determines the direction of the shift: positive for encryption
    and negative for decryption. It then checks which character range the
    character belongs to and applies the appropriate mathematical shift.
    Lowercase letters, uppercase letters, and digits each use different rules.
    Characters outside these ranges are returned unchanged.
    """
    sign = 1 if encrypting else -1  # +1 applies the shift forward; -1 applies the exact opposite shift, which is what undoes it on decryption           
   
    if 'a' <= char <= 'n':  # lowercase, first half (a-n) 
        return _shift_within_range(char, 'a', 14, sign * (shift1 * shift2))     # forward by shift1*shift2
   
    if 'o' <= char <= 'z':  # lowercase, second half (o-z)
        return _shift_within_range(char, 'o', 12, -sign * (shift1 + shift2))    # backward by shift1+shift2
    
    if 'A' <= char <= 'M':  # uppercase, first half (A-M)
        return _shift_within_range(char, 'A', 13, -sign * shift1)               # backward by shift1 

    if 'N' <= char <= 'Z':  # uppercase, second half (N-Z)
        return _shift_within_range(char, 'N', 13, sign * (shift2 ** 2))         # forward by shift2 squared
  
    if '0' <= char <= '9':  # digits 0-9
        return _shift_within_range(char, '0', 10, sign * (shift1 - shift2))     # forward by shift1-shift2

    return char             # spaces, tabs, newlines, punctuation, symbols: left exactly as they are

def encrypt_file(shift1: int, shift2: int, input_path: str, output_path: str) -> None:
    """
    Encrypt the contents of a text file and save the result to another file.

    It reads the entire input file, processes each character using
    _transform_char() with encryption enabled, joins the transformed
    characters into one string, and writes the encrypted text to the
    output file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()                         # load the whole file into memory as one string

    pieces: list[str] = []
    for char in text:
        pieces.append(_transform_char(char, shift1, shift2, encrypting=True)) # encrypt one char at a time
    encrypted = "".join(pieces)                 # reassemble the transformed characters into one string

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(encrypted)                      # save the encrypted text to disk

def decrypt_file(shift1: int, shift2: int, input_path: str, output_path: str) -> None:
    """
    Decrypt the contents of an encrypted text file and save the result.

    It reads the encrypted file, processes each character using
    _transform_char() with encryption disabled, joins the transformed
    characters into one string, and writes the decrypted text to the
    output file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()                         # load the encrypted file into memory as one string                      

    pieces: list[str] = []
    for char in text:
        pieces.append(_transform_char(char, shift1, shift2, encrypting=False))  # reverse the shift for each char
    decrypted = "".join(pieces)                 # reassemble the transformed characters into one string

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(decrypted)                      # save the decrypted text to disk

def verify_files(original_path: str, decrypted_path: str) -> bool:
    """
    Check whether the original and decrypted files contain exactly the same text.

    It reads both files, compares their contents using ==, and returns 
    True when they are identical or False when they are different.
    """
    with open(original_path, 'r', encoding='utf-8') as f:
        original = f.read()                     # the untouched source text
    with open(decrypted_path, 'r', encoding='utf-8') as f:
        decrypted = f.read()                    # the result of the encryp -> decrypt round trip

    success = original == decrypted             # an exact match means the cipher is fully reversible
    if success:
        print(f"Decryption Verification: '{decrypted_path}' matches '{original_path}' -> Decryption Successful.")
    else:
        print(f"Decryption Result: '{decrypted_path}' doesn't match '{original_path}' -> Decryption was unsuccessful.")
    return success

def get_valid_shift(prompt: str) -> int:
    """
    Ask the user for a valid non-negative integer shift value.

    It repeatedly asks for input, converts the input to an integer using int(),
    checks that the value is not negative, and returns it when valid.
    If the user enters invalid text or a negative number, an error message
    is displayed and the user is asked again.
    """
    while True:                             # keep asking until a valid value is given
        try:
            value = int(input(prompt))      # raises ValueError if the input isn't an integer

            if value < 0:
                print("Error: shift value must be non-negative.")
                continue                    # reject negatives and ask again

            return value                    # a valid non-negative integer was entered

        except ValueError:
            print("Error: please enter a non-negative integer.")

def main() -> None:
    """
    Run the complete encryption, decryption, and verification process.

    It gets two shift values from the user, encrypts the original file,
    decrypts the encrypted file, and finally compares the decrypted file
    with the original file to check whether the process was successful,
    and prints the result accordingly.
    """
    raw_path = 'raw_text.txt'
    encrypted_path = 'encrypted_text.txt'
    decrypted_path = 'decrypted_text.txt'

    print('-'*95)
    shift1 = get_valid_shift("Enter shift1: ")  # first shift value from the user
    shift2 = get_valid_shift("Enter shift2: ")  # second shift value from the user

    print('-'*95) 
    encrypt_file(shift1,shift2,raw_path, encrypted_path)         # step 1: encrypt the original file
    print(f"Encrypted '{raw_path}' -> '{encrypted_path}'") 

    print('-'*95)  
    decrypt_file(shift1,shift2,encrypted_path, decrypted_path)   # step 2: decrypt it back again
    print(f"Decrypted '{encrypted_path}' -> '{decrypted_path}'")

    print('-'*95) 
    verify_files(raw_path, decrypted_path)                       # step 3: check the round trip matches   
    print('-'*95) 

if __name__ == "__main__":
    main()      # Entry point: run main() only when this script is executed directly