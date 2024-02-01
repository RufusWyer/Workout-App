import os
import wx
import threading as th
import time

# Things to add:
# Edit workout screen.
# Ability to pause/play with space bar.
# Controls to prevent problematic data entered into create workout screen.
# Preview button when choosing workouts.


testapp = wx.App()

frames_dictionary = {}


class MainFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(280, 310))
        self.panel = wx.Panel(self)
        self.title_text = wx.StaticText(self.panel, label='Workout Timer', pos=(48, 16))
        font_1 = wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_text.SetFont(font_1)
        self.create_workout_button = wx.Button(self.panel, label='Create New Workout', pos=(56, 150), size=(150, 40),
                                               style=wx.ALIGN_CENTRE_VERTICAL)
        self.create_workout_button.Bind(wx.EVT_BUTTON, self.create_workout_button_pressed)
        self.choose_workout_button = wx.Button(self.panel, label='Start Workout', pos=(56, 60), size=(150, 40),
                                               style=wx.ALIGN_CENTRE_VERTICAL)
        self.choose_workout_button.Bind(wx.EVT_BUTTON, self.choose_workout_button_pressed)
        self.edit_workout_button = wx.Button(self.panel, label='Edit Workout', pos=(56, 200), size=(150, 40),
                                               style=wx.ALIGN_CENTRE_VERTICAL)
        self.edit_workout_button.Bind(wx.EVT_BUTTON, self.edit_workout_button_pressed)
        self.line = wx.StaticLine(self.panel, pos=(20, 124), size=(228, 1))

    def disable_buttons(self):
        self.create_workout_button.Disable()
        self.choose_workout_button.Disable()
        self.edit_workout_button.Disable()

    def enable_buttons(self):
        self.create_workout_button.Enable()
        self.choose_workout_button.Enable()
        self.edit_workout_button.Enable()

    def create_workout_button_pressed(self, e):
        frames_dictionary['create_workout_frame'] = CreateWorkoutFrame('Create New Workout')
        frames_dictionary['create_workout_frame'].Show()
        self.disable_buttons()

    def choose_workout_button_pressed(self, e):
        frames_dictionary['choose_workout_frame'] = ChooseWorkoutFrame('')
        frames_dictionary['choose_workout_frame'].Show()
        self.disable_buttons()

    def edit_workout_button_pressed(self, e):
        frames_dictionary['choose_workout_frame_edit'] = ChooseWorkoutFrameEdit('Edit Workout')
        frames_dictionary['choose_workout_frame_edit'].Show()
        self.disable_buttons()


class ChooseWorkoutFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(205, 400))
        self.panel = wx.Panel(self)
        self.Centre()
        # 'Choose workout' text widget
        self.choose_workout_static = wx.StaticText(self.panel, label='Choose Your Workout:', pos=(20, 20))
        # Workout selection buttons stored in list and height stored in mutable variable, to allow automatic insertion
        # of as many widgets that are needed.
        self.workout_list = []
        self.workout_button = []
        self.workout_button_height = 40
        # Reads workout list file (simply list of all currently saved workout names) and saves into list.
        with open('Data/Workout List.txt', 'r') as file:
            for line in file:
                self.workout_list.append(line.rstrip())
        # Creates button for each item in workout list, button height variable used to set button height, then increased
        # with each iteration.
        for item in self.workout_list:
            self.workout_button.append(wx.Button(self.panel, label=str(item), pos=(20, self.workout_button_height),
                      size=(150, 40), style=wx.ALIGN_CENTRE_VERTICAL))
            self.workout_button_height += 46
        # Binding each button in list using for loop. All bind to same function, but the button event object later used
        # distinguished which was pressed.
        for item in self.workout_button:
            item.Bind(wx.EVT_BUTTON, self.workout_button_pressed)
        # Binding on_close to close button
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def workout_button_pressed(self, e):
        file_data = []
        # Opens the relevant workout file of the button pressed, by taking the button event object and using it to index
        # in button list, and then matching that index location to the workout list to get workout name, same as file name.
        with open(('Data/Saved Workouts/' + str(self.workout_list[self.workout_button.index(e.GetEventObject())]) + '.txt'), 'r') as file:
            # Saving file lines in list, stripping whitespace and | on end (used to delimit lists and auto placed at end)
            for line in file:
                file_data.append(line.rstrip().rstrip('|'))
        exercise_list = []
        exercise_lengths = []
        rest_lengths = []
        # Iterating through all 3 lines for exercise and both lengths, splitting lines by | (used to delimit when saving),
        # and storing data in lists.
        for a, b, c in zip(file_data[3].split('|'), file_data[4].split('|'), file_data[5].split('|')):
            exercise_list.append(a)
            exercise_lengths.append(b)
            rest_lengths.append(c)
        # Assigning all data to workout class to store. workout class registered to mainframe as this frame closes.
        MainFrame.workout = Workout(title=file_data[0].rstrip(), mode=file_data[1].rstrip(), repeats=file_data[2].rstrip(),
                               exercise_list=exercise_list, exercise_lengths=exercise_lengths, rest_lengths=rest_lengths)
        # Creating timer frame and closing choice frame.
        frames_dictionary['timer_frame'] = TimerFrame('Workout Timer')
        frames_dictionary['timer_frame'].Show()
        self.on_close(None)

    def on_close(self, e):
        # On close function, re-activates button to open the window
        # When closed by choosing workout button, none type passed into e, so button not reactivated.
        if e is not None:
            frames_dictionary['main_frame'].enable_buttons()
        self.Destroy()


class TimerFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(612, 612))
        self.panel = wx.Panel(self)
        self.Centre()
        # Binding close event to On Close function
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # Defining variables. Master counter and list used to store and use workout data. Skip and go are used during
        # pausing/skipping time.
        self.master_counter = 0
        self.master_list = []
        self.go = True
        self.skip = False
        # Creating widgets: text with exercise labels and countdown for timer, pause, play, and forward/back skip buttons.
        # Countdown and exercise label text are made width of window and aligned centre, to more easily align the two
        # and allow for long exercise labels in correct format.
        self.start_button = wx.Button(self.panel, label='Start Workout', pos=(225, 220), size=(150, 40), style=wx.ALIGN_CENTRE_VERTICAL)
        self.pause_button = wx.Button(self.panel, label='Pause', pos=(215, 360), size=(70, 30),
                                      style=wx.ALIGN_CENTRE_VERTICAL)
        self.play_button = wx.Button(self.panel, label='Play', pos=(315, 360), size=(70, 30),
                                     style=wx.ALIGN_CENTRE_VERTICAL)
        self.forward_button = wx.Button(self.panel, label='Forward 5s', pos=(415, 360), size=(70, 30),
                                     style=wx.ALIGN_CENTRE_VERTICAL)
        self.back_button = wx.Button(self.panel, label='Back 5s', pos=(115, 360), size=(70, 30),
                                     style=wx.ALIGN_CENTRE_VERTICAL)
        self.countdown_text = wx.StaticText(self.panel, label='', pos=(0, 100), size=(600, 50), style=wx.ALIGN_CENTRE)
        self.counter_text = wx.StaticText(self.panel, label='', pos=(0, 230), size=(600, 50), style=wx.ALIGN_CENTRE)
        self.exercise_label = wx.StaticText(self.panel, label='', pos=(0, 140), size=(600, 50), style=wx.ALIGN_CENTRE)
        self.next_exercise = wx.StaticText(self.panel, label='', pos=(0, 320), size=(600, 20), style=wx.ALIGN_CENTRE)
        # Setting larger fonts for timer and exercise label
        font_1 = wx.Font(48, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_2 = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.counter_text.SetFont(font_1)
        self.exercise_label.SetFont(font_1)
        self.next_exercise.SetFont(font_2)
        # Binding buttons
        self.start_button.Bind(wx.EVT_BUTTON, self.start_button_pressed)
        self.play_button.Bind(wx.EVT_BUTTON, self.play_button_pressed)
        self.pause_button.Bind(wx.EVT_BUTTON, self.pause_button_pressed)
        self.forward_button.Bind(wx.EVT_BUTTON, self.forward_button_pressed)
        self.back_button.Bind(wx.EVT_BUTTON, self.back_button_pressed)
        # Hiding all widgets except start button and label-less text. Shown after starting button pressed and 5s countdown.
        self.forward_button.Hide()
        self.back_button.Hide()
        self.pause_button.Hide()
        self.play_button.Hide()
        self.counter_text.Hide()

    def pause_button_pressed(self, e):
        # Play and pause is determined through go variable, the timer loop is kept in infinite while true loop doing
        # nothing while go is False.
        self.go = False

    def play_button_pressed(self, e):
        self.go = True

    def forward_button_pressed(self, e):
        # Forward and back buttons use skip variable, if true, this auto ends any 1s sleep, allowing the time skip to
        # happen immediately. If statement prevents skipping past end of workout. 4s are skipped as it looks smoother
        # like this, not sure why.
        self.skip = True
        if (self.master_counter + 4) > len(self.master_list):
            self.master_counter = len(self.master_list)
        else:
            self.master_counter += 4

    def back_button_pressed(self, e):
        # If statement prevents skipping past start of workout. 6s are skipped as it looks smoother like this, not sure why.
        self.skip = True
        if self.master_counter < 6:
            self.master_counter = 0
        else:
            self.master_counter -= 6

    def sleep(self, duration, start_time, get_now=time.perf_counter):
        # A sleep function to replace built in one, as it is much more accurate like this. Takes initial start time
        # as argument to allow any calculations within main code block to be done during the wait time and not on top of
        # it, theoretically making it more accurate. Skip is reset to false to prevent extra seconds being skipped.
        now = start_time
        end = now + duration
        self.skip = False
        # Skip turned to false will auto end any waiting. While loop ends when duration is passed.
        while now < end:
            if self.skip is True:
                return
            now = get_now()

    def start_button_pressed(self, e):
        # Begin main timer function as thread, seemed simpler this way rather than binding a thread directly to a button.
        # Threading used to allow other inputs such as pause and skip to be taken without the entire CPU freezing during
        # 1s sleep or during perpetual while loop when paused. All relevant workout data is fed into this function.
        self.start_button.Hide()
        self.thread_timer = th.Thread(target=self.timer_thread, args=(MainFrame.workout.exercise_list, MainFrame.workout.exercise_lengths, MainFrame.workout.rest_lengths, MainFrame.workout.repeats))
        self.thread_timer.start()

    def timer_thread(self, exercise_list, exercise_lengths, rest_lengths, repeats):
        # Main timer thread, starts with 5s countdown before workout begins. Note time taken at start of loop,
        # and code executed in between to increase accuracy theoretically. Yield function force updates the widgets,
        # without it there is a noticeable and uneven delay, used in every 1s loop now.
        self.counter_text.Show()
        for item in [5, 4, 3, 2, 1]:
            time_start = (time.perf_counter())
            self.counter_text.SetLabelText(str(item))
            wx.Yield()
            self.sleep(1, time_start)
        # Showing buttons and exercise label
        self.play_button.Show()
        self.pause_button.Show()
        self.forward_button.Show()
        self.back_button.Show()
        self.exercise_label.Show()
        wx.Yield()
        # Creating master list consisting of tuples of (the exercise/rest label, and the time to be shown on counter), for
        # every second in the workout, start to finish. Done this way to allow skipping to happen easily with just
        # increasing a master counter, with all data on one linear track that can be followed alongside the master counter.
        # Last rest length is saved so the final rest can be reomved from the list.
        for a, b, c in zip(exercise_list, exercise_lengths, rest_lengths):
            for item in range(int(b)):
                self.master_list.append((a, (int(b)-item)))
            for item in range(int(c)):
                self.master_list.append(('Rest', (int(c)-item)))
            last_rest = int(c)
        # Multiplying master list by number of repeats for workout.
        master_list_count = self.master_list
        for item in range(int(repeats)):
            if item == 0:
                continue
            self.master_list = self.master_list + master_list_count
        # Deleting last rest, by slicing off last elements, calculated by taking the last rest length.
        del self.master_list[(len(self.master_list) - last_rest):]
        # Main workout timer loop. 'While true' loop allows CPU to constantly stay within loop while paused, and can only
        # be broken by the master counter reaching the end of the workout. Second while loop contains sleep function and
        # is stopped by pause making go variable false, and master counter reaching the end. While loop with master
        # counter used instead of for loop going through the master list, as this allows the position of the counter to be
        # manipulated with skips, not possible with for loop. Counter and labels updated with the data from the tuple in
        # master list, using master counter to 'iterate' through it.
        while True:
            while self.go is True and self.master_counter < len(self.master_list):
                time_start = (time.perf_counter())
                self.counter_text.SetLabelText(str((self.master_list[self.master_counter])[1]))
                self.exercise_label.SetLabelText(str((self.master_list[self.master_counter])[0]))
                # Next exercise is shown on rests, calculated by taking the exercise label in list from the position of
                # the current counter plus the length remaining of current exercise. If statement prevents this on the
                # last exercise, instead setting it to Rest so the label will be set to blank. If next exercise is rest,
                # it is instead set to blank.
                if (self.master_counter + (self.master_list[self.master_counter])[1]) < len(self.master_list):
                    next_exercise = (str((self.master_list[
                        (self.master_counter + (self.master_list[self.master_counter])[1])])[0]))
                else:
                    next_exercise = 'Rest'
                if next_exercise != 'Rest':
                    self.next_exercise.SetLabelText('Next up: ' + next_exercise)
                else:
                    self.next_exercise.SetLabelText('')
                wx.Yield()
                self.master_counter += 1
                self.sleep(1, time_start)
            if self.master_counter == len(self.master_list):
                break
        # Workout finished text
        self.exercise_label.SetLabelText('Finished!')
        self.counter_text.Hide()
        wx.Yield()

    def on_close(self, e):
        frames_dictionary['main_frame'].enable_buttons()
        self.Destroy()


class CreateWorkoutFrame(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(600, 650))
        self.panel = wx.Panel(self)
        self.Centre()
        # Binding close event to On Close function
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # Defining Starting Widgets
        self.workout_name_static = wx.StaticText(self.panel, label='Workout Name:', pos=(20, 20))
        self.workout_name_ctrl = wx.TextCtrl(self.panel, value='', pos=(108, 17))
        self.basic_button = wx.RadioButton(self.panel, label='Basic', pos=(20, 50))
        self.basic_button.SetValue(True)
        self.advanced_button = wx.RadioButton(self.panel, label='Advanced', pos=(80, 50))
        # Basic Mode widgets, static texts and ctrls for exercise length, rest length, workout repeats
        self.exercise_length_static = wx.StaticText(self.panel, label='Exercise Length (s):', pos=(20, 80))
        self.exercise_length_ctrl = wx.TextCtrl(self.panel, value='', pos=(125, 77), size=(22, 22))
        self.rest_length_static = wx.StaticText(self.panel, label='Rest Length (s):', pos=(20, 110))
        self.rest_length_ctrl = wx.TextCtrl(self.panel, value='', pos=(105, 107), size=(22, 22))
        self.workout_repeats_static = wx.StaticText(self.panel, label='Number of Workout Repeats:', pos=(20, 140))
        self.workout_repeats_ctrl = wx.TextCtrl(self.panel, value='', pos=(178, 137), size=(22, 22))
        self.basic_line = wx.StaticLine(self.panel, pos=(10, 170), size=(226, 1))
        # Basic Add/Remove exercise buttons, remove is disabled at start due to minimum 1 exercises
        self.add_exercise_button = wx.Button(self.panel, label='Add Exercise', pos=(20, 210),
                                             size=(90, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        self.remove_exercise_button = wx.Button(self.panel, label='Remove Exercise', pos=(115, 210),
                                                size=(110, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        self.remove_exercise_button.Disable()
        # Basic Exercise widgets and heights saved in mutable variables
        self.exercise_text_static = [wx.StaticText(self.panel, label='Exercise 1:', pos=(20, 180))]
        self.exercise_text_ctrl = [(wx.TextCtrl(self.panel, value='', pos=(90, 177)))]
        self.exercise_height = 180
        # Advanced Mode widgets,
        self.adv_workout_repeats_static = wx.StaticText(self.panel, label='Number of Workout Repeats:', pos=(20, 80))
        self.adv_workout_repeats_ctrl = wx.TextCtrl(self.panel, value='', pos=(178, 77), size=(22, 22))
        # Advanced Exercise widgets and heights saved in mutable variables
        self.adv_exercise_text_static = [wx.StaticText(self.panel, label='Exercise 1:', pos=(20, 120))]
        self.adv_exercise_text_ctrl = [(wx.TextCtrl(self.panel, value='', pos=(90, 117)))]
        self.adv_exercise_length_static = [wx.StaticText(self.panel, label='Exercise Length (s):', pos=(210, 120))]
        self.adv_exercise_length_ctrl = [wx.TextCtrl(self.panel, value='', pos=(316, 117), size=(22, 22))]
        self.adv_rest_length_static = [wx.StaticText(self.panel, label='Rest Length (s):', pos=(356, 120))]
        self.adv_rest_length_ctrl = [wx.TextCtrl(self.panel, value='', pos=(442, 117), size=(22, 22))]
        self.adv_add_exercise_button = wx.Button(self.panel, label='Add Exercise', pos=(20, 150),
                                             size=(90, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        self.adv_remove_exercise_button = wx.Button(self.panel, label='Remove Exercise', pos=(115, 150),
                                                size=(110, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        self.advanced_line = wx.StaticLine(self.panel, pos=(10, 110), size=(464, 1))
        self.adv_remove_exercise_button.Disable()
        self.adv_exercise_height = 120
        # Hiding all Advanced Mode Widgets
        self.adv_workout_repeats_static.Hide()
        self.adv_workout_repeats_ctrl.Hide()
        self.adv_add_exercise_button.Hide()
        self.adv_remove_exercise_button.Hide()
        self.advanced_line.Hide()
        for item in self.adv_exercise_text_static:
            item.Hide()
        for item in self.adv_exercise_text_ctrl:
            item.Hide()
        for item in self.adv_exercise_length_static:
            item.Hide()
        for item in self.adv_exercise_length_ctrl:
            item.Hide()
        for item in self.adv_rest_length_static:
            item.Hide()
        for item in self.adv_rest_length_ctrl:
            item.Hide()
        # Save button
        self.save_workout_button = wx.Button(self.panel, label='Save Workout', pos=(20, 570),
                                            size=(90, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        # Button binding
        self.add_exercise_button.Bind(wx.EVT_BUTTON, self.add_exercise_button_pressed)
        self.remove_exercise_button.Bind(wx.EVT_BUTTON, self.remove_exercise_button_pressed)
        self.adv_add_exercise_button.Bind(wx.EVT_BUTTON, self.adv_add_exercise_button_pressed)
        self.adv_remove_exercise_button.Bind(wx.EVT_BUTTON, self.adv_remove_exercise_button_pressed)
        self.basic_button.Bind(wx.EVT_RADIOBUTTON, self.basic_button_pressed)
        self.advanced_button.Bind(wx.EVT_RADIOBUTTON, self.advanced_button_pressed)
        self.save_workout_button.Bind(wx.EVT_BUTTON, self.save_workout_button_pressed)

    def add_exercise_button_pressed(self, e):
        # Increase height of all new exercise-name widgets to lower them
        self.exercise_height += 30
        # Creating new text and text ctrl widgets
        self.exercise_text_static.append(wx.StaticText(self.panel, label=('Exercise ' + str(len(self.exercise_text_static)+1) + ':'),
                                                       pos=(20, self.exercise_height)))
        self.exercise_text_ctrl.append(wx.TextCtrl(self.panel, value='', pos=(90, (self.exercise_height-3))))
        # Lowering button widgets
        self.add_exercise_button.SetPosition((20, (self.exercise_height+30)))
        self.remove_exercise_button.SetPosition((115, (self.exercise_height+30)))
        # Showing remove button, starts hidden
        self.remove_exercise_button.Enable()
        # Maximum 12 exercises, enforced by hiding add button
        if len(self.exercise_text_static) == 12:
            self.add_exercise_button.Disable()

    def remove_exercise_button_pressed(self, e):
        # Destroy and delete exercise widgets from lists
        (self.exercise_text_static[(len(self.exercise_text_static)-1)]).Destroy()
        del (self.exercise_text_static[(len(self.exercise_text_static) - 1)])
        (self.exercise_text_ctrl[(len(self.exercise_text_ctrl) - 1)]).Destroy()
        del (self.exercise_text_ctrl[(len(self.exercise_text_ctrl) - 1)])
        # Decrease height of all new exercise-name widgets to raise them
        self.exercise_height -= 30
        # Raising button widgets
        self.add_exercise_button.SetPosition((20, (self.exercise_height + 30)))
        self.remove_exercise_button.SetPosition((115, (self.exercise_height + 30)))
        # Show exercise button in case hidden by maxing out exercises
        self.add_exercise_button.Enable()
        # Setting minimum exercise number at 1, enforced by hiding remove button
        if len(self.exercise_text_static) == 1:
            self.remove_exercise_button.Disable()

    def adv_add_exercise_button_pressed(self, e):
        # Increase height of all new exercise widgets to lower them
        self.adv_exercise_height += 30
        # Creating new exercise widgets
        self.adv_exercise_text_static.append(
            wx.StaticText(self.panel, label=('Exercise ' + str(len(self.adv_exercise_text_static) + 1) + ':'),
                          pos=(20, self.adv_exercise_height)))
        self.adv_exercise_text_ctrl.append(wx.TextCtrl(self.panel, value='', pos=(90, (self.adv_exercise_height - 3))))
        self.adv_exercise_length_static.append(wx.StaticText(self.panel, label='Exercise Length (s):',
                                                             pos=(210, self.adv_exercise_height)))
        self.adv_exercise_length_ctrl.append(wx.TextCtrl(self.panel, value='',
                                                         pos=(316, (self.adv_exercise_height - 3)), size=(22, 22)))
        self.adv_rest_length_static.append(wx.StaticText(self.panel, label='Rest Length (s):',
                                                         pos=(356, self.adv_exercise_height)))
        self.adv_rest_length_ctrl.append(wx.TextCtrl(self.panel, value='', pos=(442, (self.adv_exercise_height - 3)),
                                                     size=(22, 22)))
        # Lowering button widgets
        self.adv_add_exercise_button.SetPosition((20, (self.adv_exercise_height + 30)))
        self.adv_remove_exercise_button.SetPosition((115, (self.adv_exercise_height + 30)))
        # Showing remove button, starts hidden
        self.adv_remove_exercise_button.Enable()
        # Maximum 12 exercises, enforced by hiding add button
        if len(self.adv_exercise_text_static) == 12:
            self.adv_add_exercise_button.Disable()

    def adv_remove_exercise_button_pressed(self, e):
        # Destroy and delete exercise widgets from lists
        self.adv_exercise_text_static[(len(self.adv_exercise_text_static) - 1)].Destroy()
        del self.adv_exercise_text_static[(len(self.adv_exercise_text_static) - 1)]
        (self.adv_exercise_text_ctrl[(len(self.adv_exercise_text_ctrl) - 1)]).Destroy()
        del (self.adv_exercise_text_ctrl[(len(self.adv_exercise_text_ctrl) - 1)])
        (self.adv_exercise_length_static[(len(self.adv_exercise_length_static) - 1)]).Destroy()
        del (self.adv_exercise_length_static[(len(self.adv_exercise_length_static) - 1)])
        (self.adv_exercise_length_ctrl[(len(self.adv_exercise_length_ctrl) - 1)]).Destroy()
        del (self.adv_exercise_length_ctrl[(len(self.adv_exercise_length_ctrl) - 1)])
        (self.adv_rest_length_static[(len(self.adv_rest_length_static) - 1)]).Destroy()
        del (self.adv_rest_length_static[(len(self.adv_rest_length_static) - 1)])
        (self.adv_rest_length_ctrl[(len(self.adv_rest_length_ctrl) - 1)]).Destroy()
        del (self.adv_rest_length_ctrl[(len(self.adv_rest_length_ctrl) - 1)])
        # Decrease height of all new exercise-name widgets to raise them
        self.adv_exercise_height -= 30
        # Raising button widgets
        self.adv_add_exercise_button.SetPosition((20, (self.adv_exercise_height + 30)))
        self.adv_remove_exercise_button.SetPosition((115, (self.adv_exercise_height + 30)))
        # Show exercise button in case hidden by maxing out exercises
        self.adv_add_exercise_button.Enable()
        # Setting minimum exercise number at 1, enforced by hiding remove button
        if len(self.adv_exercise_text_static) == 1:
            self.adv_remove_exercise_button.Disable()

    def advanced_button_pressed(self, e):
        # Hiding all Basic Mode Widgets
        self.exercise_length_static.Hide()
        self.exercise_length_ctrl.Hide()
        self.rest_length_static.Hide()
        self.rest_length_ctrl.Hide()
        self.workout_repeats_static.Hide()
        self.workout_repeats_ctrl.Hide()
        self.basic_line.Hide()
        self.add_exercise_button.Hide()
        self.remove_exercise_button.Hide()
        for item in self.exercise_text_static:
            item.Hide()
        for item in self.exercise_text_ctrl:
            item.Hide()
        # Showing all Advanced Mode widgets
        self.adv_workout_repeats_static.Show()
        self.adv_workout_repeats_ctrl.Show()
        self.adv_add_exercise_button.Show()
        self.adv_remove_exercise_button.Show()
        self.advanced_line.Show()
        for item in self.adv_exercise_text_static:
            item.Show()
        for item in self.adv_exercise_text_ctrl:
            item.Show()
        for item in self.adv_exercise_length_static:
            item.Show()
        for item in self.adv_exercise_length_ctrl:
            item.Show()
        for item in self.adv_rest_length_static:
            item.Show()
        for item in self.adv_rest_length_ctrl:
            item.Show()

    def basic_button_pressed(self, e):
        # Showing all Basic Mode Widgets
        self.exercise_length_static.Show()
        self.exercise_length_ctrl.Show()
        self.rest_length_static.Show()
        self.rest_length_ctrl.Show()
        self.workout_repeats_static.Show()
        self.workout_repeats_ctrl.Show()
        self.basic_line.Show()
        self.add_exercise_button.Show()
        self.remove_exercise_button.Show()
        for item in self.exercise_text_static:
            item.Show()
        for item in self.exercise_text_ctrl:
            item.Show()
        # Hiding all Advanced Mode widgets
        self.adv_workout_repeats_static.Hide()
        self.adv_workout_repeats_ctrl.Hide()
        self.adv_add_exercise_button.Hide()
        self.adv_remove_exercise_button.Hide()
        self.advanced_line.Hide()
        for item in self.adv_exercise_text_static:
            item.Hide()
        for item in self.adv_exercise_text_ctrl:
            item.Hide()
        for item in self.adv_exercise_length_static:
            item.Hide()
        for item in self.adv_exercise_length_ctrl:
            item.Hide()
        for item in self.adv_rest_length_static:
            item.Hide()
        for item in self.adv_rest_length_ctrl:
            item.Hide()

    def on_close(self, e):
        # On close function, re-activates button to open the window
        frames_dictionary['main_frame'].enable_buttons()
        self.Destroy()

    def save_workout_button_pressed(self, e):
        # Defining variables used to store saved data.
        exercise_list = []
        exercise_lengths = []
        rest_lengths = []
        saved_workouts = []
        saved_workouts_string = ''
        # Saves different data for basic/advanced mode
        # Basic Mode saving:
        if self.basic_button.GetValue() is True:
            for item in self.exercise_text_ctrl:
                # Continue statement to avoid saving blank lines
                if item.GetLineText(0) == '':
                    continue
                # Transferring inputs from ctrls into lists to save, length/times are static across all exercises
                exercise_list.append(item.GetLineText(0))
                exercise_lengths.append(self.exercise_length_ctrl.GetLineText(0))
                rest_lengths.append(self.rest_length_ctrl.GetLineText(0))
            mode = 'basic'
            repeats = self.workout_repeats_ctrl.GetLineText(0)
        # Advanced Mode saving
        else:
            # Transferring ctrl inputs to lists (adv mode), looping through 3 at once
            for a, b, c in zip(self.adv_exercise_text_ctrl, self.adv_exercise_length_ctrl, self.adv_rest_length_ctrl):
                # Continue statement to avoid saving blank/incomplete lines
                if a.GetLineText(0) == '' or b.GetLineText(0) == '' or c.GetLineText(0) == '':
                    continue
                exercise_list.append(a.GetLineText(0))
                exercise_lengths.append(b.GetLineText(0))
                rest_lengths.append(c.GetLineText(0))
            mode = 'advanced'
            repeats = self.adv_workout_repeats_ctrl.GetLineText(0)
        # Saving workout data into workout class variable
        MainFrame.new_workout = Workout(title=self.workout_name_ctrl.GetLineText(0), mode=mode,
                              repeats=repeats,
                              exercise_list=exercise_list, exercise_lengths=exercise_lengths, rest_lengths=rest_lengths)
        # Updating saved 'workout list' file, open, parse into list, append, sort, re-save
        with open('Data/Workout List.txt', 'r') as workout_list_r:
            for line in workout_list_r:
                saved_workouts.append(line.rstrip())
            # If statement splits function into create workout and edit workout frames
            if type(self) == CreateWorkoutFrame:
                # Checking for existing workout with same name, if not then continue. Else statement brings up overwrite screen
                if MainFrame.new_workout.title not in saved_workouts:
                    saved_workouts.append(MainFrame.new_workout.title)
                    saved_workouts.sort()
                    for item in saved_workouts:
                        saved_workouts_string += (item + '\n')
                    with open('Data/Workout List.txt', 'w') as workout_list_w:
                        workout_list_w.write(saved_workouts_string)
                    # Saving data into txt file, titled with the workout name + .txt
                    with open(('Data/Saved Workouts/' + (MainFrame.new_workout.title + '.txt')), 'w') as file:
                        file.write(str(MainFrame.new_workout))
                    # Closing the frame when saved.
                    self.on_close(None)
                # Overwrite workout screen if workout already in list
                else:
                    frames_dictionary['overwrite_workout'] = OverwriteWorkout('')
                    frames_dictionary['overwrite_workout'].Show()
            # Else statement only triggers if saved in edit workout frame, no overwrite screen
            else:
                # workout saved immediately, no need to check for overwrite
                with open(('Data/Saved Workouts/' + (MainFrame.new_workout.title + '.txt')), 'w') as file:
                    file.write(str(MainFrame.new_workout))
                # checking for workout name change. If new workout name is not in saved list, adding new name, removing
                # old name, resaving the list, and removing the old file.
                if MainFrame.new_workout.title not in saved_workouts:
                    saved_workouts.append(MainFrame.new_workout.title)
                    saved_workouts.remove(MainFrame.workout.title)
                    saved_workouts.sort()
                    for item in saved_workouts:
                        saved_workouts_string += (item + '\n')
                    with open('Data/Workout List.txt', 'w') as workout_list_w:
                        workout_list_w.write(saved_workouts_string)
                    os.remove(('Data/Saved Workouts/' + MainFrame.workout.title + '.txt'))
                self.on_close(None)


class OverwriteWorkout(wx.Frame):
    def __init__(self, title):
        super().__init__(parent=None, title=title, size=(250, 120))
        self.panel = wx.Panel(self)
        self.Centre()
        # Overwrite message frame, yes and no buttons.
        self.static_text = wx.StaticText(self.panel, label='Workout already exists, overwrite?', pos=(28, 20))
        self.yes_button = wx.Button(self.panel, label='Yes', pos=(55, 40), size=(32, 24),
                                               style=wx.ALIGN_CENTRE_VERTICAL)
        self.no_button = wx.Button(self.panel, label='No', pos=(145, 40), size=(32, 24),
                                    style=wx.ALIGN_CENTRE_VERTICAL)
        self.no_button.Bind(wx.EVT_BUTTON, self.no_button_pressed)
        self.yes_button.Bind(wx.EVT_BUTTON, self.yes_button_pressed)

    # Yes button overwrites existing file, then closes the window plus create/edit workout frame.
    def yes_button_pressed(self, e):
        with open(
                ('Data/Saved Workouts/' + (MainFrame.new_workout.title + '.txt')), 'w') as file:
            file.write(str(MainFrame.new_workout))
        frames_dictionary['create_workout_frame'].on_close(None)
        self.Close()

    # No button only closes the frame.
    def no_button_pressed(self, e):
        self.Close()


class ChooseWorkoutFrameEdit(ChooseWorkoutFrame):
    def __init__(self, title):
        super().__init__(title)

    def workout_button_pressed(self, e):
        file_data = []
        # Opens the relevant workout file of the button pressed, by taking the button event object and using it to index
        # in button list, and then matching that index location to the workout list to get workout name, same as file name.
        with open(('Data/Saved Workouts/' + str(self.workout_list[self.workout_button.index(e.GetEventObject())]) + '.txt'), 'r') as file:
            # Saving file lines in list, stripping whitespace and | on end (used to delimit lists and auto placed at end)
            for line in file:
                file_data.append(line.rstrip().rstrip('|'))
        exercise_list = []
        exercise_lengths = []
        rest_lengths = []
        # Iterating through all 3 lines for exercise and both lengths, splitting lines by | (used to delimit when saving),
        # and storing data in lists.
        for a, b, c in zip(file_data[3].split('|'), file_data[4].split('|'), file_data[5].split('|')):
            exercise_list.append(a)
            exercise_lengths.append(b)
            rest_lengths.append(c)
        # Assigning all data to workout class to store. workout class registered to mainframe as this frame closes.
        MainFrame.workout = Workout(title=file_data[0].rstrip(), mode=file_data[1].rstrip(), repeats=file_data[2].rstrip(),
                               exercise_list=exercise_list, exercise_lengths=exercise_lengths, rest_lengths=rest_lengths)
        # Creating edit workout frame and closing choice frame.
        frames_dictionary['edit_workout_frame'] = EditWorkoutFrame('Edit Workout')
        frames_dictionary['edit_workout_frame'].Show()
        self.on_close(None)


class EditWorkoutFrame(CreateWorkoutFrame):
    # Edit workout frame inherits features from create workout frame, then fills all widgets with the info saved in the
    # txt file.
    def __init__(self, title):
        super().__init__(title)
        # Fills out widgets for advanced mode workouts. Switches to advanced mode using method and changes the radiobutton
        # to reflect this.
        if MainFrame.workout.mode == 'advanced':
            self.advanced_button_pressed(None)
            self.advanced_button.SetValue(True)
            self.workout_name_ctrl.SetLabelText(MainFrame.workout.title)
            self.adv_workout_repeats_ctrl.SetLabelText(MainFrame.workout.repeats)
            # Filling out widgets. a, b, c all lists of exercises/lengths, d used as a counter to allow the info to be
            # put into the right position in the lines.
            for a, b, c, d in zip(MainFrame.workout.exercise_list, MainFrame.workout.exercise_lengths,
                                  MainFrame.workout.rest_lengths, range(len(MainFrame.workout.exercise_list))):
                self.adv_exercise_text_ctrl[d].SetLabelText(str(a))
                self.adv_exercise_length_ctrl[d].SetLabelText(str(b))
                self.adv_rest_length_ctrl[d].SetLabelText(str(c))
                # Adds new exercise line for each item, except the final item on the list.
                if (d + 1) < len(MainFrame.workout.exercise_list):
                    self.adv_add_exercise_button_pressed(None)
        # Fills out widgets in basic mode.
        if MainFrame.workout.mode == 'basic':
            self.workout_name_ctrl.SetLabelText(MainFrame.workout.title)
            self.workout_repeats_ctrl.SetLabelText(MainFrame.workout.repeats)
            # Exercise and rest lengths are all the same, so no need to iterate.
            self.exercise_length_ctrl.SetLabelText(MainFrame.workout.exercise_lengths[0])
            self.rest_length_ctrl.SetLabelText(MainFrame.workout.rest_lengths[0])
            # a is saved info, b is used as counter to select correct widgets.
            for a, b in zip(MainFrame.workout.exercise_list, range(len(MainFrame.workout.exercise_list))):
                self.exercise_text_ctrl[b].SetLabelText(str(a))
                if (b + 1) < len(MainFrame.workout.exercise_list):
                    self.add_exercise_button_pressed(None)
        # Delete workout button
        self.delete_workout_button = wx.Button(self.panel, label='Delete Workout', pos=(460, 570),
                                             size=(105, 24), style=wx.ALIGN_CENTRE_VERTICAL)
        self.delete_workout_button.Bind(wx.EVT_BUTTON, self.delete_workout_button_pressed)

    def delete_workout_button_pressed(self, e):
        os.remove(('Data/Saved Workouts/' + MainFrame.workout.title + '.txt'))
        saved_workouts = []
        saved_workouts_string = ''
        with open('Data/Workout List.txt', 'r') as workout_list_r:
            for line in workout_list_r:
                saved_workouts.append(line.rstrip())
        saved_workouts.remove(MainFrame.workout.title)
        for item in saved_workouts:
            saved_workouts_string += (item + '\n')
        with open('Data/Workout List.txt', 'w') as workout_list_w:
            workout_list_w.write(saved_workouts_string)
        self.on_close(None)

    def on_close(self, e):
        # On close function, re-activates button to open the window
        frames_dictionary['main_frame'].enable_buttons()
        self.Destroy()


class Workout:
    # Workout class used as data structure to store all workout data.
    def __init__(self, title, mode, repeats, exercise_list, exercise_lengths, rest_lengths):
        self.title = title
        self.mode = mode
        self.repeats = repeats
        self.exercise_list = exercise_list
        self.exercise_lengths = exercise_lengths
        self.rest_lengths = rest_lengths

    def __str__(self):
        # Defining str method, stored in this way in txt file, delimited by | in lists
        exercise_list_string = ''
        exercise_lengths_string = ''
        rest_lengths_string = ''
        for a, b, c in zip(self.exercise_list, self.exercise_lengths, self.rest_lengths):
            exercise_list_string += a + '|'
            exercise_lengths_string += b + '|'
            rest_lengths_string += c + '|'
        return (self.title + '\n' + self.mode + '\n' + self.repeats + '\n' + exercise_list_string + '\n' +
                exercise_lengths_string + '\n' + rest_lengths_string)


frames_dictionary['main_frame'] = MainFrame('Workout Timer')
frames_dictionary['main_frame'].Show()

testapp.MainLoop()
