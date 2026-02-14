# HomeLab: smart-plug-automation

Using Kasa HS103 Smart Plugs purchased online, I connected them into my home router but without access to the internet. This would allow for me to have full control of the Smart Plugs since it couldn't attempt any firmware updates.

I was able to make use of [python-kasa](https://github.com/python-kasa/python-kasa) to control different Smart Plug functions. Everything is currently running off of my Raspberry Pi 4 at home.

## Scripts:
  * ### scheduler.py:
    * As of now, just scheduled on/off functions are used for the Smart Plugs. This was originally set up to tackle a problem of sometimes forgetting to properly and consistently turn on and off lights for my pet turtle, Freddy, but the on/off function should be useful for other random applications I may have in the future.
    * Rather than using a set on/off time, I have the Pi use Cron to check this script every 30 minutes. If for any reason the Raspberry Pi missed the original start time, as long as it's currently within the active range, it'll still turn on.
    * The script was also set in such a way where the only changing file would be the JSON file (schedule.json), and will allow for iterations of all 4 plugs I possess with the possibility of all plugs have unlimited active time ranges.
    
    ![](https://i.imgur.com/Q37NBiP.png)

## Required .env variables
(-): Backups incase not present

### logger.py
* (-) LOG_STATE ('debug' or 'info')
* (-) LOG_ONLY (bool)

### scheduler.py
Dependent on schedule.json plug_id's:
* PLUG_0 (IP address)
* PLUG_1 (IP address)
* PLUG_2 (IP address)
* PLUG_3 (IP address)
