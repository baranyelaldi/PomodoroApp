import time
from datetime import datetime
import os
from enum import Enum, auto

#Commands to control timer
class Command(Enum): 
    CONTINUE = auto()
    PAUSE = auto()
    QUIT = auto()
    SKIP = auto()


class Pomodoro():
    WORK_MIN = 25
    SHORT_BREAK_MIN = 5
    LONG_BREAK_MIN = 15

    #Current Test Values
    WORK_SECS = 3 # WORK_MIN * 60
    SHORT_BREAK_SECS = 1 # SHORT_BREAK_MIN * 60
    LONG_BREAK_SECS = 2 # LONG_BREAK_MIN * 60

    #For spammed enter in the terminal
    def flush_stdin(self):
        # Windows-only: clear pending keypresses (including spammed Enter)
        if os.name == "nt":
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()

    #Return enumarated command
    def ask_command(self) -> int:
        while True:
                self.flush_stdin()  
                cmd = input("[Enter=continue | p=pause | q=quit | s=skip] > ").strip().lower()

                if cmd == "":
                    return Command.CONTINUE
                elif cmd == "q":
                    print("Quitting...")
                    return Command.QUIT
                elif cmd == "s":
                    print("Skipping...")
                    return Command.SKIP
                else:
                    print("Please enter a known command")

    #Format the seconds in minute and second format(no more than an hour is alloved in my pomodoro)
    def format_seconds(self, secs: int) -> str:
        return time.strftime("%M:%S", time.gmtime(secs))

    #Classic countdown
    def countdown(self, secs):
        while (secs > 0):
            print(self.format_seconds(secs))
            time.sleep(1)
            secs -= 1
    
    #According to rotation, start the relevant session
    def session(self, rotation: int):
        if(rotation%2 == 0):
            print("Work session started.")
            self.countdown(self.WORK_SECS)
        elif(rotation == 5):
            print("Long break started.")
            self.countdown(self.LONG_BREAK_SECS)
        else:
            print("Short break started.")
            self.countdown(self.SHORT_BREAK_SECS)
    
    #Return the name of the current session
    def which_rotation(self, rotation: int) -> str:
        if(rotation%2 == 0):
            return "Work session"
        elif(rotation == 5):
            return "Long break session"
        else:
            return "Short break session"

    #Pomodoro for fixed number of work sessions
    def pomodoro_start(self, rounds: int):
        rotation = 0
        for i in range(rounds*2):
            
            while True:
                cmd = self.ask_command()

                match cmd:
                    case Command.QUIT:
                        return
                    case Command.SKIP:
                        print(f"Skipped {self.which_rotation(rotation)}, waiting to continue...")
                        rotation += 1
                        continue
                    case Command.CONTINUE:
                        break
            
            self.session(rotation)
            rotation += 1

            
    #Pomodoro (Infinite)
    def pomodoro_start(self):
        rotation = 0
        while True:
            while True:
                cmd = self.ask_command()

                match cmd:
                    case Command.QUIT:
                        return
                    case Command.SKIP:
                        print(f"Skipped {self.which_rotation(rotation)}, waiting to continue...")
                        rotation += 1
                        continue
                    case Command.CONTINUE:
                        break
            
            self.session(rotation)
            rotation += 1
            

pmdr = Pomodoro()
pmdr.pomodoro_start()