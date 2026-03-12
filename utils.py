def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            # Fallback to ASCII with replacement characters for Windows CMD/PS
            print(str(msg).encode('ascii', 'replace').decode('ascii'))
        except:
            pass
