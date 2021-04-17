import iface_lib
import scraping

import curses
import json
import time


class LoginScreen(iface_lib.InterfaceScreen):
    def __init__(self, interface):
        super().__init__(interface)
        self.email_input = ""
        self.password_input = ""
        self.selected = 0
        self.failed_login = False
        self.logged_in = False

    def render(self, window):
        window.addstr(0, 0, f"Email Adress: {self.email_input}",
                      curses.A_REVERSE if self.selected == 0 else 0)
        window.addstr(1, 0, f"Password: {'*' * len(self.password_input)}",
                      curses.A_REVERSE if self.selected == 1 else 0)
        window.addstr(2, 0, "Login",
                      curses.A_REVERSE if self.selected == 2 else 0)

        if self.failed_login:
            window.addstr(4, 0, "Login failed", curses.A_BLINK)

    def handle_key(self, key):
        if key == curses.KEY_DOWN:
            if self.selected < 2:
                self.selected += 1
            else:
                self.selected = 0
        elif key == curses.KEY_UP:
            if self.selected != 0:
                self.selected -= 1
            else:
                self.selected = 2
        elif key == '\x7F':
            if self.selected == 0:
                self.email_input = self.email_input[:-1]
            elif self.selected == 1:
                self.password_input = self.password_input[:-1]
        elif key == '\n' and self.selected == 2:
            if self.logged_in:
                self.interface.driver.logout()
            login_state = self.interface.driver.login(
                self.email_input, self.password_input)
            if login_state == 0:
                self.failed_login = False
                self.interface.go_to_screen(MainScreen(self.interface))
                self.logged_in = True
            elif login_state == 1:
                self.failed_login = True

        elif isinstance(key, str) and self.selected != 2:
            if self.selected == 0:
                self.email_input += key
            elif self.selected == 1:
                self.password_input += key
        
        elif key == 'q' and self.selected == 2:
            self.interface.close()


class MainScreen(iface_lib.ChoiceScreen):
    def __init__(self, interface):
        super().__init__(interface, [VideoconferenceListScreen(
            interface), SubjectListScreen(interface)])


class VideoconferenceListScreen(iface_lib.InterfaceScreen):
    def __init__(self, interface):
        super().__init__(interface)
        self.title = "Videoconferences"
        self.vconfs = self.interface.driver.get_videoconferences()

    def render(self, window):
        for i, vconf in enumerate(self.vconfs):
            window.addstr(i, 0, vconf[1])


class SubjectListScreen(iface_lib.ChoiceScreen):
    def __init__(self, interface):
        self.title = "Subjects"
        self.subjects = None
        super().__init__(interface, [])

    def render(self, window):
        if self.subjects is None:
            self.subjects = self.interface.driver.get_subjects()
            self.choices = [SubjectScreen(
            self.interface, identifier, self.subjects[identifier]) for identifier in self.subjects]
        super().render(window)


class SubjectScreen(iface_lib.ChoiceScreen):
    def __init__(self, interface, identifier, title):
        self.identifier = identifier
        self.title = title
        self.units = None
        super().__init__(interface, [])

    def render(self, window):
        if self.units is None:
            self.units = self.interface.driver.get_units(self.identifier)
            self.choices = [UnitScreen(self.interface, self.identifier, *unit) for unit in self.units]
        super().render(window)


class UnitScreen(iface_lib.InterfaceScreen):
    def __init__(self, interface, subject, identifier, title, done):
        self.title = title
        self.done = done
        self.text = None
        self.subject = subject
        self.identifier = identifier
        super().__init__(interface)

    def render(self, window):
        if self.text is None:
            self.text = self.interface.driver.get_unit(self.subject, self.identifier)
        window.addstr(self.text)
    
    def choice_render(self, window, index, selected, options):
        if not self.done:
            options |= curses.color_pair(1)
        super().choice_render(window, index, selected, options)


class SchuManInterface(iface_lib.Interface):
    def __init__(self):
        super().__init__(LoginScreen)
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

        self.driver = scraping.SchuManDriver()

    def close(self):
        super().close()
        self.driver.driver.quit()


if __name__ == "__main__":
    interface = SchuManInterface()
    curses.wrapper(interface.main_wrapped)
