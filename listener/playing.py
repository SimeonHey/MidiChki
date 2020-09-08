#!venv37/bin/python
import logging
import time
import pygame.midi
import argparse

from random import random

import subscribers
from utils.classes import MidiNote


# from simple_lights import SimpleLights
logging.basicConfig(level=logging.INFO)


def find_piano_id(device_name):
    pygame.midi.quit()
    pygame.midi.init()

    device_cnt = pygame.midi.get_count()
    logging.info(f"{device_cnt} USB devices connected...")

    for i in range(device_cnt):
        info = pygame.midi.get_device_info(i)

        name = str(info[1])
        is_input = info[2]

        logging.info(f"Checking {name}, is_input={is_input}...")
        if is_input and device_name in name:
            print(f"Found it on id {i}!")
            return i

    logging.warning("Couldn't find piano...")
    raise FileNotFoundError("Couldn't find piano...")


def wait_for_piano(device_name):
    while True:
        try:
            piano_id = find_piano_id(device_name)
            break
        except FileNotFoundError as e:
            logging.info("Retrying...")
            time.sleep(1)

    return pygame.midi.Input(piano_id)


def read_to_string(read, cur_time):
    return f"{read[0][0]},{read[0][1]},{read[0][2]},{read[0][3]},{read[1]},{cur_time}"


# write_path = "/media/pi/SS Backup/midichki/simefile.txt"
write_path = "/home/pi/Developing/MidiChki/dontgitit/simefile.txt" # TODO: Make a cli argument
def persist_stuff(strval):
    with open(write_path, 'a+') as the_file:
        the_file.write(strval + "\n")


# upload_url = "https://mighty-island-21925.herokuapp.com/postNotes"
# upload_url = "http://192.168.0.151:8080/postNotes"


def midi_events(reads, cur_time, subscriber_queues):
    to_upload = []

    for read in reads:
        data, timestamp = read
        status, note, velocity, idk = data

        if status != 248: # This is a midi clock which we dislike
            note = MidiNote(read[0][1], read[0][2], read[0][0], read[1])

            strval = read_to_string(read, cur_time)
            # persist_stuff(strval)

            for q in subscriber_queues:
                q.put(note)


if __name__ == '__main__':
    logging.info("Hello!")

    parser = argparse.ArgumentParser(description='Stream Midichki to the server')
    parser.add_argument('-p', '--piano', required=True)
    parser.add_argument('-u', '--upload', required=True)
    args = parser.parse_args()

    device_name = args.piano
    upload_dest = args.upload

    subscriber_queues = subscribers.enable_subscribers()

    piano = wait_for_piano(device_name)

    logging.info("Indefinitely listening for notes...")
    last_note_time = time.time()
    while True:
        reads = piano.read(100)
        time.sleep(0.05) # in seconds
        logging.info(f"Read {len(reads)} stuff")

        cur_time = time.time()

        if len(reads) == 0:
            elapsed = cur_time - last_note_time
            if elapsed > 5:
                try:
                    piano.close()
                except Exception:
                    logging.info("piano was indeed detached")
                    raise Exception("Exiting... Start me again!")

                piano = wait_for_piano(device_name)
                last_note_time = cur_time
        else:
            last_note_time = cur_time
            midi_events(reads, cur_time, subscriber_queues)

