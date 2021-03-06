import curses
import queue
import textwrap


class Interface:
    def __init__(self, start_screen, *args):
        self.stdscr = curses.initscr()

        curses.start_color()

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.screen_stack = [start_screen(self, *args)]
        self.closed = False

    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        self.closed = True

    def main(self):
        while not self.closed:
            self.stdscr.clear()
            self.stdscr.move(0, 0)
            self.screen_stack[-1].render(self.stdscr)
            self.stdscr.move(self.stdscr.getmaxyx()[
                             0] - 1, self.stdscr.getmaxyx()[1] - 1)
            self.stdscr.refresh()

            self.screen_stack[-1].handle_key(self.stdscr.get_wch())

    def main_wrapped(self, window: curses.window):
        self.stdscr = window
        self.main()

    def go_back(self):
        if len(self.screen_stack) > 1:
            self.screen_stack.pop(-1)
        else:
            self.close()

    def go_to_screen(self, screen):
        self.screen_stack.append(screen)


class InterfaceScreen:
    def __init__(self, interface):
        self.interface = interface
        pass

    def render(self, window: curses.window):
        pass

    def handle_key(self, key):
        if key == 'q':
            self.interface.close()
        elif key == curses.KEY_LEFT:
            self.interface.go_back()

    def choice_render(self, window, index, selected, options=0):
        title = self.title if hasattr(
            self, 'title') else type(choice).__name__
        window.addstr(index, 0, title,
                      (curses.A_REVERSE if selected == index else 0) | options)


class ChoiceScreen(InterfaceScreen):
    def __init__(self, interface, choices: list):
        self.choices = choices
        self.selected = 0
        super().__init__(interface)

    def render(self, window: curses.window):
        for i, choice in enumerate(self.choices):
            choice.choice_render(window, i, self.selected, 0)

    def handle_key(self, key):
        super().handle_key(key)

        if key == curses.KEY_DOWN:
            if self.selected < len(self.choices) - 1:
                self.selected += 1
            else:
                self.selected = 0
        elif key == curses.KEY_UP:
            if self.selected != 0:
                self.selected -= 1
            else:
                self.selected = len(self.choices) - 1

        elif key == '\n' or key == curses.KEY_RIGHT:
            self.interface.go_to_screen(self.choices[self.selected])


class ScrollScreen(InterfaceScreen):
    def __init__(self, interface, text=""):
        self.text = text
        self.top_line = 0
        super().__init__(interface)

    def render(self, window):
        text = textwrap.fill(self.text.replace('\n', '\x00'), self.interface.stdscr.getmaxyx()[
                             1]-1).replace('   ', '\n').replace('\x00', '\n')

        text = '\n'.join(text.split('\n')[self.top_line:
                                          self.top_line+self.interface.stdscr.getmaxyx()[0]])

        window.addstr(0, 0, text)

    def handle_key(self, key):
        if key == curses.KEY_DOWN:
            self.top_line += 1
            self.top_line %= len(self.text.split('\n'))
        elif key == curses.KEY_UP:
            self.top_line -= 1
            if self.top_line < 0:
                self.top_line = len(self.text.split('\n'))
        super().handle_key(key)
