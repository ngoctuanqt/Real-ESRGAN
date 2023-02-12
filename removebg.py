import glob
import argparse
import os
from pathlib import Path
from rembg import remove, new_session

def main():
    inputPath = "inputs"
    outputpath = "results"
    # custom = input("Do you want custom options? y/n: ")
    # if custom.lower() == 'y':
    ip = input("input folder, default (inputs): ")
    if ip:
        inputPath = ip
    sv = input("Save Folder, default (results): ")
    if sv:
        outputpath =  sv

    sub = (input("Do you want resize on sub folder also? y/n, default(y): ") or 'y').lower()  == 'y'

    isDel = (input("Delete input file after resize? y/n, default(n): ") or 'n').lower() =='y'

    print("\nPlease re-Check your options:")
    print(f"Input folder: {inputPath}")
    print(f"Output folder: {outputpath}")
    print(f"Delete input: {isDel}")
    print(f"Resize on sub folder also: {sub}")
    cf = input("Confirm? y/n, default(y): ")
    if cf.lower() == 'n':
        return


    if os.path.isfile(inputPath):
        paths = [inputPath]
    else:
        if not sub:
            paths = sorted(glob.glob(os.path.join(inputPath, '*')))
        else:
            paths = sorted(Path(inputPath).rglob("*"))

    session = new_session()

    print("\n======================== WORKING ===========================")
    print(f"Found {len(paths)} files to remove BG")
    for idx, path in enumerate(paths):
        path = str(path)
        if not os.path.isfile(path):
            continue
        parDir = os.path.dirname(os.path.abspath(path))
        subDir = parDir.replace(inputPath,'')
        print(f'++++++++++++++++++++++++{idx}++++++++++++++++++++++++')

        try:
            imgname, extension = os.path.splitext(os.path.basename(path))
            print('Removing image: ', imgname)

            if subDir:
                outputpath = f'{outputpath}{subDir}'
            if not os.path.exists(outputpath):
                os.makedirs(outputpath, exist_ok=True)

            save_path = os.path.join(outputpath, f'{imgname}.png')
            rmed = False
            with open(path, 'rb') as i:
                with open(save_path, 'wb') as o:
                    img = i.read()
                    output = remove(img, session=session)
                    o.write(output)
                    rmed = True
            if rmed and isDel:
                try:
                    open(path, 'w').close()
                    os.remove(path)
                    print(f"removed file {path}")
                except Exception as ex:
                    print(ex)
        except Exception as ex:
            print(ex)

if __name__ == '__main__':
    main()
