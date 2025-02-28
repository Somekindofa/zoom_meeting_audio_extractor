# Zoom Meeting Audio Extractor
## Introduction
A Zoom Meeting middle-ware that listens to both parties and records the audio in an output file for downstream tasks (database, ML training...)

## Pre-requisites
### Downloading a virtual audio cable
You will need an audio mirroring driver called [**VB-CABLE Virtual Audio Device**](https://vb-audio.com/Cable/).
Once installed, you will need to restart your computer for the driver to install.
This will implement two virtual audio cables called "CABLE Output" and "CABLE Input".
- The former is what the Python script listens on
- The latter is where Zoom meeting's audio output is sent to.

The *data flow* is the following:

**Expert speaks → Zoom → CABLE Input → CABLE Output → Python script captures it**

In order to be able to speak seamlessly, the CABLE Output has an audio duplication feature that allows routing the audio to your speakers (or other output) as well as being captured by the script for processing.

### Setting up Windows Audio Settings
If you are using Windows, follow these instructions:
- Right-click on "CABLE Output" in your Recording devices
- Select "Properties"
- Go to the "Listen" tab
- Check "Listen to this device"
- From the dropdown menu, select your speakers or headphones
- Click "Apply" and "OK"

Also, in your taskbar's audio icon, click on it and set both your Speakers and Microphone to your usual devices.

e.g.
{*Input*: Microphone (Realtek),
*Output*: Speakers}

### Configuring Zoom's Audio Settings
- Open Zoom
- Go to Settings → Audio
- For Speaker: Select "CABLE Input" (this sends the expert's voice to your virtual cable)
- For Microphone: Keep your regular microphone selected (not the virtual cable)

## Installation
Clone this repository locally using:

```bash 
git clone "https://github.com/Somekindofa/zoom_meeting_audio_extractor/"
```
Then install the script requirements with ```pip```:

```bash 
pip install -r requirements.txt
```

## How to use
For now, the script listens to "CABLE Output" for 10 seconds then writes the audio to ```output.wav``` file in the same working directory.
Further processing will be done such as sending chunks to a Whisper model using an inference endpoint.
