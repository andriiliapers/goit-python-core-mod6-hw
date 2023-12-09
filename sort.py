import os
import shutil
import sys

RESTRICTED_FOLDERS = ['archives', 'video', 'audio', 'documents', 'images', 'others']

CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")

TRANS = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()

PATHS = dict()
RESTRICTED_FOLDERS = set()
SUPPORTED_ARCHIVE_TYPES = ('TAR', 'GZ', 'ZIP')


def set_dirs(path: str) -> None:
    global PATHS
    global RESTRICTED_FOLDERS

    images_dir = os.path.join(path, 'images')
    documents_dir = os.path.join(path, 'documents')
    audio_dir = os.path.join(path, 'audio')
    video_dir = os.path.join(path, 'video')
    archives_dir = os.path.join(path, 'archives')
    others_dir = os.path.join(path, 'others')

    # create folder only if it has not yet been created
    for path in (images_dir, documents_dir, audio_dir, video_dir, archives_dir, others_dir):
        if not os.path.exists(path):
            os.mkdir(path)

    # build a global dictionary with target destinations for all file types we are
    # going to handle
    PATHS.update({file_type: images_dir for file_type in ('JPEG', 'PNG', 'JPG', 'SVG')})
    PATHS.update({file_type: video_dir for file_type in ('AVI', 'MP4', 'MOV', 'MKV')})
    PATHS.update({file_type: documents_dir for file_type in ('DOC', 'DOCX', 'TXT', 'PDF', 'XLSX' 'PPTX', 'CSV', 'XML', 'JSON')})
    PATHS.update({file_type: audio_dir for file_type in ('MP3', 'OGG', 'WAV', 'AMR')})
    PATHS.update({file_type: archives_dir for file_type in SUPPORTED_ARCHIVE_TYPES})
    PATHS['OTHER'] = others_dir

    RESTRICTED_FOLDERS = set(PATHS.values())


def sort(path: str) -> None:

    # list all files inside the dir
    entries = os.listdir(path)

    for entry in entries:
        full_path = os.path.join(path, entry)

        # Do not traverse restricted folders
        if full_path in RESTRICTED_FOLDERS:
            continue

        archive_type = entry.split('.')[-1]

        if os.path.isdir(full_path):
            # if folder, do recursive call for the
            # inner folder
            sort(full_path)
        elif archive_type.upper() in SUPPORTED_ARCHIVE_TYPES:
            handle_archive(archive_type, full_path)
        else:
            handle_regular_file(entry, path)


def handle_regular_file(entry: str, path: str) -> None:
    normalized_file_name = normalize(entry)
    rename_entry(path, entry, normalized_file_name)
    move_file(path, normalized_file_name)


def handle_archive(archive_type: str, full_path: str) -> None:
    # we can use zip, as tar and gz must be unpacked to
    # the same dir as zip
    shutil.unpack_archive(full_path, extract_dir=PATHS['ZIP'], format=archive_type)
    # remove an archive
    os.remove(full_path)


def normalize(filename: str) -> str:
    normalized_name = ''
    extension = None

    try:
        filename, extension = filename.translate(TRANS).split(".")
    except ValueError:
        filename = filename.translate(TRANS)

    for symbol in filename:
        if is_not_valid_symbol(symbol):
            normalized_name += "_"
        else:
            normalized_name += symbol

    return normalized_name \
        if not extension \
        else f'{normalized_name}.{extension}'


def is_not_valid_symbol(symbol: str) -> bool:
    return symbol.isnumeric() \
        or symbol in CYRILLIC_SYMBOLS \
        or symbol in ' !@#$%^*()&+-='


def rename_entry(path: str, old_name: str, new_name: str) -> None:
    os.rename(os.path.join(path, old_name),
              os.path.join(path, new_name))


def move_file(file_path: str, file_name: str) -> None:
    # get the extension of the file
    ext = file_name.split('.')[-1]

    # if extension is not in dictionary
    # then use file path for 'other'
    shutil.move(os.path.join(file_path, file_name),
                os.path.join(PATHS.get(ext.upper(), PATHS['OTHER']), file_name))


def remove_all_empty_dirs(root: str) -> None:
    deleted = set()

    for current_dir, subdirs, files in os.walk(root, topdown=False):

        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break

        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)


if __name__ == '__main__':
    root = sys.argv[1]
    set_dirs(root)
    sort(root)
    remove_all_empty_dirs(root)
