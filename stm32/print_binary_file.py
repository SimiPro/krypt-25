def main():
    binary_file = "s_test.bin"
    with open(binary_file, "rb") as f:
        data = f.read()
    # print first 16 bytes in hex
    print(data[:16].hex())
    # print first 16 bytes in ascii
    print(data[:16].decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    main()