from ingest import txt
    
def read(fpath):
    # print("helo")
    ext = fpath.split(".")[-1]
    if ext == "txt":
        # print("hey")
        return txt.read(fpath)
