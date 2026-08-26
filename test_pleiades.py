from pathlib import Path
import json

ROOT=Path.home()/"Desktop"/"HTML_Notitia_V2"
PLEIADES=ROOT/"data"/"pleiades-places.json"

with open(
    PLEIADES,
    encoding="utf-8"
) as f:
    data=json.load(f)

print(type(data))

if isinstance(data,dict):

    print("TOP LEVEL KEYS")
    print(list(data.keys())[:30])

    for key,value in data.items():

        print()
        print("KEY:",key)
        print("TYPE:",type(value))

        if isinstance(value,list) and value:

            print("FIRST RECORD:")
            print(value[0])

        elif isinstance(value,dict):

            print("FIRST KEYS:")
            print(list(value.keys())[:20])

        break

elif isinstance(data,list):

    print("COUNT:",len(data))
    print("FIRST RECORD:")
    print(data[0])