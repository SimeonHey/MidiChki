import logging
import time
import explorerhat as eh
import pygame.midi
from random import random
from concurrent.futures import ProcessPoolExecutor
from requests_futures.sessions import FuturesSession

session = FuturesSession(executor=ProcessPoolExecutor(max_workers=3))
logging.basicConfig(level=logging.INFO)


def random_between(start, to):
    return int(start + random() * (to - start))


def find_roland_id():
    pygame.midi.quit()
    pygame.midi.init()

    device_cnt = pygame.midi.get_count()
    logging.info(f"{device_cnt} USB devices connected...")

    for i in range(device_cnt):
        info = pygame.midi.get_device_info(i)

        name = str(info[1])
        is_input = info[2]

        logging.info(f"Checking {name}, is_input={is_input}...")
        if is_input and "Roland" in name:
            print(f"Found it on id {i}!")
            return i

    logging.warning("Couldn't find Roland...")
    raise FileNotFoundError("Couldn't find Roland...")


def wait_for_roland():
    while True:
        try:
            roland_id = find_roland_id()
            break
        except FileNotFoundError as e:
            logging.info("Retrying...")
            time.sleep(1)

    return pygame.midi.Input(roland_id)


def handle_note_pressed(note, velocity):
    global rotating

    prev = rotating
    while prev == rotating:
        rotating = random_between(0, 4)

    print(f"Pressed note {note} with vel {velocity}")

    rel_vel = velocity / 127 * 100
    lights[rotating].fade(rel_vel, 0, 0.1)


def read_to_string(read, cur_time):
    return f"{read[0][0]},{read[0][1]},{read[0][2]},{read[0][3]},{read[1]},{cur_time}"


# write_path = "/media/pi/SS Backup/midichki/simefile.txt"
write_path = "/home/pi/Documents/Developing/MidiChki/dontgitit/simefile.txt"
def persist_stuff(strval):
    with open(write_path, 'a+') as the_file:
        the_file.write(strval + "\n")


upload_url = "https://mighty-island-21925.herokuapp.com/postNotes"
# upload_url = "http://192.168.43.223:8080/postNotes"
def upload_stuff(reads):
    logging.info(f"Uploading {len(reads)} values to {upload_url}")
    session.post(upload_url, json=reads)


def midi_event(read, cur_time):
    data, timestamp = read
    status, note, velocity, idk = data

    if status == 144:
        handle_note_pressed(note, velocity)

    strval = read_to_string(read, cur_time)
    persist_stuff(strval)


# Set global state
lights = [eh.light.yellow, eh.light.blue, eh.light.red, eh.light.green]
rotating = 0

if __name__ == '__main__':
    logging.info("Hello!")

    roland = wait_for_roland()

    last_note_time = time.time()

    logging.info("Indefinitely listening for notes...")
    while True:
        reads = roland.read(100)
        # reads = [[[144, 2, 3, 4], 5]]
        time.sleep(1)
        logging.info(f"Read {len(reads)} stuff")

        cur_time = time.time()

        if len(reads) == 0:
            elapsed = cur_time - last_note_time
            if elapsed > 5:
                try:
                    roland.close()
                except Exception:
                    logging.info("Roland was indeed detached")
                    raise Exception("Exiting... Start me again!")

                roland = wait_for_roland()
                last_note_time = cur_time
        else:
            last_note_time = cur_time
            for read in reads:
                midi_event(read, cur_time)

            upload_stuff(list(map(lambda read: read[0] + [read[1], cur_time], reads)))

