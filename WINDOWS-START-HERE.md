# Run VIGILANT on Ankith's Windows computer

The requested destination is `C:\Users\Ankith\Downloads\Code- Vigilant`.
The development session runs on Linux and cannot directly access that drive.
These instructions install the delivered files locally. They do not claim a remote write has occurred.

1. Download `VIGILANT-project.zip` and `Install-VIGILANT.ps1` to the same folder.
2. In PowerShell in that folder, run `./Install-VIGILANT.ps1`. The script refuses to overwrite a nonempty destination. Alternatively, extract the ZIP and move the contents of its `VIGILANT` folder into your chosen destination.
3. Install Python 3.12, Git for Windows and Node.js with npm if they are missing.
4. Open PowerShell in `C:\Users\Ankith\Downloads\Code- Vigilant`.
5. Run `./Setup-Windows.ps1 -DownloadModels`. Setup installs a project-local Python environment, builds the frontend, restores recorded data and runs the tests. The package already includes the pinned raw datasets and repositories. Downloads require internet access. The local language model requires several GB of disk and RAM.
6. Run `./Start-VIGILANT.ps1`, then open `http://127.0.0.1:8000`.

If PowerShell blocks a downloaded script, follow your computer's normal trusted-script policy. You can also run the commands in `docs/REPRODUCIBILITY.md` manually. The package does not change execution policy or request administrator access.

The delivered frontend uses the local API and recorded database. Model binaries and installed dependencies are recreated from pinned configurations. Review `RESUME.md` and `docs/FINAL_STATUS.md` for completed work and research limitations.

Windows scripts are provided for your machine. They were reviewed in the Linux development environment; a Windows execution test remains to be performed on your computer.
