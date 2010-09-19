from Tkinter import *
import tkFileDialog
import tkSimpleDialog


copyright_msg = "PyDough Poser Exporter - odf 2010"
window_title = "PyDough"

textcolor = '#fffaf0'
entrycolor = '#fffafa'
buttoncolor = '#e0e0f0'
activebuttoncolor = '#e8e8f8'


class ErrorDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, exc_info, title = None):
        self.exc_info = exc_info
        self.details_shown = False
        self.message = self.format_error()
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.text = Label(master, text = self.message,
                          anchor = W, justify = LEFT)
        self.text.pack()
        return self.text

    def buttonbox(self):
        box = Frame(self)

        Button(box, text="Details", command=self.details).pack(
            side=LEFT, padx=5, pady=5)
        Button(box, text="OK", command=self.ok, default=ACTIVE).pack(
            side=RIGHT, padx=5, pady=5)

        self.bind("<Return>", self.ok)

        box.pack()

    def format_error(self):
        import traceback

        (exc_type, exc_val, exc_tb) = self.exc_info

        message = ["%s - %s" % (exc_type.__name__, exc_val)]
        if self.details_shown:
            message.append("")
            message.append("Traceback (innermost last):")
            for entry in traceback.extract_tb(exc_tb):
                message.append('    File "%s", line %s, in %s\n        %s'
                               % entry)
        return "\n".join(message)

    def details(self):
        self.details_shown = not self.details_shown
        self.text.configure(text = self.format_error())


class MessageDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, title = None, message = None):
        self.message = message
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        l = Label(master, text = self.message,
                  anchor = W, justify = LEFT)
        l.pack()
        return l

    def buttonbox(self):
        box = Frame(self)

        Button(box, text="OK", command=self.ok, default=ACTIVE).pack(
            side=RIGHT, padx=5, pady=5)

        self.bind("<Return>", self.ok)

        box.pack()


class PropertyDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, props, title = None):
        self.props_in = props
        self.props_out = None
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def get(self):
        return self.props_out

    def buttonbox(self):
        box = Frame(self, background = textcolor)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE,
                   background = buttoncolor,
                   activebackground = activebuttoncolor)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel,
                   background = buttoncolor,
                   activebackground = activebuttoncolor)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def body(self, master):
        self.configure(background = textcolor)
        master.configure(background = textcolor)
        entries = {}
        row = 0
        for key, val in self.props_in:
            l = Label(master, text = str(key), background = textcolor)
            l.grid(row = row, column = 0, sticky = W)
            e = Entry(master, width = 80, background = entrycolor)
            e.grid(row = row, column = 1)
            e.insert(0, str(val))
            entries[key] = e
            if row == 0:
                focus = e
            row = row + 1
        self.entries = entries
        return focus

    def apply(self):
        props = []
        for key, e in self.entries.items():
            props.append((key, e.get()))
        self.props_out = props


class Main(object):
    def __init__(self, master, worker):
        self.master = master
        self.worker = worker
        self.start_GUI()

    def end(self):
        self.master.destroy()
        
    def start_GUI(self):
        log_file_types = (
            ( "Text files", ".txt" ),
            ( "All files",  "*" ),
            )

        self.saveLogFileDialog = tkFileDialog.SaveAs(self.master,
                                                     filetypes = log_file_types,
                                                     title = "Save log")
        
        f = Frame(self.master, background = textcolor)
        f.pack(fill = 'x', expand = 1)
        l = Label(f, text = copyright_msg, background = textcolor,
                  anchor = W, justify = CENTER)
        l.pack()

        b = Button(self.master, text = "Go", command = self.go,
                   background = buttoncolor,
                   activebackground = activebuttoncolor)
        b.pack(side = 'top', fill = 'both', expand = 1)
        self.go_button = b

        opts = Frame(self.master, background = buttoncolor)
        opts.pack(fill = 'x', expand = 1)

        l = Label(opts, text = "-- (this space for rent) --",
                  background = buttoncolor)
        l.pack(side = 'left', fill = 'x', expand = 1)
        
        textframe = Frame(self.master)
        textframe.pack(fill = 'both', expand = 1)
        self.yscroll = Scrollbar(textframe)
        self.yscroll.pack(side = RIGHT, fill = "y")
        self.output = Text(textframe,
                           yscrollcommand = self.yscroll.set,
                           background = textcolor)
        self.output.pack(fill = 'both')
        self.yscroll.configure(command = self.output.yview)
        
        self.status = Label(self.master, text = "",
                            background = textcolor,
                            anchor = W, justify = LEFT)
        self.status.pack(fill = 'x')

    def show_error(self, where = None):
        ErrorDialog(self.master, sys.exc_info(), title = "Runtime error")

    def save(self):
        import os.path

        default_name = "pydough-log.txt"

        file_name = self.saveLogFileDialog.show(initialfile = default_name)
        if not file_name:
            return

        try:
            file = open(file_name, "w")
        except:
            self.show_error("Cannot open '%s'" % file_name)
        else:
            try:
                file.write(self.output.get("1.0", END))
                file.close()
            except:
                file.close()
                self.show_error("Cannot write file '%s'" % file_name)
            else:
                self.status.configure(text = "Output saved")

    def go(self):
        import os.path

        self.status.configure(text = "Working...")

        if hasattr(self, "save_button"):
            self.save_button.destroy()
            del self.save_button

        self.go_button.configure(state = 'disabled')

        self.output.delete("1.0", END)

        self.worker.go(self.process_output)

    def process_output(self, item):
        mode, data = item

        if mode == "Error":
            ErrorDialog(self.master, data)
            self.status.configure(text = "- Error encountered -")
            self.go_button.configure(state = 'normal')
        elif mode == "Status":
            self.status.configure(text = data)
        elif mode == "Output":
            self.output.insert(END, data)
            self.output.yview(END)
        elif mode == "Done":
            self.status.configure(text = "- Done -")

            self.save_button = Button(self.master,
                                      text = "Save log",
                                      command = self.save,
                                      background = buttoncolor,
                                      activebackground =
                                      activebuttoncolor)
            self.save_button.pack(side = 'left', fill = 'both', expand = 1)

            self.go_button.configure(state = 'normal')

        self.master.update()


class Worker(object):
    def __init__(self, method, *args, **kwargs):
        self.method  = method
        self.args    = args
        self.kwargs  = kwargs
        self.buffer  = []
    
    def go(self, emit):
        sys.stdout = self
        self.emit = emit
        try:
            res = self.method(*self.args, **self.kwargs)
        except:
            res = None
            self.emit(("Error", sys.exc_info()))
            self.write("   Error encountered! Giving up!\n")
        self.flush()

        self.emit(("Done", res))
        sys.stdout = sys.__stdout__

    def write(self, text):
        i = text.rfind("\n") + 1
        if i > 0:
            self.buffer.append(text[:i])
            self.flush()
            text = text[i:]
        self.buffer.append(text)

    def flush(self):
        self.emit(("Output", "".join(self.buffer)))
        self.buffer = []


def go(method, *args, **kwargs):
    root = Tk()
    root.title(window_title)
    main = Main(root, Worker(method, *args, **kwargs))
    root.protocol("WM_DELETE_WINDOW", main.end)
    root.mainloop()

def export():
    import poser

    import geometry_export
    reload(geometry_export)
    from geometry_export import exportScene

    exportScene()


if __name__ == "__main__":
    go(export)
