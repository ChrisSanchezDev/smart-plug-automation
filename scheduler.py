#TODO: Replace SmartPLug for kasa.iot or Discover.discover_single() and Device.connect()

import sys #???
import json
import asyncio #???
import os
from dotenv import load_dotenv
from datetime import datetime
from kasa import SmartPlug

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILEPATH = os.path.join(BASE_DIR, 'schedule.json')

def is_time_in_range(start_time_str, end_time_str, curr_time):
    # Convert time strings into date objects
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()

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

async def enabled_action(schedule, now):
    for p in schedule:
        turn_plug_on = False

        # Iterating through all of a plug's time ranges
        try:
            for time_range in p.get("active_ranges", []):
                if is_time_in_range(time_range["start"], time_range["end"], now):
                    turn_plug_on = True
                    break # Rather than turn_lights_on = yadayada, we'd want to break if this is on alrdy, no need to check the other time ranges
        except Exception as e:
            print(f'Error trying to collect scheduled times: {e}')
        
        try:
            plug_id = p.get("plug_id", str('Unknown plug'))
            plug_ip = os.getenv(plug_id)
            plug = SmartPlug(plug_ip)
            await plug.update()

            # Turn on plug
            if turn_plug_on:
                print(f'Curr time ({now.strftime('%H:%M')}) is within active range.')
                if plug.is_on:
                    print(f'{plug_id} is already on!')
                else:
                    await turn_plug_on_safely(plug, plug_id)
            
            # Turn off plug
            else:
                print(f'Curr time ({now.strftime('%H:%M')}) is outside the active range.')
                if plug.is_on:
                    await turn_plug_off_safely(plug, plug_id)
                else:
                    print(f'{plug_id} is already off!')
            
        except Exception as e:
            print(f'Error connecting to a plug: {plug_id}, {e}')

async def disabled_action(schedule):
    print('Currently ignoring all scheduled activities.')
    turn_plug_on = False
    for p in schedule:
        try:
            plug_id = p.get("plug_id", str('Unknown plug'))
            plug_ip = os.getenv(plug_id)
            plug = SmartPlug(plug_ip)
            await plug.update()

            if plug.is_on:
                await turn_plug_off_safely(plug, plug_id)
            else:
                print(f'{plug_id} is already off!')
            
        except Exception as e:
            print(f'Error connecting to a plug: {plug_id}, {e}')

async def forced_action(schedule):
    print('Currently ignoring all scheduled activities.')
    turn_plug_on = True
    for p in schedule:
        try:
            plug_id = p.get("plug_id", str('Unknown plug'))
            plug_ip = os.getenv(plug_id)
            plug = SmartPlug(plug_ip)
            await plug.update()

            if plug.is_on:
                print(f'{plug_id} is already on!')
            else:
                await turn_plug_on_safely(plug, plug_id)
            
        except Exception as e:
            print(f'Error connecting to a plug: {plug_id}, {e}')

async def main():
    # Current time
    now = datetime.now().time()

    try:
        with open(SCHEDULE_FILEPATH, 'r') as file:
            schedule = json.load(file)
    except FileNotFoundError:
        print(f'Schedule file can not be read. Current filepath: {SCHEDULE_FILEPATH}')
        return
    except json.JSONDecodeError:
        print('Error: The file exists but contains invalid JSON.')
        return

    # ENABLED, DISABLED, FORCE_ON LOGIC
    schedule_state = schedule[0].get('schedule_state', 'ENABLED')
    print(f'-----scheduler.py | STATE: {schedule_state} | {now}-----')
    
    if len(schedule) > 1: # Just so the code doesn't run an empty schedule
        if schedule_state == 'ENABLED':
            await enabled_action(schedule[1:], now)
        elif schedule_state == 'DISABLED':
            await disabled_action(schedule[1:], now)
        elif schedule_state == 'FORCE_ON':
            await forced_action(schedule[1:], now)
    print('---------------')
    
if __name__ == '__main__':
    asyncio.run(main())
