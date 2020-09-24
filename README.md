# Clip-Manager

Primarily used to trim down Shadowplay recordings and share to Streamable.com.

## Requirements

* [K-Lite Codecs](https://codecguide.com/download_k-lite_codec_pack_basic.htm) (for video playback)
* [FFMPEG & FFProbe](https://ffmpeg.org/download.html) (for video trimming and thumbnail generating)

## Setup

1. Download and extract the latest release from the [releases page](https://github.com/zahidul23/clip-manager/releases/).
2. Install K-Lite Codecs from link above (recommended) or simply run the 3 files, "install_audio.bat", "install_video.bat", "install_splitter.bat" inside the "install_first" folder. The latter method may result in choppy playback. 
3. FFMPEG is already provided, no need for additional downloads.
4. Run clips.exe.

First time setup will require selection of videos folder and login details for uploading to Streamable. Settings will be saved as a settings.json file in the executable's folder with the password encrypted.

![python_9QS9h1e9pE](https://user-images.githubusercontent.com/22843707/94120833-975ab680-fe1e-11ea-8408-c97f22a08a03.png)


## Usage

All videos within the selected folder and its subfolders will be shown on the main window.

![python_UlclF1ZzKZ](https://user-images.githubusercontent.com/22843707/94120516-36cb7980-fe1e-11ea-817b-f074f6746ecf.png)

Folders will be monitored and when a new video file is detected, it will be added to the top of the grid from right to left. It may take a few seconds to create the thumbnail and be added to the grid.

![python_jrQoaLkSXz](https://user-images.githubusercontent.com/22843707/94121068-e56fba00-fe1e-11ea-8db6-3375b9734012.png)

Click on the video thumbnail to open the editor. Use the top slider to choose start and end points for the video. The trim button will use FFMPEG to instantly create a separate file with the desired length. The new video will be placed at the top of the grid.

![python_B6MX6D6wpR](https://user-images.githubusercontent.com/22843707/94131444-eb1fcc80-fe2b-11ea-86e6-b58542737870.png)

Right-click a video thumbnail to upload the file to Streamable. Upon completion, the button will be enabled to open the uploaded video URL.

![ApplicationFrameHost_sdx7GYbVX5](https://user-images.githubusercontent.com/22843707/94122684-dd187e80-fe20-11ea-8580-a26acd7e8586.png)![python_DluykkYrOd](https://user-images.githubusercontent.com/22843707/94122513-a5a9d200-fe20-11ea-8d31-9d9cf591cacd.png)![python_ofVBQxWyMq](https://user-images.githubusercontent.com/22843707/94122521-a80c2c00-fe20-11ea-800b-e8d9c8fe51cc.png)![python_PXIcJfcfFv](https://user-images.githubusercontent.com/22843707/94122526-a9d5ef80-fe20-11ea-8a4c-fb486de0c208.png)


## Dependencies

* PyQt5 (https://pypi.org/project/PyQt5/)
* watchdog (https://pypi.org/project/watchdog/)
* requests-toolbelt (https://pypi.org/project/requests-toolbelt/)
* cryptography (https://pypi.org/project/cryptography/)
* ffmpy (https://pypi.org/project/ffmpy/)
* QRangeSlider (https://github.com/rsgalloway/qrangeslider)
