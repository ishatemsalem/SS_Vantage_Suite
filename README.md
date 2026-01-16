# SS Vantage Suite (v1.0.0)

**SS Vantage Suite** is a semi-polished collection of tools I made during my time at **Neuron Studios**. This is a direct port of the workflows I used to hit studio deadlines for high-profile commissions.

> **Developer’s Note:** As of this moment, I have only had time to implement my legacy character creation scripts grouped under the codename "OrthoMetric". Expansions planned.


## Key Features

* **OM_Lineup:** Designed to quickly line up orthographic views, toggle between cameras, and save specific viewing angles. Plenty of quality of life features. Proportions are also saved and easy to switch between.
* **OM_General Deform (In Development):** Designed to snap a base mesh's basic features and proportions to reference empties.

## ⚠️ Before Use:

To ensure the automated import logic works correctly:
**You must add your Horizontal Reference Image before adding any other views.** The suite uses this stage to import the base model.

Calibration edge-cases require sanding, if your character's face in the imported picture is smaller than the base model, scale up till its just a little larger

## Installation

1. Download the latest release `.zip`.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the zip file.
4. Enable **SS Vantage Suite**.
SS OrthoMetric tab on the n-panel should appear, containing Character Creation Workflow tools

## Technical Stack

* **Language:** Python (Blender API)
* **Status:** Version 1.0.0 (Legacy Character Workflow Focus) (I guess you could call this a Pre-Release Version)
* **Compatibility:** Optimized for Blender 4.2.0


## 🏗 Built With
* Python (Blender API)
* Unfiltered Egyptian ingenius
* Lots of love

* Also lots of tears blender's API is hilariously inconsistent

