from configparser import ConfigParser

db_file_path = r"C:\\Users\\lukut\Desktop\\hahaha\\car_parts_picker\\main_project\\database.ini"

def config(filename=db_file_path, section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return db


