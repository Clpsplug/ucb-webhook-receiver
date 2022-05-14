# Unity Cloud Build Webhook Handler
Powered by CherryPy

## What is this?

This scripts boots a server that can accept webhook payloads from Unity Cloud Build
and handle the artifact so that:
* the latest artifacts are always at the specific paths
* the previous artifacts are archived with the timestamp at when the archive occurs.

## Why

This program was made to ensure that we don't have to download the artifacts from UCB by hand
and the correct artifacts are in the correct directories,
so that the same script can be used each time you update your game.

This may be achievable with Jenkins, but I just simply wanted to write this for personal 
educational purposes. So... whatevs.

This script is made with SteamCMD in mind, but if you are downloading the artifacts
from Unity Cloud Build for uploading them to distributor using the similar tools,
this script is for you.

Downloading them by hand is _very_ prone to mistakes. Have you accidentally shipped
a debug version to your regular players? Then consider using this tool.

## Requirements

* Python 3.8
  * Best run on a pipenv environment

Optional:
* Docker

## How to use

### Prepare the script

1. Consider how to serve this webhook.
   * **This script need to be "visible" on the web.**  
     If you have a server that can host this script, you can use that,  
     but if you don't, you may serve it from your PC, in which case you should set up
     a tunnel.  
     Search "webhook tunnel" for a starting idea how to do this.
2. Copy the .env.example file and rename it to `.env` (or copy the content of the next step.)
3. Set the content of the `.env`:
```dotenv
# keep it false unless you know what you are doing
APP_DEBUG=false
# It is your responsibility to set this random authorization key for UCB.
# Use whatever method you'd like but `openssl rand -base64 <integer>` should do.
# Surround the key between double quotes to avoid unexpected results.
# Take note of this value as you will be putting this value in the UCB settings.
# You MUST NOT leave this blank.
UCB_TOKEN="sampleAuthKeyYouGenerated"
# You can increase this, but usually you don't have that many concurrent builds running
# at once, so no need to increase this number
MAX_WORKERS=5
```
4. Prepare the receiving server, or in this case, your PC. 
   * The serving port can be changed by editing `env.conf`.
   * If you decided to run it locally and tunnel it to the Internet:
     * Docker Compose is recommended and is safer.
       * It should work out of the box provided that 
         you have followed the instruction up until this point.
     * Just `docker compose up -d` to fire it up.
     * The serving port settings in `env.conf` should be kept as `8080` in this case. [^1]
     * The host port is also set to `8080`, so expose the `8080` port [^1] via the tunnel.

The server is ready at this point. Now head over to Unity Cloud Build dashboard
and register the webhook.

### Prepare the webhook

1. Go to your Unity Cloud Build webpage (https://dashboard.unity3d.com/)
   and navigate to the "Integrations" page for your project  
   * Sidebar > Project > "Integrations" under "Current Project."
     Make sure your project is what you intended to modify.
2. Press "New Integrations," then select "Webhook," and click "Next."
3. For the events to receive, select "Build Success" under "Cloud Build." Click "Next."
4. Choose any display name, and set webhook URL.
   * If you are typing `localhost` or `127.0.0.1` here, **STOP** as you have not
   fully understood how to serve this webhook receiver.  
   Read the previous section carefully before trying again.
5. For "Authorization Secret," put the auth token created.  
   It must match the one written in `.env` minus the quotes. [^2]
6. The "Authorization Type" dropdown should appear. Select "HMAC-SHA256 Signature."
7. Content Type MUST be "application/json."
8. Leave "Disable SSL/TLS Verification" off.   
   * if you are in a situation where you _have_ to check this option,
    ***seriously*** reconsider your setup.
9. Click "Save."

[^1]: The port can be changed by editing `env.conf` and `docker-compose.yaml`. 
  `env.conf` is for the docker port and `docker-compose.yaml` defines the port 
  on the host (which must be tunneled.)  
[^2]: You MUST NOT leave this blank as it will be weak against malicious payloads.

At this point, this script is ready to receive the webhook. 

## What happens next?

Here is the run-down of what happens on receiving the webhook:

* On successful builds, Unity Cloud Build notifies the script of them
  with the information of where to download the artifact.
* This script will look for the 'primary' artifact, which is most likely your game,
  and make the request to the URL provided in the previous step.
* The downloaded stuff will be temporarily put in the `tmp` directory.
* After extracting the artifact, the script will copy it to the following directory:
    `./output/<Project Name>/<Target Name>`
  * If this directory exists, the existing one will be archived into `./output/archives` first.
  * If you enable IL2CPP, the artifact will contain `BackUpThisFolder_ButDontShipItWithYourGame` directory.
    In the case of UCB, we do not need to back it up, and it will not be copied.

## Limitations & Future Tasks

### No "notarization" ability

This script does not support the "Notarization" required by Apple for macOS applications.
You can set it up on UCB side.

### Automatically trigger other tasks

Not implemented as of now, but very nice to have. This means e.g., to run upload tools after
webhooks are received for each target in a configurable set.

### GUI Task Viewer

Nice to have.

## Advanced Usage

### Add external assets to the artifact
You can add files/directories to your artifacts (such as Addressables bundle files.)
To do this, **place the files into the `./resources/accompaniment/<Project Name>` folder.**  
All the content will be copied to the `output` folder every time an artifact is copied there.

### Get notified of the progress (macOS only)
If run directly on macOS, then the events can be logged as the notification.  
Install `terminal-notifier` to enable the feature.

# License

MIT
