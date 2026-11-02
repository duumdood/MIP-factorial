#memory.py
#simualates main memory for the CPU
#
# ============================================================================
# ★ This file extends memory.py from the instructor's V7.1
#   Markers:  ★ [NEW]      = code added by our group
#             ★ [MODIFIED] = instructor's original code that we changed (with the reason)
#             no marker    = instructor's original code
#
#   Summary of changes:
#     1. Added read_word() / write_word() to read/write 4 bytes (1 word) at a time.
#        Previously SW stored the whole value (e.g. 3628800) at a single address,
#        but real MIPS memory holds 1 byte per address → 1 word needs 4 addresses.
#     2. dump() can now be told how many bytes to show.
# ============================================================================

class Memory:
    def __init__(self):
        #Dictionary to store memory values
        #Key -> address
        #value -> data stored at that address
        self.data = {}

    def read(self, address):
        """
        Return tha value at a given memory address.
        If the address has never been written to,
        return 0 (default memory behavior).
        """
        return self.data.get(address, 0)

    def write(self, address, value):
        """
        write a value to a given memory address.
        """
        self.data[address] = value

    # ★ [NEW] ---------------------------------------------------------------
    # read_word / write_word : read/write 32-bit data (4 bytes) in big-endian order
    #
    # big-endian = the "most significant" byte is stored at the lowest address,
    #              like writing a number from left to right
    #   Example: write_word(0x100, 0x12345678)
    #     address 0x100 = 0x12   ← top byte (bits 31-24)
    #     address 0x101 = 0x34
    #     address 0x102 = 0x56
    #     address 0x103 = 0x78   ← bottom byte (bits 7-0)
    #   This matches how the instructor already stores machine code in cpu.py
    def read_word(self, address):
        value = 0
        for i in range(4):
            value = (value << 8) | (self.read(address + i) & 0xFF)  # shift left 8 bits, then append the next byte
        return value

    def write_word(self, address, value):
        value &= 0xFFFFFFFF                     # keep only 32 bits
        for i in range(4):
            shift = 24 - 8 * i                  # byte 0 uses bits 31-24, byte 1 uses bits 23-16, ...
            self.write(address + i, (value >> shift) & 0xFF)
    # ★ [END OF NEW CODE] ---------------------------------------------------

    # ★ [MODIFIED] added the length parameter (previously always showed 100 bytes)
    def dump(self, start=0, width=20, length=100):
        #print("Memory:", self.data)
        print("Memory:")
        for i in range(start, start+length):
            if (i-start)%width==0:
                if i!=start: print()
                print(f"{hex(i)[2:]:>8}: ", end="")
            print(("0"+hex(self.data.get(i,0) & 0xFF)[2:])[-2:], end=" ")   # ★ [MODIFIED] & 0xFF in case a value is larger than 1 byte
        print()

if __name__ == "__main__":
    a = Memory()
    a.write(120,20)
    a.dump(int('0x2000',16))
