"""Merge the validated source/data checkpoint into one portable project ZIP."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT.parent/'VIGILANT-project.zip'
    archives = [ROOT.parent/'VIGILANT-data.zip', ROOT.parent/'VIGILANT-source.zip']
    entries = {}
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise ValueError('Corrupt input archive: '+str(archive))
            for member in z.infolist():
                p = Path(member.filename)
                if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != 'VIGILANT':
                    raise ValueError('Unsafe archive path')
                if not member.is_dir() and not p.name.startswith('ARCHIVE-MANIFEST-'):
                    entries[member.filename] = archive
    with tempfile.TemporaryDirectory(prefix='vigilant-package-') as tmp:
        staged = Path(tmp)/destination.name
        handles = {p: zipfile.ZipFile(p) for p in archives}
        try:
            manifest = []
            with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as out:
                for name, archive in sorted(entries.items()):
                    data = handles[archive].read(name)
                    out.writestr(name, data)
                    manifest.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
                out.writestr('VIGILANT/PACKAGE-MANIFEST.json', json.dumps(manifest, indent=2))
        finally:
            for z in handles.values():
                z.close()
        with zipfile.ZipFile(staged) as z:
            if z.testzip() is not None:
                raise ValueError('Packaged ZIP failed integrity check')
        pending = destination.with_suffix('.pending')
        shutil.copyfile(staged, pending)
        os.replace(pending, destination)
    record = {'path': str(destination), 'bytes': destination.stat().st_size,
              'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'files': len(manifest)}
    (ROOT.parent/'VIGILANT-project-checksum.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
