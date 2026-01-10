import sys #???
import json
import asyncio #???
import os
from dotenv import load_dotenv
from datetime import datetime
from kasa import SmartPlug

load_dotenv()

# Get plugs + schedules
## ex. plug_0, ontime: 12:00, offtime: 18:00

SCHEDULE_FILEPATH = './schedule.json'

def is_time_in_range(start_time_str, end_time_str, curr_time):
    # Convert time strings into date objects
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strp(end_time_str, '%H:%M').time()

    # Normal ranges (12:00 to 20:00)
    if start_time == end_time:
        return False # Edge case where someone might accidentally put the wrong times. (me)
    elif start_time <= end_time:
        return start_time <= curr_time <= end_time
    else: # Unique ranges (22:00 to 2:00)
        # Range: After start (22:00 - 24:00/00:00), Before start (00:00 - 2:00)
        return curr_time >= start_time or curr_time <= end_time
        
async def turn_plug_on_safely(plug, plug_id):
    print(f'Sending request to turn ON {plug_id}...')

    # Attempt to turn on
    await plug.turn_on()

    # Incase of hardware lag:
    await asyncio.sleep(1)

    # Refresh the plug's state
    await plug.update()

    if plug.is_on:
        print(f'{plug_id} has been turned on!')
    else:
        print(f'ERROR: {plug_id} is still off!')
    
    return

async def turn_plug_off_safely(plug, plug_id):
    print(f'Sending request to turn OFF {plug_id}...')

    await plug.turn_off()
    await asyncio.sleep(1)
    await plug.update()

    if plug.is_on:
        print(f'ERROR: {plug_id} is still on!')
    else:
        print(f'{plug_id} has been turned off!')
    
    return


async def main():
    # Current time in HH:MM format
    now = datetime.now().strftime('%H:%M')

    try:
        with open(SCHEDULE_FILEPATH, 'r') as file:
            schedule = json.load(file)
    except FileNotFoundError:
        print(f'Schedule file can not be read. Current filepath: {SCHEDULE_FILEPATH}')
        return
    
    ''' Example JSON format for each schedule object:
    {
        "plug_id": "PLUG_0",
        "on_times": ["00:00", "12:00"],
        "off_times": ["06:00", "18:00"]
    }
    '''
    for p in schedule:
        turn_plug_on = False

        # Iterating through all of a plug's time ranges
        try:
            for time_range in schedule.get("active_ranges", []):
                if is_time_in_range(time_range["start"], time_range["end"], now):
                    turn_plug_on = True
                    break # Rather than turn_lights_on = yadayada, we'd want to break if this is on alrdy, no need to check the other time ranges
        except Exception as e:
            print(f'Error trying to collect scheduled times: {e}')
        
        try:
            plug_id = schedule["path_id"]
            plug_ip = os.getenv(plug_id)
            plug = SmartPlug(plug_ip)
            await plug.update()

            # Turn on plug
            if turn_plug_on:
                print(f'Curr time ({now.strftime('%H:%M')}) is within active range.')
                if plug.is_on:
                    print(f'{plug_id} is already on!')
                else:
                    turn_plug_on_safely(plug, plug_id)
            
            # Turn off plug
            else:
                print(f'Curr time ({now.strftime('%H:%M')}) is outside the active range.')
                if plug.is_on:
                    turn_plug_off_safely(plug, plug_id)
                else:
                    print(f'{plug_id} is already off!')
            
        except Exception as e:
            print(f'Error connecting to a plug: {plug_id if plug_id else 'Unknown plug'}, {e}')

if __name__ == '__main__':
    asyncio.run(main())
