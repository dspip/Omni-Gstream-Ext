# OmniGstream Extension

## Overview

The OmniGstream extension for NVIDIA Omniverse provides a streamlined interface for capturing and streaming video frames from the Omniverse viewport using GStreamer.

## Features

- Capture video frames from the Omniverse viewport.
- Stream video in real-time using GStreamer.
- Support for adjustable frame rates and resolutions.
- Configurable pipeline settings for optimized performance.
- Easy integration with existing Omniverse workflows.

## Prerequisites

- NVIDIA Omniverse installed.
- GStreamer installed on your machine.

## Setup

To start using the OmniGstream extension in NVIDIA Omniverse, follow these steps:

1. **Clone the Project and Link it in Omniverse Extension Manager**
   - Clone the OmniGstream repository to your local machine:
   - Open NVIDIA Omniverse and go to the **Extensions** window (usually found under `Window > Extensions`).
   - Click on **Add Extension Search Path** and add the path to the OmniGstream folder you just cloned.
   - Once added, you should see the **OmniGstream** extension appear in the list of available extensions.
  
     [Screencast from 03-11-24 14:36:51.webm](https://github.com/user-attachments/assets/324121c2-0c12-46e7-a4c8-48fdae07fcd5)

2. **Enable the Extension and Initialize GStreamer**
   - In the Omniverse **Extensions** window, locate **OmniGstream** and toggle it to enable the extension.
   - Initialize the GStreamer pipeline by running the extension from the command line or any preferred script runner. Alternatively, GStreamer can be initialized directly within the Omniverse environment once the extension is enabled.

3. **Start Streaming via the UI Button**
   - Open the **OmniGstream** extension window in Omniverse.
   - You’ll see a button labeled **Init**. Click this button to initialize the GStreamer link and begin streaming video from your Omniverse viewport.

     [Screencast from 03-11-24 14:26:52.webm](https://github.com/user-attachments/assets/4343b69b-ef52-48e7-a047-5883b4a51615)

You should now be streaming the Omniverse viewport to the specified destination! For additional settings and customization, refer to the configuration options in the extension's UI.

https://github.com/user-attachments/assets/4d01a0b6-2e56-4c28-95d7-8ff40704571d










