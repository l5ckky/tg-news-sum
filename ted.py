text = "1234fe3233131567890-"
print(text[:(16 if len(text) >= 20 else None)] + ("..." if len(text) >= 20 else ""))
