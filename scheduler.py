#TODO: Replace SmartPLug for kasa.iot or Discover.discover_single() and Device.connect()

import json
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from kasa import SmartPlug
from logger import logger
from kasa import Device

logger.info('-----STARTING SCRIPT: scheduler.py-----')

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILEPATH = os.path.join(BASE_DIR, 'schedule.json')

# Current time
now = datetime.now().time()

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
        # Range: After start (22:00 - 23:59), Before start (00:00 - 2:00)
        return curr_time >= start_time or curr_time <= end_time
        
async def turn_plug_on_safely(plug, plug_id):
    logger.debug(f'Sending request to turn ON {plug_id}...')

    # Attempt to turn on
    await plug.turn_on()

    # Incase of hardware lag:
    await asyncio.sleep(1)

    if plug.is_on:
        logger.info(f'{plug_id} has been turned on!')
    else:
        logger.error(f'ERROR: {plug_id} is still off!')

async def turn_plug_off_safely(plug, plug_id):
    logger.info(f'Sending request to turn OFF {plug_id}...')

    await plug.turn_off()
    
    await asyncio.sleep(1)

    if plug.is_on:
        logger.error(f'ERROR: {plug_id} is still on!')
    else:
        logger.info(f'{plug_id} has been turned off!')

async def enabled_action(plug, plug_id, active_ranges):
    turn_plug_on = False

    # Iterating through all of a plug's time ranges
    try:
        for time_range in active_ranges:
            if not time_range:
                logger.info(f'No active ranges detected for {plug_id}! Skipping enabled action')
                return
            if is_time_in_range(time_range["start"], time_range["end"], now):
                turn_plug_on = True
                break # Rather than turn_lights_on = yadayada, we'd want to break if this is on alrdy, no need to check the other time ranges
    except Exception as e:
        logger.error(f'Error trying to collect scheduled times for {plug_id}: {e}')
    
    try:
        # Turn on plug
        if turn_plug_on:
            logger.debug(f'Curr time ({now.strftime('%H:%M')}) is within active range.')
            if plug.is_on:
                logger.debug(f'{plug_id} is already on!')
            else:
                await turn_plug_on_safely(plug, plug_id)
        
        # Turn off plug
        else:
            logger.debug(f'Curr time ({now.strftime('%H:%M')}) is outside the active range.')
            if plug.is_on:
                await turn_plug_off_safely(plug, plug_id)
            else:
                logger.debug(f'{plug_id} is already off!')
        
    except Exception as e:
        logger.error(f'Error connecting to a plug: {plug_id}, {e}')

async def disabled_action(plug, plug_id):
    logger.debug(f'Currently ignoring all scheduled activities for {plug_id}.')
    try:
        if plug.is_on:
            await turn_plug_off_safely(plug, plug_id)
        else:
            logger.debug(f'{plug_id} is already off!')
            
    except Exception as e:
        logger.error(f'Error connecting to a plug \'{plug_id}\': {e}')

async def forced_action(plug, plug_id):
    logger.debug(f'Currently ignoring all scheduled activities for {plug_id}.')
    try:
        if plug.is_on:
            logger.debug(f'{plug_id} is already on!')
        else:
            await turn_plug_on_safely(plug, plug_id)
        
    except Exception as e:
        logger.error(f'Error connecting to a plug \'{plug_id}\': {e}')

async def main():    
    try:
        # with: similar to like file = ..., but if an error occurs, the file is automatically closed.
        with open(SCHEDULE_FILEPATH, 'r') as file:
            schedule = json.load(file)
    except FileNotFoundError:
        logger.error(f'Schedule file can not be read. Current filepath: {SCHEDULE_FILEPATH}')
        return
    except json.JSONDecodeError:
        logger.error('ERROR: The schedule file exists but contains invalid JSON.')
        return

    for schedule_block in schedule:
        try:
            plug_id = schedule_block.get('plug_id', 'Unknown Plug')
            schedule_state = schedule_block.get('schedule_state', 'ENABLED')
            active_ranges = schedule_block.get('active_ranges', [])
            logger.info(f'-Plug: {plug_id} | State: {schedule_state} | {now}-')
            
            plug_ip = os.environ[plug_id]
            plug = await Device.connect(host=plug_ip)
        
            # ENABLED, DISABLED, FORCE_ON LOGIC
            if schedule_state == 'ENABLED':
                await enabled_action(plug, plug_id, active_ranges)
            elif schedule_state == 'FORCE_ON':
                await forced_action(plug, plug_id)
            elif schedule_state == 'DISABLED':
                await disabled_action(plug, plug_id)
            else:
                logger.info(f'Schedule state doesn\'t match current presets (ENABLED, FORCE_ON, DISABLED): {schedule.state}')
                logger.debug(f'Proceeding with disabled_action, but please fix this as soon as possible.')
                await disabled_action(plug, plug_id)
                
        except KeyError as e:
            logger.error(f'Error finding plug_ip using plug_id \'{plug_id}\': {e}')
        except Exception as e:
            logger.error(f'Error defining plug variables: {e}')
            
    logger.info('-----END OF SCRIPT--------------------')
    
if __name__ == '__main__':
    asyncio.run(main())
