import os
import logging

def _read_file(filepath, byte_limit = 1024):
    fd = os.open(filepath, os.O_RDONLY) # Read only
    read = os.read(fd,byte_limit)
    print("READ", read)
    return read

def get_file_as_bytes(relative_filepath):
    full_path = os.getcwd() + relative_filepath # Comes with a / in front which messes up os.path.join
    print("CURENT DIREEDTCOA", os.getcwd(), full_path)
    if not os.path.isfile(full_path):
        logging.warning("File not found {}".format(full_path))
        return False
    strem = _read_file(full_path)
    return strem