import time
from datetime import datetime
import os
import sys
from enum import Enum, auto


class KeyPoller():
    def __enter__(self):
        self.is_windows = (os.name == "nt")
        if(self.is_windows):
            import msvcrt
            self.msvcrt = msvcrt
        
        return self
    
    def __exit__(self, exc_type, exc, tb):
        return None
    
    def get_key(self):
        """Return a single character if available, else None."""
        if self.is_windows:
            if self.msvcrt.kbhit():
                ch = self.msvcrt.getwch()
                return ch
            return None


#Commands to control timer
class Command(Enum): 
    CONTINUE = auto()
    PAUSE = auto()
    QUIT = auto()
    SKIP = auto()

class PomodoroBasic():
    WORK_MIN = 25
    SHORT_BREAK_MIN = 5
    LONG_BREAK_MIN = 15

    #Current Test Values
    WORK_SECS = 10 # WORK_MIN * 60
    SHORT_BREAK_SECS = 3 # SHORT_BREAK_MIN * 60
    LONG_BREAK_SECS = 5 # LONG_BREAK_MIN * 60    



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



    #Classic countdown, old version
    def countdown(self, secs):
        while (secs > 0):
            print(self.format_seconds(secs))
            time.sleep(1)
            secs -= 1

    #According to rotation, start the relevant session, old
    def session(self, rotation: int):
        if(rotation%2 == 0):
            print("Work session started.")
            self.countdown(self.WORK_SECS)
        elif(rotation%6 == 5):
            print("Long break started.")
            self.countdown(self.LONG_BREAK_SECS)
        else:
            print("Short break started.")
            self.countdown(self.SHORT_BREAK_SECS)

    #Return the name of the current session
    def which_rotation(self, rotation: int) -> str:
        if(rotation%2 == 0):
            return "Work session"
        elif(rotation%6 == 5):
            return "Long break session"
        else:
            return "Short break session"




        #Pomodoro for fixed number of work sessions, old
    def pomodoro_start(self, rounds: int):
        rotation = 0
        for _ in range(rounds*2):
            
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

            


    #Pomodoro (Infinite), old
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

class Pomodoro():
    WORK_MIN = 25
    SHORT_BREAK_MIN = 5
    LONG_BREAK_MIN = 15

    #Current Test Values
    WORK_SECS = 10 # WORK_MIN * 60
    SHORT_BREAK_SECS = 3 # SHORT_BREAK_MIN * 60
    LONG_BREAK_SECS = 5 # LONG_BREAK_MIN * 60

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
                cmd = input("[Enter=continue | p=pause | q=quit | s=skip] > \n").strip().lower()

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
    


    #New countdown with real time controls
    def countdown_with_controls(self, secs: int):
        paused = False

        print("Controls: [p]=pause/resume  [s]=skip  [q]=quit\n")
        with KeyPoller() as keys:
            counter = 0
            secs = secs
            while secs >= 0:
                # Check key without blocking
                k = keys.get_key()
                if k:
                    k = k.lower()
                    if k == "q":
                        print("\nQuitting...")
                        return "quit"
                    if k == "s":
                        print("\nSkipped.")
                        return "skip"
                    if k == "p":
                        paused = not paused
                        print("\nPaused." if paused else "\nResumed.")

                if not paused:
                    # Print remaining time (overwrite same line)
                    print(f"\r{self.format_seconds(secs)}", end="", flush=True)
                    time.sleep(0.05)
                    #counter mechanism is added to prevent feeling of lag when pressing a key
                    counter += 1
                    if(counter == 19):
                        secs -= 1
                        counter = 0
                else:
                    # While paused, don't decrement; keep loop responsive
                    time.sleep(0.05)  
            
            print("\n\n")



        #According to rotation, start the relevant session, old
    def session_real_time(self, rotation: int) -> str:
        if(rotation%2 == 0):
            print("Work session started.\n")
            return self.countdown_with_controls(self.WORK_SECS)
        elif(rotation == 5):
            print("Long break started.\n")
            return self.countdown_with_controls(self.LONG_BREAK_SECS)
        else:
            print("Short break started.\n")
            return self.countdown_with_controls(self.SHORT_BREAK_SECS)
    
    #Return the name of the current session
    def which_rotation(self, rotation: int) -> str:
        if(rotation%2 == 0):
            return "Work session"
        elif(rotation%6 == 5):
            return "Long break session"
        else:
            return "Short break session"




    def pomodoro_real_time(self):
        rotation = 0
        while True:
            while True:
                cmd = self.ask_command()

                match cmd:
                    case Command.QUIT:
                        return
                    case Command.CONTINUE:
                        break
                    case Command.SKIP:
                        print(f"Skipped {self.which_rotation(rotation)}, waiting to continue...")
                        rotation += 1
                        pass
            
            new_instr = self.session_real_time(rotation)

            if new_instr == "quit":
                return
            if new_instr == "skip":
                print(f"Skipped current session: {self.which_rotation(rotation)}, waiting to continue...")
                rotation += 1
                continue
            rotation += 1
            

pmdr = Pomodoro()
pmdr.pomodoro_real_time()