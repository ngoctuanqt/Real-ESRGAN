import argparse
from pathlib import Path
import shutil
import cv2
import glob
import os
import numpy as np
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url
from PIL import Image
from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact

def adjust(image, w, h, center = False, padding = 50):
    print("adjust")
    # image = image.convert('RGBA')
    width, height = image.size
    wr = width/w
    hr = height/h
    if wr > hr:
        new_width = w - padding*2
        new_height = new_width * height // width
    else:
        new_height = h - padding*2
        new_width = new_height * width // height
    image = image.resize((new_width, new_height))
    new_image = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    left = (w-image.size[0]) // 2
    if center:
        top = (h - image.size[1]) // 2
    else:
        top = padding if h - image.size[1] > padding*2 else (h - image.size[1])//3
    new_image.paste(image, (left, top))
    return new_image

def main():
    """Inference demo for Real-ESRGAN.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='inputs', help='Input image or folder')
    parser.add_argument(
        '-n',
        '--model_name',
        type=str,
        default='RealESRGAN_x4plus',
        help=('Model names: RealESRGAN_x4plus | RealESRNet_x4plus | RealESRGAN_x4plus_anime_6B | RealESRGAN_x2plus | '
              'realesr-animevideov3 | realesr-general-x4v3'))
    parser.add_argument('-o', '--output', type=str, default='results', help='Output folder')
    parser.add_argument(
        '-dn',
        '--denoise_strength',
        type=float,
        default=0.5,
        help=('Denoise strength. 0 for weak denoise (keep noise), 1 for strong denoise ability. '
              'Only used for the realesr-general-x4v3 model'))
    parser.add_argument('-s', '--outscale', type=float, default=4, help='The final upsampling scale of the image')
    parser.add_argument(
        '--model_path', type=str, default=None, help='[Option] Model path. Usually, you do not need to specify it')
    parser.add_argument('--suffix', type=str, default='out', help='Suffix of the restored image')
    parser.add_argument('-t', '--tile', type=int, default=0, help='Tile size, 0 for no tile during testing')
    parser.add_argument('--tile_pad', type=int, default=10, help='Tile padding')
    parser.add_argument('--pre_pad', type=int, default=0, help='Pre padding size at each border')
    parser.add_argument('--face_enhance', action='store_true', help='Use GFPGAN to enhance face')
    parser.add_argument('--fp32', action='store_true', help='Use fp32 precision during inference. Default: fp16 (half precision).')
    parser.add_argument(
        '--alpha_upsampler',
        type=str,
        default='realesrgan',
        help='The upsampler for the alpha channels. Options: realesrgan | bicubic')
    parser.add_argument(
        '--ext',
        type=str,
        default='auto',
        help='Image extension. Options: auto | jpg | png, auto means using the same extension as inputs')
    parser.add_argument(
        '-g', '--gpu-id', type=int, default=None, help='gpu device to use (default=None) can be 0,1,2 for multi-gpu')

    args = parser.parse_args()

    ### tuan add
    custom = input("Do you want custom options? y/n: ")
    if custom.lower() == 'y':
        args.fp32 = True
        ip = input("input folder, default (inputs): ")
        if ip:
            args.input = ip
        sv = input("Save Folder, default (results): ")
        if sv:
            args.output =  sv

        print("================= AI Model ===================")
        print(" 1 = RealESRGAN_x4plus")
        print(" 2 = RealESRNet_x4plus")
        print(" 3 = RealESRGAN_x4plus_anime_6B")
        print(" 4 = RealESRGAN_x2plus")
        print(" 5 = realesr-animevideov3")
        print(" 6 = realesr-general-x4v3")
        print("==============================================")
        mode = input("Select AI model, default (1): ")
        if mode == "1": args.model_name = 'RealESRGAN_x4plus'
        if mode == "2": args.model_name = 'RealESRNet_x4plus'
        if mode == "3": args.model_name = 'RealESRGAN_x4plus_anime_6B'
        if mode == "4": args.model_name = 'RealESRGAN_x2plus'
        if mode == "5": args.model_name = 'realesr-animevideov3'
        if mode == "6": args.model_name = 'realesr-general-x4v3'
        # args.gpu_id = 0

    sub = (input("Do you want resize on sub folder also? y/n, default(y): ") or 'y').lower()  == 'y'

    isDel = (input("Delete input file after resize? y/n, default(y): ") or 'y').lower() =='y'
    customSize = input("Do you want custom size? y/n, default(4500x5400): ")
    width =  4500
    height = 5400
    if customSize.lower() == 'y':
        width = int(input("Image width, default(4500): ")) or 4500
        height = int(input("Image height, default(5400): ")) or 5400
    print("\nPlease re-Check your options:")
    print(f"Input folder: {args.input}")
    print(f"Output folder: {args.output}")
    print(f"Delete input: {isDel}")
    print(f"Resize on sub folder also: {sub}")
    print(f"Image width: {width}")
    print(f"Image height: {height}")
    cf = input("Confirm? y/n, default(y): ")
    if cf.lower() == 'n':
        return
    if args.input != args.output:
        args.suffix = ''
    else:
        args.suffix = 'resized'
    print("Preparing environment....")
    ###

    # determine models according to model names
    args.model_name = args.model_name.split('.')[0]
    if args.model_name == 'RealESRGAN_x4plus':  # x4 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']
    elif args.model_name == 'RealESRNet_x4plus':  # x4 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth']
    elif args.model_name == 'RealESRGAN_x4plus_anime_6B':  # x4 RRDBNet model with 6 blocks
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']
    elif args.model_name == 'RealESRGAN_x2plus':  # x2 RRDBNet model
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        netscale = 2
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth']
    elif args.model_name == 'realesr-animevideov3':  # x4 VGG-style model (XS size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
        netscale = 4
        file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
    elif args.model_name == 'realesr-general-x4v3':  # x4 VGG-style model (S size)
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
        netscale = 4
        file_url = [
            'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
            'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth'
        ]

    # determine model paths
    if args.model_path is not None:
        model_path = args.model_path
    else:
        model_path = os.path.join('weights', args.model_name + '.pth')
        if not os.path.isfile(model_path):
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            for url in file_url:
                # model_path will be updated
                model_path = load_file_from_url(
                    url=url, model_dir=os.path.join(ROOT_DIR, 'weights'), progress=True, file_name=None)

    # use dni to control the denoise strength
    dni_weight = None
    if args.model_name == 'realesr-general-x4v3' and args.denoise_strength != 1:
        wdn_model_path = model_path.replace('realesr-general-x4v3', 'realesr-general-wdn-x4v3')
        model_path = [model_path, wdn_model_path]
        dni_weight = [args.denoise_strength, 1 - args.denoise_strength]

    # restorer
    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        dni_weight=dni_weight,
        model=model,
        tile=args.tile,
        tile_pad=args.tile_pad,
        pre_pad=args.pre_pad,
        half=not args.fp32,
        gpu_id=args.gpu_id)

    print(f"Using {upsampler.device} to scale")

    if args.face_enhance:  # Use GFPGAN for face enhancement
        from gfpgan import GFPGANer
        face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=args.outscale,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=upsampler)
    os.makedirs(args.output, exist_ok=True)

    if os.path.isfile(args.input):
        paths = [args.input]
    else:
        if not sub:
            paths = sorted(glob.glob(os.path.join(args.input, '*')))
        else:
            paths = sorted(Path(args.input).rglob("*"))
    print("\n======================== WORKING ===========================")
    print(f"Found {len(paths)} files to resize")
    for idx, path in enumerate(paths):
        path = str(path)
        if not os.path.isfile(path):
            continue
        parDir = os.path.dirname(os.path.abspath(path))
        subDir = parDir.replace(args.input,'')
        print(f'++++++++++++++++++++++++{idx}++++++++++++++++++++++++')
        try:
            imgname, extension = os.path.splitext(os.path.basename(path))
            print('Resizing image: ', imgname)

            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if len(img.shape) == 3 and img.shape[2] == 4:
                img_mode = 'RGBA'
            else:
                img_mode = None

            try:
                if args.face_enhance:
                    _, _, output = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
                else:
                    output, _ = upsampler.enhance(img, outscale=args.outscale)
            except RuntimeError as error:
                print('Error', error)
                if "slow_conv2d_cpu" in str(error):
                    print('You should add --fp32')
                    # break
                    continue

                if "out of memory" in str(error):
                    print('You should add --tile 265')
                    # break
                    continue

                print('If you encounter CUDA out of memory, try to set --tile with a smaller number.')
            else:
                if args.ext == 'auto':
                    extension = extension[1:]
                else:
                    extension = args.ext
                if img_mode == 'RGBA':  # RGBA images should be saved in png format
                    extension = 'png'
                saveOutput = args.output

                if subDir:
                    saveOutput = f'{saveOutput}{subDir}'
                if not os.path.exists(saveOutput):
                    os.makedirs(saveOutput, exist_ok=True)

                if args.suffix == '':
                    save_path = os.path.join(saveOutput, f'{imgname}.{extension}')
                else:
                    save_path = os.path.join(saveOutput, f'{imgname}_{args.suffix}.{extension}')
                imageRGB = cv2.cvtColor(output, cv2.COLOR_BGRA2RGBA)
                try:
                    img = Image.fromarray(imageRGB)
                    outp = adjust(img, width, height)
                    if outp.save(save_path) == None:
                        print(f'Saved to {save_path}')
                        if isDel:
                            try:
                                open(path, 'w').close()
                                os.remove(path)
                                print(f"removed file {path}")
                            except Exception as ex:
                                print(ex)
                    else:
                        print(f'Failed to saved to {save_path}')
                except Exception as ex:
                    try:
                        if cv2.imwrite(save_path, output):
                            print(f'Saved to {save_path}')
                            if isDel:
                                try:
                                    open(path, 'w').close()
                                    os.remove(path)
                                    print(f"removed file {path}")
                                    continue
                                except Exception as ex:
                                    print(ex)
                    except Exception as ex:
                        print(ex)
        except Exception as ex:
            print(ex)
    print("======================== FINISHED ===========================")

if __name__ == '__main__':
    main()
